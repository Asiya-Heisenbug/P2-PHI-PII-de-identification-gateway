import json
import uuid
from pathlib import Path


STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "sessions"
STORE_DIR.mkdir(parents=True, exist_ok=True)


class MappingStore:

    def __init__(self, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.forward = {}
        self.reverse = {}
        self.counters = {}
        self._name_values = {}

    def get_token(self, original_value, label):

        if original_value in self.forward:
            return self.forward[original_value]

        n = self.counters.get(label, 0) + 1
        self.counters[label] = n

        token = f"{label}_{n:03d}"

        self.forward[original_value] = token
        self.reverse[token] = original_value

        return token

    def resolve(self, token):
        return self.reverse.get(token)

    def save(self):

        path = STORE_DIR / f"{self.session_id}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "forward": self.forward,
                    "reverse": self.reverse,
                    "counters": self.counters
                },
                f,
                indent=2
            )

        return path

    @classmethod
    def load(cls, session_id):

        path = STORE_DIR / f"{session_id}.json"

        obj = cls(session_id=session_id)

        if path.exists():

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            obj.forward = data["forward"]
            obj.reverse = data["reverse"]
            obj.counters = data["counters"]

        return obj