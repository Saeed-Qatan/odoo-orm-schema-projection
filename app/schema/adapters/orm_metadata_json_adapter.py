import json
from pathlib import Path
from typing import Any

from app.schema.aliases import AliasCatalog, get_alias_catalog
from app.schema.models import FieldSchema, ModelSchema, OrmSchema


class OrmMetadataJsonAdapter:
    def __init__(self, aliases: AliasCatalog | None = None) -> None:
        self.aliases = aliases or get_alias_catalog()

    def load(self, path: Path) -> OrmSchema:
        payload = json.loads(path.read_text(encoding="utf-8"))
        modules = payload.get("modules")
        if not isinstance(modules, list):
            raise ValueError("Metadata JSON must contain a modules list.")

        schema = OrmSchema()
        for module in modules:
            model = self._model_from_module(module)
            schema.models[model.name] = model
        self._infer_reverse_relations(schema)
        return schema

    def _model_from_module(self, module: dict[str, Any]) -> ModelSchema:
        model_name = str(module.get("model") or module.get("name") or "").strip()
        if not model_name:
            raise ValueError("Every metadata module must define a model/name.")
        table = str(module.get("table") or model_name.replace(".", "_"))
        model = ModelSchema(
            name=model_name,
            table=table,
            description=module.get("description"),
            keywords=self._strings([model_name, table, *module.get("keywords", [])]),
            category=module.get("category"),
            common_domains=self._list_of_dicts(module.get("common_domains", [])),
            field_groups=module.get("field_groups", {}) if isinstance(module.get("field_groups"), dict) else {},
        )
        for group_name, group_payload in model.field_groups.items():
            fields = group_payload.get("fields", []) if isinstance(group_payload, dict) else []
            for field_payload in fields:
                field = self._field_from_payload(field_payload, str(group_name))
                model.fields[field.name] = field
        return model

    def _field_from_payload(self, payload: dict[str, Any], group_name: str) -> FieldSchema:
        field_name = str(payload.get("name") or "").strip()
        if not field_name:
            raise ValueError("Every metadata field must define a name.")
        field_type = str(payload.get("type") or "char")
        relation = payload.get("relation")
        keywords = [field_name, *payload.get("keywords", []), *self.aliases.field_aliases.get(field_name, [])]
        return FieldSchema(
            name=field_name,
            type=field_type,
            column=payload.get("column", field_name),
            relation=str(relation) if relation else None,
            inverse=payload.get("inverse"),
            required=bool(payload.get("required", False)),
            readonly=bool(payload.get("readonly", False)),
            store=bool(payload.get("store", True)),
            description=payload.get("description"),
            keywords=self._strings(keywords),
            choices=self._choices(payload.get("choices", [])),
            group=group_name,
        )

    def _infer_reverse_relations(self, schema: OrmSchema) -> None:
        for source_model in list(schema.models.values()):
            for field in list(source_model.fields.values()):
                if field.type not in {"many2one", "one2one"} or not field.relation:
                    continue
                target = schema.models.get(field.relation)
                if target is None:
                    continue
                inverse_name = f"{source_model.table}_ids"
                if inverse_name in target.fields:
                    continue
                target.fields[inverse_name] = FieldSchema(
                    name=inverse_name,
                    type="one2many",
                    relation=source_model.name,
                    inverse=field.name,
                    inferred=True,
                    description=f"Inferred one2many relation to {source_model.name} through {field.name}.",
                    keywords=[inverse_name, source_model.name, field.name],
                )

    def _strings(self, values: list[Any]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value is None:
                continue
            text = str(value)
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result

    def _choices(self, values: Any) -> list[list[str]]:
        if not isinstance(values, list):
            return []
        choices: list[list[str]] = []
        for item in values:
            if isinstance(item, list) and len(item) >= 2:
                choices.append([str(item[0]), str(item[1])])
            elif isinstance(item, dict) and "value" in item and "label" in item:
                choices.append([str(item["value"]), str(item["label"])])
        return choices

    def _list_of_dicts(self, values: Any) -> list[dict]:
        if not isinstance(values, list):
            return []
        return [item for item in values if isinstance(item, dict)]
