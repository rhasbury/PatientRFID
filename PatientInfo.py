'''
Created on Jul 12, 2016

@author: rhasbury
'''
import datetime
import json

class PatientInfoClass:
    def __init__(self, name):
        self.name = name
        
    
    def to_JSON(self):
        date_handler = lambda obj: (
            obj.isoformat()
            if isinstance(obj, datetime.datetime)
            or isinstance(obj, datetime.date)
            else obj.__dict__            
        )
        return json.dumps(self, default=date_handler, sort_keys=True, indent=4)