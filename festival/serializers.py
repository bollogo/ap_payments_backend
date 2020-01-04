from rest_framework import routers, serializers, viewsets
from .models import Festival

class FestivalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Festival
        fields = (
            'id',
            'name',
            'description',
            'picture',
            'start_time',
            'end_time'
        )


