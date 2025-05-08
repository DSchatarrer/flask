# src\core\utils.py

from datetime import date, time, datetime
from decimal import Decimal
import json


def to_json_compatible(data):
    def serializer(obj):
        if isinstance(obj, (date, time, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return str(obj)

    return json.loads(json.dumps(data, default=serializer))