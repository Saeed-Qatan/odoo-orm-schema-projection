from pydantic import BaseModel, ConfigDict, Field


class RawColumn(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False


class RawForeignKey(BaseModel):
    table: str
    column: str
    ref_table: str
    ref_column: str = "id"
    constraint_name: str | None = None


class RawTable(BaseModel):
    name: str
    columns: list[RawColumn] = Field(default_factory=list)
    primary_key: list[str] = Field(default_factory=list)


class RawDatabaseSchema(BaseModel):
    tables: dict[str, RawTable] = Field(default_factory=dict)
    foreign_keys: list[RawForeignKey] = Field(default_factory=list)


class FieldSchema(BaseModel):
    name: str
    type: str
    column: str | None = None
    relation: str | None = None
    inverse: str | None = None
    required: bool = False
    readonly: bool = False
    store: bool = True
    inferred: bool = False
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)


class ModelSchema(BaseModel):
    name: str
    table: str
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    fields: dict[str, FieldSchema] = Field(default_factory=dict)


class OrmSchema(BaseModel):
    models: dict[str, ModelSchema] = Field(default_factory=dict)


class RetrievalCandidate(BaseModel):
    id: str
    kind: str
    model: str
    field: str | None = None
    score: float
    source: str
    text: str = ""


class ProjectionOptions(BaseModel):
    max_models: int | None = None
    max_depth: int | None = None
    max_fields_per_model: int | None = None
    max_total_fields: int | None = None
    top_k_final: int | None = None
    debug: bool = False


class ProjectionRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    options: ProjectionOptions = Field(default_factory=ProjectionOptions)


class ProjectionMetrics(BaseModel):
    latency_ms: float
    total_fields_before: int
    total_fields_after: int
    reduction_ratio: float
    hallucinated_models: int = 0
    hallucinated_fields: int = 0
    retrieval_ms: float = 0
    graph_ms: float = 0
    projection_ms: float = 0


class ProjectionDebug(BaseModel):
    retrieval: list[RetrievalCandidate] = Field(default_factory=list)
    paths: list[list[str]] = Field(default_factory=list)
    removed_fields: list[str] = Field(default_factory=list)
    metrics: ProjectionMetrics


class ProjectionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str
    models: list[str]
    schema_: dict = Field(alias="schema")
    debug: ProjectionDebug | None = None
