import re
from abc import ABC, abstractmethod

from app.schema.models import OrmSchema, RetrievalCandidate


TOKEN_RE = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)


def normalize_text(text: str) -> str:
    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
    }
    value = text.lower()
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def tokenize(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(normalize_text(text))
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        for prefix in ("وال", "ال", "و"):
            if token.startswith(prefix) and len(token) > len(prefix) + 1:
                expanded.append(token[len(prefix) :])
                break
    return expanded


def build_corpus(schema: OrmSchema) -> list[RetrievalCandidate]:
    candidates: list[RetrievalCandidate] = []
    for model in schema.models.values():
        model_text = " ".join([model.name, model.table, model.description or "", *model.keywords])
        candidates.append(
            RetrievalCandidate(
                id=f"model:{model.name}",
                kind="model",
                model=model.name,
                score=0,
                source="corpus",
                text=model_text,
            )
        )
        for field in model.fields.values():
            field_text = " ".join(
                [
                    model.name,
                    model.table,
                    field.name,
                    field.type,
                    field.relation or "",
                    field.description or "",
                    *field.keywords,
                ]
            )
            candidates.append(
                RetrievalCandidate(
                    id=f"field:{model.name}.{field.name}",
                    kind="field",
                    model=model.name,
                    field=field.name,
                    score=0,
                    source="corpus",
                    text=field_text,
                )
            )
    return candidates


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[RetrievalCandidate]:
        raise NotImplementedError

