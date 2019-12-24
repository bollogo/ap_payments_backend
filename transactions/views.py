import traceback

import json

from aeternity import transactions, signing, node, identifiers, hashing

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.db.models import Count
from django.views.generic import TemplateView
from transactions import blockchain
from users.models import Wallet
from .models import Invoice, Transaction

def signed_tx_to_obj(tx_str):
    tx = hashing.decode_rlp(tx_str)

    if hashing._int_decode(tx[0]) != 11:
        raise Exception("invalid tag")

    if len(tx) != 4:
        raise Exception("invalid tx")

    return transactions._tx_native(op=transactions.UNPACK_TX, tx=hashing.encode("tx", tx[3]))


# MERCHANT
@csrf_exempt
def create_invoice(request):
    assert request.method == "POST"
    data = json.loads(request.body)

    destination = data["destination"]
    amount = max(0, data["amount"])
    label = data["label"]

    i = Invoice.objects.create(
        destination=destination,
        amount=amount,
        label=label,
        status="pending",
    )

    return JsonResponse({
        "id": str(i.id),
        "destination": i.destination,
        "amount": i.amount,
        "label": i.label,
        "status": i.status,
    })


# MERCHANT
def check_invoice(request, id):
    try:
        i = Invoice.objects.get(id=id)
    except (KeyError, ValueError, Invoice.DoesNotExist):
        raise Http404

    return JsonResponse({
        "id": str(i.id),
        "destination": i.destination,
        "amount": i.amount,
        "label": i.label,
        "status": i.status,
        "tx_hash": i.transaction_set.last().tx_hash if i.status == "successful" else None,
    })

def get_balance(request, pub):
    wallet = Wallet.for_pub_key(pub)
    balance = wallet.update_balance_from_blockchain()
    return JsonResponse({
        "balance": wallet.balance
    })

def get_nonce(request, pub):
    return JsonResponse({
        "nonce": blockchain.get_nonce(pub)
    })


# USER
@csrf_exempt
def broadcast_tx(request):
    assert request.method == "POST"
    data = json.loads(request.body)

    # get Invoice
    try:
        i = Invoice.objects.get(id=data["id"], status="pending")
    except (KeyError, ValueError, Invoice.DoesNotExist):
        raise Http404

    # get Transaction
    try:
        tx_obj = signed_tx_to_obj(data["signed_tx"])
    except Exception as e:
        traceback.print_exc()

        # invalid signed tx => Invoice failed permanently
        i.status = "failed"
        i.error_reason = str(e)
        i.save(update_fields=["status", "error_reason"])

        return JsonResponse({
            "id": str(i.id),
            "amount": i.amount,
            "label": i.label,
            "status": i.status,
            "error_reason": i.error_reason,
        })


    if tx_obj.data.recipient_id != i.destination:
        # invalid destination => Invoice failed permanently
        i.status = "failed"
        i.error_reason = "Invalid destination: want %s, got %s" % (i.destination, tx_obj.data.recipient_id)
        i.save(update_fields=["status", "error_reason"])

        return JsonResponse({
            "id": str(i.id),
            "amount": i.amount,
            "label": i.label,
            "status": i.status,
            "error_reason": i.error_reason,
        })

    if tx_obj.data.amount != i.amount:
        # invalid amount => Invoice failed permanently
        i.status = "failed"
        i.error_reason = "Invalid amount: want %d, got %d" % (i.amount, tx_obj.data.amount)
        i.save(update_fields=["status", "error_reason"])

        return JsonResponse({
            "id": str(i.id),
            "amount": i.amount,
            "label": i.label,
            "status": i.status,
            "error_reason": i.error_reason,
        })


    # TODO: check and update balance
    if False:
        i.status = "failed"
        i.error_reason = "insufficient balance"

        i.save(update_fields=["status", "error_reason"])

        return JsonResponse({
            "id": str(i.id),
            "amount": i.amount,
            "label": i.label,
            "status": i.status,
            "error_reason": i.error_reason,
        })

    estimated_new_balance = ae.api.get_account_by_pubkey(pubkey=tx_obj.data.sender_id).balance - i.amount

    # broadcast tx
    try:
        ret = ae.broadcast_transaction(data["signed_tx"])

        if not ret or not ret.startswith("th_"):
            raise Exception(ret)

        try:
            tx_on_chain = ae.get_transaction_by_hash(hash=ret)
            print("tx_on_chain=%r" % (tx_on_chain, ))
        except Exception as e:
            traceback.print_exc()

    except Exception as e:
        new_nonce = ae.get_next_nonce(tx_obj.data.sender_id)

        return JsonResponse({
            "id": str(i.id),
            "amount": i.amount,
            "label": i.label,
            "status": "retry",
            "error_reason": str(e),
            "new_nonce": new_nonce,
        })

    # broadcast successful
    tx = Transaction.objects.create(
        invoice=i,
        source=tx_obj.data.sender_id,
        destination=tx_obj.data.recipient_id,
        amount=tx_obj.data.amount,
        payload=tx_obj.data.payload,
        date_broadcast=timezone.now(),
        signed_tx=data["signed_tx"],
        tx_hash=ret
    )

    i.status = "successful"
    i.save(update_fields=["status"])

    return JsonResponse({
        "id": str(i.id),
        "amount": i.amount,
        "label": i.label,
        "status": i.status,
        "tx_hash": tx.tx_hash,
        "estimated_new_balance": estimated_new_balance,
    })


class StatsView(TemplateView):
    template_name = "stats.html"

    def get_context_data(self):
        context = super().get_context_data()

        context["merchant"] = self.merchant
        context["invoices"] = self.invoices
        context["counts"] = self.counts
        context["total_count"] = Invoice.objects.filter(status="successful").count()
        context["total"] = sum(Invoice.objects.filter(status="successful").values_list("amount", flat=True))

        return context


    def get(self, request, merchant_key):
        self.merchant = merchant_key

        self.invoices = Invoice.objects.filter(
            destination=merchant_key,
            status="successful",
        )

        self.counts = Invoice.objects.filter(status="successful") \
                                     .values("label") \
                                     .annotate(cnt=Count("label")) \
                                     .order_by()

        return super().get(request)
