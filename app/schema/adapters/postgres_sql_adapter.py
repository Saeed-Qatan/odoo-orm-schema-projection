import re
from pathlib import Path

from app.schema.models import RawColumn, RawDatabaseSchema, RawForeignKey, RawTable


CREATE_TABLE_RE = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>"?[\w.]+"?)\s*\((?P<body>.*?)\);',
    re.IGNORECASE | re.DOTALL,
)
FK_RE = re.compile(
    r'ALTER\s+TABLE\s+(?:ONLY\s+)?(?P<table>"?[\w.]+"?).*?'
    r'CONSTRAINT\s+(?P<constraint>"?[\w.]+"?)\s+FOREIGN\s+KEY\s*\((?P<column>"?[\w.]+"?)\)\s+'
    r'REFERENCES\s+(?P<ref_table>"?[\w.]+"?)\s*\((?P<ref_column>"?[\w.]+"?)\)',
    re.IGNORECASE | re.DOTALL,
)
INLINE_FK_RE = re.compile(
    r'FOREIGN\s+KEY\s*\((?P<column>"?[\w.]+"?)\)\s+REFERENCES\s+(?P<ref_table>"?[\w.]+"?)\s*\((?P<ref_column>"?[\w.]+"?)\)',
    re.IGNORECASE,
)
PK_RE = re.compile(r"PRIMARY\s+KEY\s*\((?P<columns>.*?)\)", re.IGNORECASE | re.DOTALL)


def _clean_identifier(value: str) -> str:
    return value.strip().strip('"').split(".")[-1]


def _split_sql_items(body: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
        else:
            current.append(char)
    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


class PostgresSqlSchemaAdapter:
    def load(self, path: Path) -> RawDatabaseSchema:
        sql = path.read_text(encoding="utf-8")
        schema = RawDatabaseSchema()

        for match in CREATE_TABLE_RE.finditer(sql):
            table_name = _clean_identifier(match.group("name"))
            table = RawTable(name=table_name)
            table_foreign_keys: list[RawForeignKey] = []

            for item in _split_sql_items(match.group("body")):
                upper_item = item.upper()
                if upper_item.startswith(("CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK")):
                    pk = PK_RE.search(item)
                    if pk:
                        table.primary_key = [_clean_identifier(col) for col in pk.group("columns").split(",")]
                    fk = INLINE_FK_RE.search(item)
                    if fk:
                        table_foreign_keys.append(
                            RawForeignKey(
                                table=table_name,
                                column=_clean_identifier(fk.group("column")),
                                ref_table=_clean_identifier(fk.group("ref_table")),
                                ref_column=_clean_identifier(fk.group("ref_column")),
                            )
                        )
                    continue

                parts = item.split()
                if len(parts) < 2:
                    continue
                column_name = _clean_identifier(parts[0])
                data_type = parts[1].lower()
                if data_type in {"character", "double", "timestamp"} and len(parts) >= 3:
                    data_type = f"{data_type} {parts[2].lower()}"
                table.columns.append(
                    RawColumn(
                        name=column_name,
                        data_type=data_type,
                        nullable="NOT NULL" not in upper_item,
                        primary_key="PRIMARY KEY" in upper_item,
                    )
                )
                if "PRIMARY KEY" in upper_item and column_name not in table.primary_key:
                    table.primary_key.append(column_name)

            schema.tables[table_name] = table
            schema.foreign_keys.extend(table_foreign_keys)

        for match in FK_RE.finditer(sql):
            schema.foreign_keys.append(
                RawForeignKey(
                    table=_clean_identifier(match.group("table")),
                    column=_clean_identifier(match.group("column")),
                    ref_table=_clean_identifier(match.group("ref_table")),
                    ref_column=_clean_identifier(match.group("ref_column")),
                    constraint_name=_clean_identifier(match.group("constraint")),
                )
            )

        return schema
