# خطة تطوير Backend Prototype: Odoo ORM Schema Projection

## الملخص

نبني Backend بلغة Python وFastAPI يأخذ `schema.sql` من Odoo PostgreSQL، يحوله إلى `ORM-like Schema` قريب من Odoo، يبني Graph للعلاقات، ثم يستقبل سؤال المستخدم ويرجع أصغر Schema هرمية لازمة للإجابة. النسخة الأولى لا تشغل Odoo، ولا تولد Domain، ولا تعتمد على LLM في اختيار الحقول؛ التركيز على Retrieval + Graph + Pruning بسرعة عالية ودقة قابلة للقياس.

معيار النجاح الأساسي للمشروع:

- زمن الإجابة: من `1.0` إلى `1.5` ثانية كحد أعلى للطلب العادي.
- الهلوسة: `0` Models و`0` Fields غير موجودة في الـSchema.
- الدقة: يرجع فقط القدر المطلوب من السؤال، بدون توسع زائد.
- صحة العلاقات: أي علاقة في المخرج يجب أن تأتي من علاقة موجودة أو مستنتجة بوضوح من FK.
- تقليل الحجم: تقليل الـSchema بنسبة واضحة مقارنة بالـSchema الكاملة.

## التقنية والخوارزميات

- Backend: `FastAPI`, `uvicorn`, `pydantic`, `pydantic-settings`.
- Schema parsing: `pglast` لقراءة PostgreSQL `schema.sql`.
- ORM-like mapping: تحويل `sale_order` إلى `sale.order`، وتحويل FK إلى `many2one`، واستنتاج `one2many` بعلامة `inferred=true`.
- Graph: `networkx` لتمثيل Models وFields والعلاقات وتشغيل `BFS`, `shortest_path`, `Dijkstra`، ولاحقًا `Personalized PageRank`.
- Sparse Retrieval: `rank-bm25`.
- Dense Retrieval: `sentence-transformers` مع `faiss-cpu`.
- Fuzzy Matching: `rapidfuzz`.
- Hybrid Retrieval: `Reciprocal Rank Fusion (RRF)`.
- Pruning: `Top-K`, `Score Thresholding`, `max_depth`, `max_models`, `max_fields_per_model`, `max_total_fields`.
- Performance: تحميل الـSchema والـGraph والفهارس مرة واحدة عند تشغيل التطبيق، ثم تنفيذ الطلبات من الذاكرة.

## هيكل المشروع

```text
app/
  main.py
  core/
    config.py
    rate_limit.py
    logging.py
  schema/
    models.py
    adapters/
      postgres_sql_adapter.py
    orm_mapper.py
    repository.py
  graph/
    builder.py
    traverser.py
    ranker.py
  retrieval/
    base.py
    bm25.py
    dense.py
    fuzzy.py
    hybrid.py
    rrf.py
  projection/
    budget.py
    linker.py
    pruner.py
    projector.py
    pipeline.py
  api/
    routes/
      health.py
      schema.py
      projection.py
  evaluation/
    golden_set.py
    metrics.py

data/
  raw/odoo/schema.sql
  processed/odoo_orm_schema.json
  processed/odoo_schema_graph.json
  indexes/bm25.pkl
  indexes/faiss.index
  indexes/faiss_metadata.json
```

## مراحل التطوير

### Phase 1 — Foundation

- [ ] تثبيت الحزم الأساسية: `fastapi`, `uvicorn`, `pydantic-settings`, `pglast`, `networkx`, `rank-bm25`, `rapidfuzz`, `sentence-transformers`, `faiss-cpu`, `pytest`.
- [ ] نقل الإعدادات إلى `app/core/config.py`.
- [ ] إضافة `.env.example`.
- [ ] إضافة `GET /health`.
- [ ] جعل SQLAlchemy اختياريًا ومؤجلًا، وليس جزءًا من Core Pipeline.

### Phase 2 — Schema Ingestion

- [ ] وضع Odoo schema الخام في `data/raw/odoo/schema.sql`.
- [ ] بناء `PostgresSqlSchemaAdapter` باستخدام `pglast`.
- [ ] استخراج الجداول، الأعمدة، أنواع البيانات، المفاتيح الأساسية، والعلاقات.
- [ ] بناء `RawDatabaseSchema` باستخدام Pydantic.

### Phase 3 — ORM-like Schema Mapping

- [ ] بناء `OrmMapper`.
- [ ] تحويل الجداول إلى أسماء Odoo-like:
  - `sale_order` → `sale.order`
  - `sale_order_line` → `sale.order.line`
  - `res_partner` → `res.partner`
- [ ] تحويل FK إلى `many2one`.
- [ ] استنتاج `one2many` العكسية مع `inferred=true`.
- [ ] حفظ الناتج في `data/processed/odoo_orm_schema.json`.
- [ ] منع تكرار الـHierarchy في التخزين؛ الـHierarchy تولد وقت الطلب فقط.

### Phase 4 — Schema Graph

- [ ] بناء `SchemaGraphBuilder` باستخدام `networkx`.
- [ ] تمثيل العقد:
  - `model:sale.order`
  - `field:sale.order.partner_id`
- [ ] تمثيل الحواف:
  - model يحتوي field.
  - field يرتبط model.
  - model يرتبط model عبر علاقة ORM.
- [ ] بناء `GraphTraverser` يدعم `shortest_path` و`BFS` بعمق محدود.
- [ ] حفظ graph snapshot في `data/processed/odoo_schema_graph.json`.

### Phase 5 — Retrieval Indexes

- [ ] بناء corpus لكل Model وField يحتوي الاسم، النوع، العلاقة، ووصف عربي/إنجليزي مختصر.
- [ ] بناء `BM25Retriever`.
- [ ] بناء `DenseRetriever` باستخدام `sentence-transformers` و`faiss-cpu`.
- [ ] بناء `FuzzyRetriever` باستخدام `rapidfuzz`.
- [ ] بناء `HybridRetriever` يدمج النتائج عبر `RRF`.
- [ ] حفظ الفهارس في `data/indexes/`.
- [ ] إضافة aliases أولية:
  - عميل/زبون/customer → `partner_id`, `res.partner`
  - مبيعات/sales → `sale.order`
  - منتج/product → `product_id`, `product.product`
  - كمية/quantity → `product_uom_qty`
  - تاريخ/date → `date_order`

### Phase 6 — Query Pipeline

- [ ] بناء `SchemaProjectionPipeline`.
- [ ] خطوات التنفيذ:
  - تطبيع السؤال العربي/الإنجليزي.
  - تحديد `Complexity Budget`.
  - تشغيل Hybrid Retrieval.
  - Schema Linking لاختيار Models وFields.
  - Graph Traversal لربط المرشحين بعلاقات صحيحة.
  - Schema Pruning لإزالة الزائد.
  - Projector لإخراج Hierarchical ORM Schema.
- [ ] الميزانيات الافتراضية:
  - `max_models=5`
  - `max_depth=3`
  - `max_fields_per_model=8`
  - `max_total_fields=30`
  - `top_k_bm25=30`
  - `top_k_dense=30`
  - `top_k_final=20`
- [ ] ممنوع إرجاع أي Model أو Field غير موجود في `odoo_orm_schema.json`.

### Phase 7 — API

- [ ] إضافة `POST /api/v1/project-schema`.
- [ ] Request:
```json
{
  "query": "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية",
  "options": {
    "max_models": 5,
    "max_depth": 3,
    "max_total_fields": 30
  }
}
```
- [ ] Response:
```json
{
  "query": "...",
  "models": ["sale.order", "res.partner", "sale.order.line", "product.product"],
  "schema": {},
  "debug": {
    "retrieval": [],
    "paths": [],
    "removed_fields": [],
    "metrics": {
      "latency_ms": 0,
      "total_fields_before": 0,
      "total_fields_after": 0,
      "reduction_ratio": 0,
      "hallucinated_models": 0,
      "hallucinated_fields": 0
    }
  }
}
```
- [ ] إضافة `GET /api/v1/schema/models`.
- [ ] إضافة `GET /api/v1/schema/models/{model_name}`.
- [ ] جعل `debug=false` افتراضيًا.

### Phase 8 — Quality, Speed & Hallucination Control

- [ ] تحميل الـSchema والـGraph وBM25 وFAISS في الذاكرة عند بدء التطبيق.
- [ ] عدم بناء embeddings أو indexes أثناء request.
- [ ] إضافة request timeout داخلي: `1500ms`.
- [ ] إضافة performance budget:
  - Retrieval أقل من `400ms`.
  - Graph traversal أقل من `300ms`.
  - Pruning + projection أقل من `300ms`.
  - API overhead أقل من `200ms`.
- [ ] إضافة strict validator قبل الإرجاع:
  - يتحقق أن كل model موجود.
  - يتحقق أن كل field موجود داخل model الصحيح.
  - يتحقق أن كل relation صحيحة.
  - يحذف أي عنصر غير موثق بدل تمريره.
- [ ] إضافة over-selection guard:
  - إذا لم يطلب السؤال حقولًا من model معين، لا نضيفه إلا إذا كان ضروريًا كمسار علاقة.
  - إذا أضيف model كـbridge فقط، نضيف أقل حقول ممكنة منه.
- [ ] إضافة confidence scores:
  - `retrieval_score`
  - `linking_score`
  - `graph_score`
  - `final_score`
- [ ] إذا كانت الثقة منخفضة، يرجع النظام Schema محافظة صغيرة بدل التوسع الكبير.

### Phase 9 — Backend Protection & Limits

- [ ] إضافة Rate Limiting:
  - `POST /api/v1/project-schema`: 30 طلب/دقيقة.
  - endpoints القراءة: 100 طلب/دقيقة.
- [ ] إضافة limits:
  - أقصى طول للسؤال.
  - أقصى `max_depth`.
  - أقصى `max_total_fields`.
  - أقصى زمن للطلب.
- [ ] إضافة logging للزمن، عدد النتائج، ونسبة التقليص.
- [ ] عدم تسجيل أسرار أو `.env`.
- [ ] منع أي SQL execution من سؤال المستخدم؛ النظام يتعامل مع metadata فقط.

### Phase 10 — Evaluation

- [ ] إنشاء Golden Set من 20 إلى 30 سؤالًا.
- [ ] لكل سؤال نحدد يدويًا:
  - expected models.
  - expected fields.
  - expected relationship paths.
  - maximum allowed extra fields.
- [ ] المقاييس:
  - Model Precision / Recall.
  - Field Precision / Recall.
  - Relationship Validity.
  - Reduction Ratio.
  - Latency P50 / P95.
  - Hallucination Count.
  - Over-selection Rate.
- [ ] شروط القبول:
  - `P95 latency <= 1500ms`.
  - `hallucination_count = 0`.
  - `relationship_validity = 100%`.
  - `reduction_ratio` واضح مقارنة بالـSchema الكاملة.
  - لا يرجع أكثر من المطلوب إلا عند الحاجة لعلاقة ضرورية.
- [ ] توليد تقرير `evaluation_report.json`.

### Phase 11 — Optional Advanced Features

- [ ] إضافة `Personalized PageRank` بعد نجاح النسخة الأساسية.
- [ ] إضافة synonyms عربية أوسع داخل `schema_aliases.json`.
- [ ] إضافة cache لنتائج الأسئلة المتكررة.
- [ ] إضافة واجهة بسيطة لعرض السؤال، الموديلات المختارة، مسارات العلاقات، والـSchema النهائي.

## خطة الاختبار

- اختبار parsing: يتأكد أن `schema.sql` ينتج جداول وأعمدة وFKs.
- اختبار ORM mapping: يتأكد أن `sale_order` يصبح `sale.order` وأن FK يصبح `many2one`.
- اختبار graph traversal: يتأكد من المسار `sale.order → sale.order.line → product.product`.
- اختبار retrieval: سؤال “اسم العميل والكمية” يجب أن يرجع `partner_id`, `product_uom_qty`.
- اختبار pruning: لا يتم إرجاع حقول غير مطلوبة.
- اختبار no hallucination: كل عنصر في response موجود في `odoo_orm_schema.json`.
- اختبار API: `POST /api/v1/project-schema` يرجع JSON صالح.
- اختبار latency: الطلبات العادية يجب أن تكون بين `1.0` و`1.5` ثانية أو أقل.
- اختبار rate limit: الطلبات فوق الحد ترجع `429`.

## الافتراضات والقرارات النهائية

- مصدر الـSchema في v1 هو Prisma Odoo `schema.sql`.
- الـSchema النهائية داخل المشروع ستكون `ORM-like JSON`، لا Python hardcoded ولا DB tables.
- قاعدة البيانات ليست ضرورية في Core Pipeline، وتؤجل للتقييم والـlogs إن احتجناها.
- لا نولد Odoo Domain في هذا البروتوتايب؛ نرجع فقط Schema كافية وآمنة.
- أول نسخة تعتمد على `BM25 + Dense + Fuzzy + RRF + NetworkX Traversal`.
- `PPR` مرحلة تحسين لاحقة، وليست شرطًا لأول demo.
- الأولوية في التقييم: السرعة خلال `1.5s`، منع الهلوسة، صحة العلاقات، تقليل حجم الـSchema، ثم تحسين الـranking.
