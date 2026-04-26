# DataDialysis Project Walkthrough

This document is a **guided tour** of the same areas you would cover in a short demo or technical walkthrough: before/after behavior, the ingestion entry point and flags, modularity, validation and rejections, and configuration. Use **synthetic data only** in any environment you show or record—no real IDs or sensitive names.

---

## 1. Before and after (field-level and messy → clean)

### Option A: Dashboard Change History

**Where to look:** Dashboard → **Change History**.

**Local URL:** `http://localhost:3000/change-history` (with API, frontend, and DB running).

**What you are showing:** The table exposes **Old Value**, **New Value**, and **Change Type** (INSERT/UPDATE), which is the clearest in-product story for “before vs after” at field granularity.

**How to prepare:**
- Run a pipeline first (e.g. `examples/end_to_end_flow.py` or ingest sample CSV/JSON) so rows exist.
- Stick to **synthetic** sample data (see `examples/end_to_end_flow.py` for fake PII patterns).

**Implementation pointers:**
- **Sole entry point:** `IngestionPipeline` in `src/main.py` (feature flags for redaction, NER, circuit breaker, raw vault, CDC, security report). Adapters and validators apply `RedactorService`; the pipeline wires NER and redaction logging.
- **API:** `src/dashboard/api/routes/change_history.py`
- **UI:** `dashboard-frontend/app/(dashboard)/change-history/page.tsx`

### Option B: Messy input vs cleaned output (script)

**Script:** `scripts/demo_before_after.py`

**What it illustrates:**
- **Left:** Messy synthetic input (duplicates, bad timestamps, missing IDs, inconsistent casing).
- **Right:** Same logical data after validation and redaction (stable IDs, normalized dates, redacted PII).

Run it in the terminal or open generated output/HTML; for a presentation you can place the two views side by side in a slide or doc.

---

## 1b. IngestionPipeline: single entry point and flags

**Class:** `IngestionPipeline` in `src/main.py`.

Behavior is controlled through constructor flags; defaults favor safety and audit without turning on the heaviest optional paths:

| Flag | Default | Purpose |
|------|--------|---------|
| `enable_circuit_breaker` | `True` | Abort batch when failure rate exceeds threshold |
| `enable_redaction_logging` | `True` | Log each PII redaction for audit |
| `enable_ner` | **`False`** | NER for names in unstructured text (e.g. notes); off by default (runtime cost) |
| `enable_raw_vault` | `True` | Store encrypted originals when storage supports it (PostgreSQL) |
| `enable_cdc` | `True` | CDC / smart updates when storage supports it |
| `enable_adaptive_chunking` | `False` | Adaptive CSV/JSON chunk sizes |
| `generate_security_report` | `True` | Security report after run when storage supports it |

PII redaction is always applied by adapters and Pydantic validators; the pipeline configures **NER** and **redaction logging**. Encryption applies when raw vault is on and the storage adapter supports it.

---

## 2. Modularity (dependency view)

The layout is **domain → adapters / infrastructure → dashboard**; a dependency graph makes that easy to explain.

**Optional tool:**
```bash
pip install pydeps
```

**From repo root:**
```powershell
pydeps src --max-bacon=2 -o docs/dependency_graph.svg
```

**Variants:**
- `pydeps src --max-bacon=2 --cluster` — cluster by top-level package.
- `pydeps src --max-bacon=1 -o docs/deps_simple.svg` — fewer edges.

**What to highlight:** Domain as the core; adapters and infrastructure on the outside—**hexagonal (ports & adapters)**.

**If the graph is too dense:**
```powershell
pydeps src.domain src.adapters src.infrastructure --max-bacon=1 -o docs/deps_core.svg
```

---

## 3. Validation: rejected records and why

Rejections are logged by the ingest pipeline (there is no dedicated rejections table yet). For a walkthrough you can **tail logs** or plan a future rejections UI.

### Log-based path (no code change)

1. Use **synthetic bad data** (invalid date, missing required field, duplicate key, etc.).
2. Run the pipeline against a file that fails validation.
3. Look for structured rejection context, including:
   - `rejection_type`: `validation_failure`
   - `error_type`: e.g. `ValidationError`, `PydanticValidationError`
   - `error_message`: human-readable reason
   - `raw_record_preview`: truncated record (safe if synthetic)

**Where it is implemented:**  
`src/adapters/ingesters/xml_ingester.py`, `json_ingester.py`, `csv_ingester.py` → `_log_security_rejection()`.

**Readable JSON logs:** set `JSON_LOGS=true` (see `docker-compose.yml` and API env), trigger a rejection, inspect one structured line.

### Circuit breaker (batch-level stop)

**Where to look:** Dashboard **Circuit Breaker** view if present, or `GET /api/circuit-breaker`.

**Story:** When failure rate crosses the threshold, the circuit opens and the batch aborts—fail-fast when quality collapses.

**API:** `src/dashboard/api/routes/circuit_breaker.py`

---

## 4. Configuration: filters, mapping, and env knobs

Filter and safety behavior is split across a few obvious files—good stops on a tour:

| Topic | File | What to point at |
|------|------|-------------------|
| **Environment** (circuit breaker, NER, XML, limits) | `src/infrastructure/settings.py` | `DD_CIRCUIT_BREAKER_*`, `DD_NER_*`, `DD_XML_*`, `DD_MAX_RECORD_SIZE` |
| **Source → canonical fields** | `src/domain/field_mapping.py` | `DEFAULT_FIELD_MAPPING` (synonyms → domain names) |
| **XML extraction shape** | `xml_config.json` (repo root) | `root_element`, `fields` (XPath → field name) |

**Suggested narrative order:**
1. **`xml_config.json`** — what gets pulled from XML without code edits.
2. **`src/domain/field_mapping.py`** — how external columns map into the domain model.
3. **`src/infrastructure/settings.py`** — how ops tunes safety and performance.

---

## 5. Hygiene when presenting or recording

- **Privacy:** Only synthetic data in terminals, dashboards, and slides (`examples/end_to_end_flow.py`, `scripts/demo_before_after.py`).
- **Clarity:** If you export visuals, a light window shadow and minimal callouts (validation line, circuit state, config block) help viewers follow the story.

---

## Walkthrough checklist

| Theme | What to do |
|-------|----------------|
| Before / after | Open **Change History** in the dashboard, **or** run `scripts/demo_before_after.py` and compare outputs. |
| Modularity | Generate `docs/dependency_graph.svg` with pydeps and walk the layers. |
| Validation | Ingest synthetic bad data → show a `SECURITY REJECTION` log line with `error_message`. |
| Circuit breaker | Show circuit breaker API or dashboard state after forced failures. |
| Configuration | Step through `xml_config.json`, `src/domain/field_mapping.py`, `src/infrastructure/settings.py`. |
