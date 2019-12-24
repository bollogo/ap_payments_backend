from django.db import models
import uuid
import sys
from .json import json

class BaseQuerySet(models.QuerySet):
    def to_dict(self):
        return self.model.get_serializer()(self, many=True).data

    def to_json(self):
        return json.dumps(self.to_dict())

    def dump_to_file(self, filename):
        with open(filename, 'w') as f:
            f.write(self.to_json())

class BaseModel(models.Model):
    class Meta:
        abstract = True
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    @classmethod
    def get_serializer(cls):
        serializers_path = cls.__module__.split('.')[0] + '.serializers'
        return getattr(sys.modules[serializers_path], cls.serializer_class)

    def to_dict(self):
        return self.__class__.get_serializer()(self).data

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
