import uuid
from django.db import models
from users.models import User, Charge, Payout


class FestivalModel(models.Model):
    class Meta:
        abstract = True
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


    
class FestivalQuerySet(models.QuerySet):
    def to_dict(self):
        return [dict(pk=festival.pk, name=festival.name) for festival in self]


class Festival(FestivalModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    picture = models.CharField(max_length=255, blank=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)

    owner = models.ForeignKey(User, models.DO_NOTHING, related_name='festivals')

    def __repr__(self):
        return self.name
    
    def __str__(self):
        return self.name

    objects = FestivalQuerySet.as_manager()

    def charges(self):
        return Charge.objects.filter(is_paid=True)
    
    def payouts(self):
        return Payout.objects.all()

    def users(self):
        return User.objects.filter(email__icontains='wristband')

