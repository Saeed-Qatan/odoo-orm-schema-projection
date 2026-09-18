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
    choices: list[list[str]] = Field(default_factory=list)
    group: str | None = None


class ModelSchema(BaseModel):
    name: str
    table: str
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    category: str | None = None
    common_domains: list[dict] = Field(default_factory=list)
    field_groups: dict = Field(default_factory=dict)
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


class MatchedTerm(BaseModel):
    input: str
    matched: str
    target: str
    score: float
    match_type: str = "exact"


class Ambiguity(BaseModel):
    term: str
    candidates: list[str] = Field(default_factory=list)
    reason: str


class QueryUnderstanding(BaseModel):
    intent: str | None = None
    entities: list[str] = Field(default_factory=list)
    filters: dict[str, str] = Field(default_factory=dict)
    required_models: list[str] = Field(default_factory=list)
    required_fields: dict[str, list[str]] = Field(default_factory=dict)
    anchor_model: str | None = None
    field_paths: list[list[str]] = Field(default_factory=list)
    matched_terms: list[MatchedTerm] = Field(default_factory=list)
    ambiguities: list[Ambiguity] = Field(default_factory=list)


class ConfidenceScores(BaseModel):
    retrieval_score: float = 0
    linking_score: float = 0
    graph_score: float = 0
    final_score: float = 0


class RelationshipPath(BaseModel):
    models: list[str]
    relation_fields: dict[str, str] = Field(default_factory=dict)


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
    query_understanding: QueryUnderstanding | None = None
    retrieval: list[RetrievalCandidate] = Field(default_factory=list)
    paths: list[list[str]] = Field(default_factory=list)
    relationship_paths: list[RelationshipPath] = Field(default_factory=list)
    removed_fields: list[str] = Field(default_factory=list)
    confidence: ConfidenceScores | None = None
    metrics: ProjectionMetrics


class ProjectionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str
    supported: bool = True
    unsupported_reason: str | None = None
    models: list[str]
    schema_: dict = Field(alias="schema")
    debug: ProjectionDebug | None = None
