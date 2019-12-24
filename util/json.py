import json
from uuid import UUID

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


def dumps(my_object):
    return json.dumps(my_object, cls=UUIDEncoder)
