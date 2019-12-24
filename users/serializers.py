from rest_framework import routers, serializers, viewsets
from .models import Charge, Payout, Wallet, User, Wristband

class WristbandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wristband
        fields = (
            'id', 'token',
        )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'date_created',
        )


class WalletSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    wristbands = WristbandSerializer(read_only=True, many=True)
    class Meta:
        model = Wallet
        fields = (
            'id', 'pub_key', 'user', 'balance', 'date_created', 'user', 'wristbands'
        )
    

class ChargeSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)    
    class Meta:
        model = Charge
        fields = (
            'id', 'amount', 'payment_method', 'is_paid', 'date_created', 'wallet'
        )


class PayoutSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)
    class Meta:
        model = Payout
        fields = (
            'id', 'token', 'amount', 'date_created', 'wallet'
        )
