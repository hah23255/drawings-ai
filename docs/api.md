# Drawings AI: API & Tool Integration Guide

This guide describes how to programmatically integrate Drawings AI in your Python applications or expose its toolkits to LLM agents.

## 1. Pipeline Execution API

```python
from drawings_ai import DrawingsAIPipeline, ConfidenceLevel

# Initialize the pipeline
pipeline = DrawingsAIPipeline(workspace_dir="./project_workspace", ocr_enabled=True)

# Register custom entity rule (e.g. data center UPS systems)
pipeline.parser.register_rule(
    entity_type="ups_system",
    regex_pattern=r'\b(UPS-[0-9]+kVA)\b',
    default_material="Electrical Equipment",
    default_reliability=ConfidenceLevel.HIGH
)

# Run indexing (append mode enabled to aggregate multiple files)
result = pipeline.index_drawings("electrical_layout.pdf", append=True)
print(f"Indexed {len(result.drawing_sheets)} sheets and {len(result.entities)} entities.")
```

## 2. LLM Tool Integration (OpenAI/Anthropic)

Expose the database and wiki interfaces as tools for Claude or GPT models:

```python
# Retrieve OpenAI-compatible JSON tool schemas
tool_schemas = pipeline.get_llm_tools()

# Expose to LLM
# response = client.chat.completions.create(
#     model="gpt-4o",
#     messages=messages,
#     tools=tool_schemas
# )

# Execute tool call requested by the LLM
tool_name = "query_drawings_database"
args = {"sql_query": "SELECT name, count FROM entities WHERE entity_type='ups_system'"}

toolkit = pipeline.get_toolkit()
result = toolkit.execute_tool(tool_name, args)
print(result)
```

## 3. Database Schema

The SQLite database (`drawings.db`) has the following tables:

1.  **`sheets`**: List of drawing sheets.
    *   `sheet_number` (TEXT, PK): Sheet identifier (e.g., "S-101").
    *   `title` (TEXT): Title block name.
    *   `scale` (TEXT): Drawing scale.
    *   `revision` (TEXT): Revision stage.
2.  **`entities`**: Physical objects.
    *   `id` (INTEGER, PK): Auto-incremented ID.
    *   `entity_type` (TEXT): Category.
    *   `name` (TEXT): Object name.
    *   `material` (TEXT): Material composition.
    *   `source_drawing_page` (TEXT, FK): Sheet reference.
    *   `reliability` (TEXT): Confidence rating.
    *   `count` (INTEGER): Quantity.
3.  **`dimensions`**: Object dimensions.
    *   `entity_id` (INTEGER, FK): Parent entity ID.
    *   `dimension_key` (TEXT): Metric name (e.g., "width_mm").
    *   `dimension_value` (REAL): Numerical measurement.
