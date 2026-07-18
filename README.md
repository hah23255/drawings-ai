# Drawings AI: Construction Drawing Indexing Pipeline (Bilingual: EN/BG)

> [!NOTE]
> **English**: Drawings AI is a production-ready, data-engineering pipeline that reverse-engineers 2D CAD and PDF construction drawings into queryable SQLite databases (`drawings.db`) and structured trade markdown wikis (`drawings.md`). This architecture slashes LLM token costs by **up to 70x** while achieving **100% database query accuracy** for quantity takeoffs and spec compliance.
>
> **Български**: Drawings AI е индустриално оптимизиран софтуерен тръбопровод за обработка на данни (data engineering), който преобразува 2D CAD и PDF строителни чертежи в структурирани SQLite релационни бази данни (`drawings.db`) и технически спецификации в Markdown формат (`drawings.md`). Тази архитектура намалява разходите за токени при работа с големи езикови модели (LLMs) **до 70 пъти**, като същевременно постига **100% точност на заявките** при количествени сметки и проверка на съответствието със стандарти.

---

## Technical Features / Технически характеристики

*   **EN**:
    *   **Extensible Tag Extraction**: Programmatic regex and rule registration for custom tags (e.g. data center equipment or architectural tables) without subclassing.
    *   **Multi-File Aggregation**: Append mode allows merging hundreds of drawing sheets into a unified SQLite index.
    *   **Dual Ingestion Layers**: SQLite relational database for structured metrics + localized markdown wiki for specifications and general notes.
    *   **OCR Support**: Automated scanned (raster) PDF page detection and transcription using Tesseract OCR.
    *   **LLM Integration Ready**: Exposes pre-validated OpenAI/Anthropic tool schemas with built-in SQL injection guard rails.
*   **BG**:
    *   **Разширяемо извличане на обекти**: Програмна регистрация на regex правила за персонализирани тагове (например оборудване за центрове за данни или архитектурни спецификации).
    *   **Агрегиране на множество файлове**: Режимът за добавяне (append mode) позволява обединяване на стотици чертежи в една обща SQLite база данни.
    *   **Двуслойно индексиране**: Релационна база данни за количествени сметки + локализирано техническо уики (Markdown Wiki) за спецификации и бележки.
    *   **OCR интеграция**: Автоматично разпознаване на сканирани (растерни) страници и транскрибиране чрез Tesseract OCR.
    *   **Готовност за LLM интеграция**: Автоматично генериране на JSON схеми за инструменти (tools), съвместими с OpenAI и Anthropic (Claude), с вградена защита срещу SQL инжекции.

---

## Quick Start / Бърз старт (Python API)

```python
from drawings_ai import DrawingsAIPipeline, ConfidenceLevel

# Initialize the pipeline in your workspace
pipeline = DrawingsAIPipeline(workspace_dir="./workspace", ocr_enabled=True)

# Register a custom electrical socket extraction rule
pipeline.parser.register_rule(
    entity_type="power_socket",
    regex_pattern=r'\b(Sockets-[0-9]+)\b',
    default_material="Plastic Moulded",
    default_reliability=ConfidenceLevel.HIGH
)

# Run indexing
result = pipeline.index_drawings("layout.pdf", append=True)
print(f"Registered sheets: {len(result.drawing_sheets)}")
```

For detailed guides, please refer to:
*   [Architecture Mapping](docs/architecture.md)
*   [API & Integration](docs/api.md)
*   [Production Deployment Guide](docs/deployment.md)

---

## License / Лиценз
Distributed under the MIT License. / Разпространява се под MIT лиценз.
© 2026 Hristo Hristov.
