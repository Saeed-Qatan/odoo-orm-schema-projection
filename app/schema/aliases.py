import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_ALIAS_PATH = Path("data/config/schema_aliases.json")


class AliasCatalog:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.model_aliases: dict[str, list[str]] = payload.get("models", {})
        self.field_aliases: dict[str, list[str]] = payload.get("fields", {})
        self.intent_terms: dict[str, list[str]] = payload.get("intents", {})
        self.entities: dict[str, dict] = payload.get("entities", {})
        self.months: dict[str, str] = payload.get("months", {})
        self.filters: dict[str, dict] = payload.get("filters", {})

    @classmethod
    def load(cls, path: Path = DEFAULT_ALIAS_PATH) -> "AliasCatalog":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(payload)


@lru_cache
def get_alias_catalog(path: str = str(DEFAULT_ALIAS_PATH)) -> AliasCatalog:
    return AliasCatalog.load(Path(path))
