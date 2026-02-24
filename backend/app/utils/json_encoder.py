import json
from datetime import datetime, date
from uuid import UUID

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif hasattr(obj, 'value'):  # Handle Enum objects
            return obj.value
        elif hasattr(obj, '__dict__'):  # Handle objects with __dict__
            return obj.__dict__
        return super().default(obj)