import copy
import hashlib
import json
import time


class ResponseCache:
    def __init__(self, ttl=300, capacity=256):
        self.ttl, self.capacity, self.entries = ttl, capacity, {}

    def key(self, provider, model, messages, prompt_version, dev_mode):
        return hashlib.sha256(json.dumps([provider, model, messages, prompt_version, dev_mode],
                                         sort_keys=True).encode()).hexdigest()

    def get(self, key):
        entry = self.entries.get(key)
        if entry and entry[0] > time.monotonic():
            result = copy.deepcopy(entry[1])
            result.metadata.update({"cache_hit": True, "original_cost": result.cost,
                                    "original_response_id": result.response_id})
            result.cost, result.latency = 0.0, 0.0
            return result
        self.entries.pop(key, None)

    def put(self, key, result):
        if len(self.entries) >= self.capacity:
            self.entries.pop(next(iter(self.entries)))
        self.entries[key] = (time.monotonic() + self.ttl, copy.deepcopy(result))
