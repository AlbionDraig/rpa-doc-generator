# API Documentation - RPA Doc Generator

> Comprehensive guide to all public functions, classes, and modules in the RPA Doc Generator codebase.

## Table of Contents

- [API by Layer](#api-by-layer)
  - [API Routes Layer](#api-routes-layer)
  - [Application/Use Cases Layer](#applicationuse-cases-layer)
  - [Parser Layer](#parser-layer)
  - [Analysis Layer](#analysis-layer)
  - [Generator Layer](#generator-layer)
  - [Ingestion Layer](#ingestion-layer)
- [Core Utilities](#core-utilities)
- [Configuration & Settings](#configuration--settings)

---

## API by Layer

### API Routes Layer

**Location:** `app/api/routes/`

#### `POST /generate/`
**File:** `app/api/routes/generate.py`

Upload a bot package (ZIP file) and generate SDD documentation (Markdown, DOCX, PDF).

**Request:**
- `file`: ZIP file containing the bot project

**Response (200):**
```json
{
  "project_name": "ProjectName",
  "sdd_markdown": "path/to/SDD_ProjectName.md",
  "sdd_word": "path/to/SDD_ProjectName.docx", 
  "sdd_pdf": "path/to/SDD_ProjectName.pdf",
  "flow_svg": "path/to/flujo_taskbots.svg",
  "timestamp": "20260417_120000_000000"
}
```

**Error (400/503):**
```json
{
  "error": "Description",
  "code": "ERROR_CODE"
}
```

#### `POST /quality/`
**File:** `app/api/routes/quality.py`

Upload a bot package and generate quality/code review report.

**Request:**
- `file`: ZIP file

**Response (200):**
```json
{
  "project_name": "ProjectName",
  "quality_markdown": "path/to/Calidad_ProjectName.md",
  "quality_word": "path/to/Calidad_ProjectName.docx",
  "quality_pdf": "path/to/Calidad_ProjectName.pdf",
  "timestamp": "20260417_120000_000000"
}
```

#### `GET /download/:artifact_type/:timestamp/`
**File:** `app/api/routes/download.py`

Download a previously generated artifact (markdown, docx, pdf, svg).

**Parameters:**
- `artifact_type`: `sdd_markdown`, `sdd_word`, `sdd_pdf`, `quality_markdown`, `quality_word`, `quality_pdf`, `flow_svg`
- `timestamp`: folder timestamp from generation response

**Response:** Binary file with appropriate `Content-Type` header

#### `GET /system/health`
**File:** `app/api/routes/system.py`

Check API health and concurrency/rate limit status.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "limits": {
    "concurrency": {
      "max": 5,
      "current": 2,
      "queue": 0
    },
    "rate_limit": {
      "per_ip_per_minute": 30,
      "per_path_per_minute": 100
    }
  }
}
```

---

### Application/Use Cases Layer

**Location:** `app/application/use_cases/`

#### `generate_sdd(zip_path: str, settings: AppSettings = None) -> dict`
**File:** `app/application/use_cases/generate_sdd.py`

**Purpose:** Orchestrates the end-to-end SDD generation pipeline.

**Process:**
1. Extract ZIP file using `app/ingestion/extractor.py:extract_project()`
2. Parse project using `app/parser/project_parser.py:parse_project()`
3. Build flow graph using `app/analysis/flow_builder.py:build_flow()`
4. Generate tree using `app/analysis/tree_builder.py:build_tree()`
5. Build flow SVG using `app/generator/diagram_generator.py:generate_flow_svg()`
6. Generate Markdown using `app/generator/sdd_generator.py:generate_sdd()`
7. Export to DOCX/PDF using word/pdf generators
8. Return artifacts mapping

**Returns:**
```python
{
    "project_name": str,
    "sdd_markdown": str,      # path
    "sdd_word": str,          # path
    "sdd_pdf": str,           # path
    "flow_svg": str,          # path
    "timestamp": str          # folder timestamp
}
```

#### `generate_quality(zip_path: str, settings: AppSettings = None) -> dict`
**File:** `app/application/use_cases/generate_quality.py`

**Purpose:** Generates quality/code review report with prioritization and remediations.

**Process:**
1. Parse project (reuses SDD parser)
2. Build task descriptions via AI or heuristic
3. Build prioritization findings
4. Generate Markdown report
5. Export to DOCX/PDF

**Returns:**
```python
{
    "project_name": str,
    "quality_markdown": str,  # path
    "quality_word": str,      # path
    "quality_pdf": str,       # path
    "timestamp": str          # folder timestamp
}
```

#### `download_artifact(artifact_type: str, timestamp: str) -> str`
**File:** `app/application/use_cases/download_artifact.py`

**Purpose:** Locates and returns file path for a generated artifact.

**Parameters:**
- `artifact_type`: one of `sdd_markdown`, `sdd_word`, `sdd_pdf`, `quality_markdown`, `quality_word`, `quality_pdf`, `flow_svg`
- `timestamp`: folder creation timestamp (e.g., `20260417_120000_000000`)

**Returns:** Absolute path to artifact file

**Raises:** `FileNotFoundError` if artifact not found in timestamp folder

---

### Parser Layer

**Location:** `app/parser/`

#### **Main Facade:** `parse_project(path: str) -> dict`
**File:** `app/parser/project_parser.py`

**Purpose:** Main entry point to parse an RPA project directory.

**Algorithm:**
1. Load manifest if exists
2. Discover taskbot entries (JSON files)
3. Parse each taskbot:
   - Extract XML: nodes, variables, packages
   - Analyze flow: conditions, loops, error handlers, task calls
   - Extract metadata: developer, date, description
4. Build dependency graph between taskbots
5. Collect systems, credentials, packages project-wide
6. Sanitize all sensitive data

**Returns:**
```python
{
    "name": str,              # Project name from manifest or folder
    "task_count": int,
    "metadata": {
        "entrypoints": list,
        "description": str,
    },
    "tasks": [
        {
            "name": str,
            "path": str,
            "type": str,              # "taskbot" or "auxiliary"
            "is_entrypoint": bool,
            "role": str,              # "main", "lookup", "utility"
            "description": str,
            "developer": str,
            "declared_date": str,
            "size": int,              # bytes
            "node_stats": {
                "total_nodes": int,
                "decision_nodes": int,
                "loop_nodes": int,
                "task_calls": int,
                "error_handlers": int,
            },
            "variables": {
                "input": list,
                "output": list,
                "internal": list,
            },
            "task_calls": [           # runTask invocations
                {
                    "target_name": str,
                    "inputs": list,
                    "outputs": list,
                }
            ],
            "credentials": list,      # CredentialVault references
            "systems": list,          # URLs, databases, etc.
            "packages": list,         # AA360 packages used
            "error_handling": {
                "has_try": bool,
                "has_catch": bool,
                "has_finally": bool,
            },
            "actions": list,          # Step summaries
            "comments": list,         # Functional comments
            "dependencies": list,     # Manifest dependencies
        }
    ],
    "systems": list,          # Project-wide systems
    "credentials": list,      # Project-wide credentials
    "packages": list,         # Project-wide AA360 packages
    "files": {
        "manifest_count": int,
        "xml_count": int,
        "json_count": int,
    },
    "tree": str,              # ASCII tree representation
}
```

#### **Sub-modules:**

**`_common.py`** - Shared utilities
- `sanitize_text(value, field_name=None) -> str` — Masks sensitive data (passwords, user paths, credentials)
- `_extract_comment_text(node) -> str` — Extracts sanitized text from Comment nodes
- `_extract_value_literal(value) -> str` — Extracts value from AA360 nested structures
- `_load_json(file_path) -> dict` — Safe JSON loading
- `_looks_like_taskbot(file_path) -> bool` — Heuristic detection

**`_documents.py`** - XML/JSON file parsing
- `parse_xml_file(file_path, relative_path, ...) -> dict` — Parses AA360 XML (taskbot file format)
- `extract_variables_from_xml(root, logger) -> dict` — Extracts input/output variables
- `extract_actions_from_xml(root, logger) -> list` — Summarizes action steps
- `parse_json_file(file_path, relative_path, ...) -> dict` — Parses JSON auxiliary files

**`_node_analysis.py`** - AA360 node traversal
- `analyze_nodes(nodes, ...) -> dict` — Main node analyzer; returns stats and observations
- `extract_task_call(node) -> dict` — Parses runTask invocations
- `extract_credential_from_node(node) -> dict` — Detects CredentialVault usage
- `extract_systems_from_node(node) -> list` — Detects URLs, DB connections, etc.
- `should_keep_summary(node, depth) -> bool` — Filters which nodes to document

**`_project_support.py`** - Project-level aggregation
- `discover_task_entries(project_root, manifest) -> list` — Finds all taskbot entries
- `mark_entrypoints(tasks) -> None` — Marks which taskbots are entry points
- `collect_project_systems(tasks) -> list` — Deduplicates systems across taskbots
- `collect_project_credentials(tasks) -> list` — Deduplicates credentials
- `build_file_summary(project_root, manifest, tasks) -> dict` — Counts auxiliary files

---

### Analysis Layer

**Location:** `app/analysis/`

#### `build_flow(tasks: list) -> dict`
**File:** `app/analysis/flow_builder.py`

**Purpose:** Builds a directed graph of task dependencies.

**Algorithm:**
1. Create node for each entrypoint taskbot
2. Traverse task_calls to build edges
3. Topological sort to determine execution order

**Returns:**
```python
{
    "nodes": [
        {"name": str, "type": str}
    ],
    "edges": [
        {"source": str, "target": str, "label": str}
    ],
    "summary": {
        "total_nodes": int,
        "total_edges": int,
        "entry_count": int,
    }
}
```

#### `build_tree(path: str, prefix: str = "", include_stats: bool = True) -> str`
**File:** `app/analysis/tree_builder.py`

**Purpose:** Generates ASCII directory tree representation.

**Excludes:** `.metadata`, `.jar`, image files, cache folders

**Returns:** Multi-line string with tree structure and file size annotations

#### `describe_task_with_ai(task: dict, settings: AppSettings = None) -> dict`
**File:** `app/analysis/task_ai_describer.py`

**Purpose:** Analyzes a taskbot and returns functional description and quality insights.

**Logic:**
- If AI is enabled and configured: sends structured prompt to LLM (OpenAI, Claude, etc.)
- Falls back to heuristic analysis if AI disabled or fails

**Returns:**
```python
{
    "task_profile": str,           # "core", "lookup", "utility", "support"
    "what_it_does": str,           # Functional summary
    "business_function": str,      # Business purpose
    "criticality": str,            # "alta", "media", "baja"
    "risks": list[str],            # Risk observations
    "recommendations": list[str],  # Improvement suggestions
    "source": str,                 # "ai" or "heuristic"
    "confidence": str,             # "alta", "media", "baja"
}
```

#### `build_quality_task_descriptions(tasks: list, settings: AppSettings = None) -> dict`
**File:** `app/analysis/task_ai_describer.py`

**Purpose:** Batch task analysis for all taskbots.

**Returns:**
```python
{
    "TaskbotName": {
        # task description dict (see describe_task_with_ai)
    },
    ...
}
```

#### `build_quality_prioritization(project_data: dict, task_descriptions: dict, observations: list, settings: AppSettings = None) -> dict`
**File:** `app/analysis/task_ai_describer.py`

**Purpose:** Builds prioritized list of quality findings and remediation plan.

**Returns:**
```python
{
    "priority_findings": [
        {
            "severity": "bloqueante|alto|medio|bajo",
            "task": str,              # Taskbot name
            "title": str,             # Finding title
            "why": str,               # Why it matters
        }
    ],
    "sprint_plan": [
        {
            "priority": "P1|P2|P3",
            "action": str,            # What to do
            "effort": "S|M|L",        # Estimated effort
            "impact": str,            # Expected impact
            "owner": str,             # Who should fix
            "tasks": list[str],       # Related taskbots
            "done_criteria": list[str],
        }
    ],
    "source": str,                # "ai" or "heuristic"
    "confidence": str,            # "alta", "media", "baja"
}
```

---

### Generator Layer

**Location:** `app/generator/`

#### **SDD Document:** `generate_sdd(project_data: dict, tree: str, flow: dict = None, ...) -> str`
**File:** `app/generator/sdd_generator.py`

**Purpose:** Generates Markdown SDD document with all project information.

**Sections Generated:**
1. Executive Summary (AI-powered)
2. General Information
3. Project Statistics
4. Flow Diagram
5. Dependency Contracts
6. Taskbot Inventory
7. Variable Contracts
8. Credentials & Vaults
9. External Systems
10. AA360 Packages

**Returns:** Markdown string content

#### **Quality Report:** `generate_quality_file(project_data: dict, output_path: str, settings: AppSettings = None) -> str`
**File:** `app/generator/sdd_generator.py`

**Purpose:** Generates Markdown quality report with findings and sprint plan.

**Sections:**
1. Summary (task count, observation count)
2. Findings
3. Prioritized Findings
4. Remediation Sprint Plan
5. Task Interpretations

**Returns:** File path

#### **Word Export:** `generate_sdd_word(project_data: dict, tree: str, output_path: str, ...) -> str`
**File:** `app/generator/word_generator.py`

**Purpose:** Exports SDD to professional DOCX with styling.

**Features:**
- Cover page with project branding
- Auto-generated Table of Contents
- Colored headers and tables
- Image embedding (flow diagram)
- Professional fonts and spacing

**Returns:** File path

#### **Word Quality:** `generate_quality_word(project_data: dict, output_path: str, md_content: str = None) -> str`
**File:** `app/generator/word_generator.py`

**Purpose:** Exports quality report to DOCX.

**Returns:** File path

#### **PDF Export:** `generate_sdd_pdf(md_content: str, output_path: str, project_name: str = "Proyecto", ...) -> str`
**File:** `app/generator/pdf_generator.py`

**Purpose:** Exports Markdown to PDF using reportlab.

**Returns:** File path

#### **PDF Quality:** `generate_quality_pdf(md_content: str, output_path: str, project_name: str = "Proyecto") -> str`
**File:** `app/generator/pdf_generator.py`

**Purpose:** Exports quality report to PDF.

**Returns:** File path

#### **SVG Diagram:** `generate_flow_svg(flow: dict) -> str`
**File:** `app/generator/diagram_generator.py`

**Purpose:** Generates interactive SVG diagram of task flow.

**Algorithm:**
1. Calculate node positions (BFS from entrypoints)
2. Draw nodes with color coding
3. Draw edges with labels
4. Add start/end indicators

**Returns:** SVG string content

#### **SVG to PNG:** `convert_svg_to_png(svg_path: str, png_path: str, scale: float = 3.0) -> str`
**File:** `app/generator/diagram_generator.py`

**Purpose:** Converts SVG to PNG for embedding in DOCX (uses svglib + reportlab).

**Returns:** PNG file path

---

### Ingestion Layer

**Location:** `app/ingestion/`

#### `save_file(file: UploadFile, settings: AppSettings = None) -> str`
**File:** `app/ingestion/uploader.py`

**Purpose:** Safely uploads and saves ZIP file to temporary directory.

**Safety:**
- Validates `.zip` extension
- Enforces max file size (default: 500MB)
- Streams file in chunks (default: 1MB)
- Creates timestamped folder

**Returns:** Absolute path to saved ZIP file

**Raises:** `ValueError` for invalid file or size violations

#### `extract_project(zip_path: str, settings: AppSettings = None) -> str`
**File:** `app/ingestion/extractor.py`

**Purpose:** Safely extracts ZIP contents with validation.

**Safety:**
- Tests ZIP integrity
- Validates member paths (no path traversal)
- Enforces max extraction size (default: 1GB)
- Creates extraction folder

**Returns:** Absolute path to extraction folder

**Raises:** `ValueError` for bad ZIP or path traversal attempts

---

## Core Utilities

### `app/observability.py`

#### `RequestIdMiddleware`
**Purpose:** Adds unique `request_id` to each HTTP request for tracing.

**Environment:** Sets `request_id` in context for logging

#### `ContextLoggerAdapter`
**Purpose:** Wraps logger to include `request_id` in all log messages.

**Usage:**
```python
logger = ContextLoggerAdapter(logging.getLogger(__name__))
logger.info("Message")  # Includes request_id in output
```

### `app/limits.py`

#### `ConcurrencyLimiter`
**Purpose:** Semaphore-based concurrency control with timeout.

**Configuration:** Max 5 concurrent operations

#### `EndpointRateLimitMiddleware`
**Purpose:** Sliding-window rate limiting per IP/endpoint.

**Configuration:**
- Per-IP: 30 requests/minute
- Per-path: 100 requests/minute

---

## Configuration & Settings

### `app/application/settings.py`

#### `AppSettings`
**Purpose:** Centralized configuration via environment variables.

**Key Fields:**
```python
class AppSettings:
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    
    # Upload/Extraction limits
    max_file_size: int = 500 * 1024 * 1024        # 500MB
    max_extraction_size: int = 1024 * 1024 * 1024  # 1GB
    upload_chunk_size: int = 1024 * 1024           # 1MB
    
    # AI Integration
    ai_quality_enabled: bool = False
    ai_provider: str = "openai"
    ai_model: str = "gpt-4"
    ai_api_key: str = ""
    ai_api_base_url: str = "https://api.openai.com/v1"
    ai_timeout_seconds: int = 30
    
    # Concurrency & Rate Limiting
    max_concurrency: int = 5
    rate_limit_per_ip_per_minute: int = 30
    rate_limit_per_path_per_minute: int = 100
    
    # Output directories
    tmp_dir: Path = Path("./tmp")
    output_dir: Path = Path("./output")
    
    @classmethod
    def from_env(cls) -> "AppSettings":
        """Load configuration from environment variables (.env or system)"""
```

---

## Examples

### Generate SDD End-to-End

```python
from app.application.use_cases.generate_sdd import generate_sdd

result = generate_sdd("/path/to/uploaded/bot.zip")
print(result["sdd_markdown"])
print(result["sdd_word"])
print(result["flow_svg"])
```

### Generate Quality Report

```python
from app.application.use_cases.generate_quality import generate_quality

result = generate_quality("/path/to/uploaded/bot.zip")
print(result["quality_markdown"])
```

### Parse Project Directly

```python
from app.parser.project_parser import parse_project

project_data = parse_project("/path/to/project")
print(project_data["tasks"])
print(project_data["systems"])
print(project_data["credentials"])
```

### Build Quality Analysis

```python
from app.analysis.task_ai_describer import build_quality_task_descriptions, build_quality_prioritization

task_descriptions = build_quality_task_descriptions(project_data["tasks"])
findings = build_quality_prioritization(project_data, task_descriptions, [])
print(findings["sprint_plan"])
```

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_FILE` | 400 | File is not a .zip |
| `FILE_TOO_LARGE` | 400 | Exceeds max file size |
| `BAD_ZIP` | 400 | ZIP is corrupted |
| `EXTRACTION_ERROR` | 400 | Extraction failed (size, traversal, etc.) |
| `PARSE_ERROR` | 400 | Project parsing failed |
| `GENERATION_ERROR` | 500 | Document generation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVICE_OVERLOADED` | 503 | Concurrency limit exceeded |

---

## Environment Variables

```bash
# API
API_PORT=8000
API_HOST=0.0.0.0

# Upload/Extraction
MAX_FILE_SIZE=524288000          # 500MB
MAX_EXTRACTION_SIZE=1073741824   # 1GB
UPLOAD_CHUNK_SIZE=1048576       # 1MB

# AI Integration
AI_QUALITY_ENABLED=false
AI_PROVIDER=openai
AI_MODEL=gpt-4
AI_API_KEY=sk-...
AI_API_BASE_URL=https://api.openai.com/v1
AI_TIMEOUT_SECONDS=30

# Concurrency & Rate Limiting
MAX_CONCURRENCY=5
RATE_LIMIT_PER_IP_PER_MINUTE=30
RATE_LIMIT_PER_PATH_PER_MINUTE=100

# Directories
TMP_DIR=./tmp
OUTPUT_DIR=./output
```

---

**Last Updated:** 2026-04-17  
**Version:** 1.0.0
