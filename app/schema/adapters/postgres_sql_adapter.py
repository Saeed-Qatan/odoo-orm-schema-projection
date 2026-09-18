import re
from pathlib import Path
from typing import Any

from app.schema.models import RawColumn, RawDatabaseSchema, RawForeignKey, RawTable


CREATE_TABLE_RE = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>"?[\w.]+"?)\s*\((?P<body>.*?)\)\s*(?:INHERITS\s*\((?P<parents>[^)]*)\))?\s*;',
    re.IGNORECASE | re.DOTALL,
)
FK_RE = re.compile(
    r'ALTER\s+TABLE\s+(?:ONLY\s+)?(?P<table>"?[\w.]+"?)[^;]*?'
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


def _enum_name(value: Any) -> str:
    return getattr(value, "name", str(value))


def _string_value(value: Any) -> str:
    return getattr(value, "sval", str(value))


class PostgresSqlSchemaAdapter:
    def load(self, path: Path) -> RawDatabaseSchema:
        sql = path.read_text(encoding="utf-8")
        try:
            return self._load_with_pglast(sql)
        except Exception:
            return self._load_with_regex(sql)

    def _load_with_pglast(self, sql: str) -> RawDatabaseSchema:
        from pglast import parse_sql

        schema = RawDatabaseSchema()
        statements = parse_sql(sql)
        inheritance: dict[str, list[str]] = {}
        for raw in statements:
            stmt = raw.stmt
            stmt_type = type(stmt).__name__
            if stmt_type == "CreateStmt":
                self._extract_create_table(stmt, schema)
                inheritance[_clean_identifier(stmt.relation.relname)] = [
                    _clean_identifier(parent.relname) for parent in stmt.inhRelations or []
                ]
            elif stmt_type == "AlterTableStmt":
                self._extract_foreign_keys(stmt, schema)
        self._resolve_inheritance(schema, inheritance)
        return schema

    def _resolve_inheritance(
        self, schema: RawDatabaseSchema, inheritance: dict[str, list[str]]
    ) -> None:
        resolved: set[str] = set()

        def inherit(table_name: str, visiting: set[str]) -> None:
            if table_name in resolved:
                return
            if table_name in visiting:
                raise ValueError(f"Cyclic table inheritance: {table_name}")
            table = schema.tables[table_name]
            for parent_name in inheritance.get(table_name, []):
                if parent_name not in schema.tables:
                    raise ValueError(f"Missing inheritance parent: {parent_name}")
                inherit(parent_name, visiting | {table_name})
                existing = {column.name: column for column in table.columns}
                for column in schema.tables[parent_name].columns:
                    if column.name not in existing:
                        inherited = column.model_copy(deep=True)
                        inherited.primary_key = False
                        table.columns.append(inherited)
                    elif not column.nullable:
                        existing[column.name].nullable = False
            for column in table.columns:
                if column.name in table.primary_key:
                    column.primary_key = True
                    column.nullable = False
            resolved.add(table_name)

        for table_name in schema.tables:
            inherit(table_name, set())

    def _extract_create_table(self, stmt: Any, schema: RawDatabaseSchema) -> None:
        table_name = _clean_identifier(stmt.relation.relname)
        table = RawTable(name=table_name)
        pending_primary_keys: set[str] = set()

        for item in stmt.tableElts or []:
            item_type = type(item).__name__
            if item_type == "ColumnDef":
                column = self._column_from_pglast(item)
                table.columns.append(column)
                for constraint in item.constraints or []:
                    contype = _enum_name(constraint.contype)
                    if contype == "CONSTR_PRIMARY":
                        pending_primary_keys.add(column.name)
                    elif contype == "CONSTR_NOTNULL":
                        column.nullable = False
                    elif contype == "CONSTR_FOREIGN" and constraint.pktable:
                        schema.foreign_keys.append(
                            RawForeignKey(
                                table=table_name,
                                column=column.name,
                                ref_table=_clean_identifier(constraint.pktable.relname),
                                ref_column=_clean_identifier(_string_value((constraint.pk_attrs or ["id"])[0])),
                                constraint_name=getattr(constraint, "conname", None),
                            )
                        )
            elif item_type == "Constraint":
                contype = _enum_name(item.contype)
                if contype == "CONSTR_PRIMARY":
                    for attr in item.keys or []:
                        pending_primary_keys.add(_clean_identifier(_string_value(attr)))
                elif contype == "CONSTR_FOREIGN" and item.pktable:
                    fk_attrs = list(item.fk_attrs or [])
                    pk_attrs = list(item.pk_attrs or [])
                    if fk_attrs:
                        schema.foreign_keys.append(
                            RawForeignKey(
                                table=table_name,
                                column=_clean_identifier(_string_value(fk_attrs[0])),
                                ref_table=_clean_identifier(item.pktable.relname),
                                ref_column=_clean_identifier(_string_value(pk_attrs[0])) if pk_attrs else "id",
                                constraint_name=getattr(item, "conname", None),
                            )
                        )

        table.primary_key = list(pending_primary_keys)
        for column in table.columns:
            if column.name in pending_primary_keys:
                column.primary_key = True
                column.nullable = False
        schema.tables[table_name] = table

    def _extract_foreign_keys(self, stmt: Any, schema: RawDatabaseSchema) -> None:
        table_name = _clean_identifier(stmt.relation.relname)
        for command in stmt.cmds or []:
            constraint = getattr(command, "def_", None)
            if type(constraint).__name__ != "Constraint":
                continue
            if _enum_name(constraint.contype) == "CONSTR_PRIMARY":
                table = schema.tables[table_name]
                table.primary_key = [
                    _clean_identifier(_string_value(attr)) for attr in constraint.keys or []
                ]
                continue
            if _enum_name(constraint.contype) != "CONSTR_FOREIGN" or not constraint.pktable:
                continue
            fk_attrs = list(constraint.fk_attrs or [])
            pk_attrs = list(constraint.pk_attrs or [])
            if not fk_attrs:
                continue
            schema.foreign_keys.append(
                RawForeignKey(
                    table=table_name,
                    column=_clean_identifier(_string_value(fk_attrs[0])),
                    ref_table=_clean_identifier(constraint.pktable.relname),
                    ref_column=_clean_identifier(_string_value(pk_attrs[0])) if pk_attrs else "id",
                    constraint_name=getattr(constraint, "conname", None),
                )
            )

    def _column_from_pglast(self, column_def: Any) -> RawColumn:
        column_name = _clean_identifier(column_def.colname)
        data_type = self._type_name(column_def.typeName)
        nullable = True
        primary_key = False
        for constraint in column_def.constraints or []:
            contype = _enum_name(constraint.contype)
            if contype == "CONSTR_NOTNULL":
                nullable = False
            elif contype == "CONSTR_PRIMARY":
                primary_key = True
                nullable = False
        return RawColumn(name=column_name, data_type=data_type, nullable=nullable, primary_key=primary_key)

    def _type_name(self, type_name: Any) -> str:
        names = [_string_value(name) for name in type_name.names or []]
        names = [name for name in names if name != "pg_catalog"]
        if not names:
            return "unknown"
        value = " ".join(names).lower()
        aliases = {"int4": "integer", "int8": "bigint", "varchar": "character varying", "float8": "double precision"}
        return aliases.get(value, value)

    def _load_with_regex(self, sql: str) -> RawDatabaseSchema:
        schema = RawDatabaseSchema()
        inheritance: dict[str, list[str]] = {}

        for match in CREATE_TABLE_RE.finditer(sql):
            table_name = _clean_identifier(match.group("name"))
            table = RawTable(name=table_name)
            inheritance[table_name] = [
                _clean_identifier(parent) for parent in (match.group("parents") or "").split(",")
                if parent.strip()
            ]
            table_foreign_keys: list[RawForeignKey] = []

            for item in _split_sql_items(match.group("body")):
                upper_item = item.upper()
                if re.match(r"^(?:CONSTRAINT\b|PRIMARY\s+KEY\b|FOREIGN\s+KEY\b|UNIQUE\b|CHECK\b)", upper_item):
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
                reference = re.search(
                    r'\bREFERENCES\s+(?P<table>"?[\w.]+"?)\s*\((?P<column>"?[\w.]+"?)\)',
                    item,
                    re.IGNORECASE,
                )
                if reference:
                    table_foreign_keys.append(
                        RawForeignKey(
                            table=table_name,
                            column=column_name,
                            ref_table=_clean_identifier(reference.group("table")),
                            ref_column=_clean_identifier(reference.group("column")),
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

        alter_primary_keys = re.compile(
            r'ALTER\s+TABLE\s+(?:ONLY\s+)?(?P<table>"?[\w.]+"?)[^;]*?'
            r'PRIMARY\s+KEY\s*\((?P<columns>[^)]*)\)',
            re.IGNORECASE | re.DOTALL,
        )
        for match in alter_primary_keys.finditer(sql):
            table_name = _clean_identifier(match.group("table"))
            if table_name not in schema.tables:
                raise ValueError(f"Missing primary-key table: {table_name}")
            schema.tables[table_name].primary_key = [
                _clean_identifier(column) for column in match.group("columns").split(",")
            ]
        self._resolve_inheritance(schema, inheritance)
        return schema
