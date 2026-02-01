import json
import os

class SimpleDB:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = {}
    
    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def set(self, key, value):
        self.data[key] = value
        self.save()
    
    def get(self, key):
        return self.data.get(key)
    
    def delete(self, key):
        if key in self.data:
            del self.data[key]
            self.save()
    
    def keys(self):
        return [[k] for k in self.data.keys()]

ytdb = SimpleDB('ytcache.json')
sounddb = SimpleDB('soundcache.json')