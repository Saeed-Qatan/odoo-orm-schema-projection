from app.schema.models import FieldSchema, OrmSchema


class SchemaProjector:
    def project(
        self,
        schema: OrmSchema,
        selected_fields: dict[str, set[str]],
        preferred_roots: list[str] | None = None,
        field_paths: list[list[str]] | None = None,
    ) -> dict:
        if field_paths is not None:
            return self._project_field_paths(schema, selected_fields, field_paths, preferred_roots or [])
        roots = self._find_roots(schema, selected_fields, preferred_roots or [])
        if not roots and selected_fields:
            roots = [next(iter(selected_fields))]
        projected = {}
        visited: set[str] = set()
        for root in roots:
            projected[root] = {"fields": self._project_model(schema, root, selected_fields, visited)}
        return projected

    def _project_field_paths(
        self,
        schema: OrmSchema,
        selected_fields: dict[str, set[str]],
        field_paths: list[list[str]],
        preferred_roots: list[str],
    ) -> dict:
        projected: dict = {}
        for path in field_paths:
            current = path[0]
            resolved = []
            for index, name in enumerate(path[1:]):
                if name not in selected_fields.get(current, set()):
                    break
                field = schema.models[current].fields[name]
                resolved.append((name, field))
                if index < len(path) - 2:
                    current = field.relation
            else:
                # Keep fields scoped to their relationship occurrence, not just their model.
                target = projected.setdefault(path[0], {"fields": {}})["fields"]
                for index, (name, field) in enumerate(resolved):
                    payload = target.setdefault(name, self._field_payload(field))
                    if index < len(resolved) - 1:
                        target = payload.setdefault("fields", {})
        if not projected:
            for root in preferred_roots:
                if root in selected_fields:
                    projected[root] = {"fields": {}}
                    break
        return projected
    def _find_roots(
        self,
        schema: OrmSchema,
        selected_fields: dict[str, set[str]],
        preferred_roots: list[str],
    ) -> list[str]:
        for root in preferred_roots:
            if root in selected_fields:
                return [root]

        referenced = set()
        for model_name, fields in selected_fields.items():
            model = schema.models.get(model_name)
            if not model:
                continue
            for field_name in fields:
                field = model.fields.get(field_name)
                if field and field.relation in selected_fields and field.type in {"many2one", "one2many"}:
                    referenced.add(field.relation)
        roots = [model for model in selected_fields if model not in referenced]
        return roots[:1] if roots else []

    def _project_model(
        self,
        schema: OrmSchema,
        model_name: str,
        selected_fields: dict[str, set[str]],
        visited: set[str],
    ) -> dict:
        model = schema.models.get(model_name)
        if not model:
            return {}
        if model_name in visited:
            return {}
        visited.add(model_name)

        payload = {}
        for field_name in selected_fields.get(model_name, set()):
            field = model.fields.get(field_name)
            if not field:
                continue
            payload[field_name] = self._field_payload(field)
            if field.relation and field.relation in selected_fields:
                child = self._project_model(schema, field.relation, selected_fields, visited.copy())
                if child:
                    payload[field_name]["fields"] = child
        return payload

    def _field_payload(self, field: FieldSchema) -> dict:
        payload = {
            "type": field.type,
            "required": field.required,
            "readonly": field.readonly,
            "store": field.store,
        }
        if field.relation:
            payload["relation"] = field.relation
        if field.inverse:
            payload["inverse"] = field.inverse
        if field.inferred:
            payload["inferred"] = True
        return payload

