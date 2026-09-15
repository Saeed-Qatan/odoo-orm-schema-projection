from app.schema.models import FieldSchema, ModelSchema, OrmSchema, RawDatabaseSchema


ODOO_ALIASES: dict[str, list[str]] = {
    "sale.order": ["sales", "sale", "مبيعات", "طلب بيع", "أمر بيع"],
    "sale.order.line": ["sales line", "order line", "سطر البيع", "بنود البيع"],
    "res.partner": ["customer", "client", "partner", "عميل", "زبون", "جهة اتصال"],
    "product.product": ["product", "item", "منتج", "صنف"],
    "account.move": ["invoice", "bill", "فاتورة", "قيد محاسبي"],
}

FIELD_ALIASES: dict[str, list[str]] = {
    "partner_id": ["customer", "client", "partner", "عميل", "زبون"],
    "product_id": ["product", "item", "منتج", "صنف"],
    "product_uom_qty": ["quantity", "qty", "كمية", "الكمية"],
    "date_order": [
        "date",
        "order date",
        "تاريخ",
        "تاريخ الطلب",
        "يناير",
        "فبراير",
        "مارس",
        "أبريل",
        "ابريل",
        "مايو",
        "يونيو",
        "يوليو",
        "أغسطس",
        "اغسطس",
        "سبتمبر",
        "أكتوبر",
        "اكتوبر",
        "نوفمبر",
        "ديسمبر",
    ],
    "amount_total": ["total", "amount", "إجمالي", "مبلغ"],
    "name": ["name", "اسم", "الاسم"],
    "user_id": ["salesperson", "user", "مندوب", "البائع", "أحمد", "احمد"],
}


def table_to_model_name(table: str) -> str:
    parts = table.split("_")
    if len(parts) <= 1:
        return table
    return ".".join(parts)


def scalar_type(pg_type: str) -> str:
    value = pg_type.lower()
    if "timestamp" in value:
        return "datetime"
    if value == "date":
        return "date"
    if value in {"varchar", "character varying", "char"} or "character" in value:
        return "char"
    if value in {"text", "json", "jsonb"}:
        return value
    if value in {"bool", "boolean"}:
        return "boolean"
    if value in {"int", "int4", "integer", "bigint", "smallint", "serial"}:
        return "integer"
    if value in {"numeric", "decimal", "float", "double precision", "real"}:
        return "float"
    return value


class OrmMapper:
    def map(self, raw_schema: RawDatabaseSchema) -> OrmSchema:
        table_to_model = {table: table_to_model_name(table) for table in raw_schema.tables}
        fk_by_table_column = {(fk.table, fk.column): fk for fk in raw_schema.foreign_keys}
        orm = OrmSchema()

        for table_name, raw_table in raw_schema.tables.items():
            model_name = table_to_model[table_name]
            model = ModelSchema(
                name=model_name,
                table=table_name,
                description=f"Odoo-like model mapped from PostgreSQL table {table_name}.",
                keywords=[model_name, table_name, *ODOO_ALIASES.get(model_name, [])],
            )
            for column in raw_table.columns:
                fk = fk_by_table_column.get((table_name, column.name))
                if fk and fk.ref_table in table_to_model:
                    field = FieldSchema(
                        name=column.name,
                        type="many2one",
                        column=column.name,
                        relation=table_to_model[fk.ref_table],
                        required=not column.nullable,
                        description=f"Many2one relation to {table_to_model[fk.ref_table]}.",
                        keywords=[column.name, *FIELD_ALIASES.get(column.name, [])],
                    )
                else:
                    field = FieldSchema(
                        name=column.name,
                        type=scalar_type(column.data_type),
                        column=column.name,
                        required=not column.nullable,
                        description=f"Field {column.name} from column {column.name}.",
                        keywords=[column.name, *FIELD_ALIASES.get(column.name, [])],
                    )
                model.fields[field.name] = field
            orm.models[model_name] = model

        for fk in raw_schema.foreign_keys:
            if fk.table not in table_to_model or fk.ref_table not in table_to_model:
                continue
            source_model = table_to_model[fk.table]
            target_model = table_to_model[fk.ref_table]
            inverse_name = f"{fk.table}_ids"
            target = orm.models[target_model]
            if inverse_name not in target.fields:
                target.fields[inverse_name] = FieldSchema(
                    name=inverse_name,
                    type="one2many",
                    relation=source_model,
                    inverse=fk.column,
                    inferred=True,
                    description=f"Inferred one2many relation to {source_model} through {fk.column}.",
                    keywords=[inverse_name, source_model, fk.column],
                )

        return orm

