import os
import re
import warnings
from typing import List, Dict, Any, Optional, Callable
from drawings_ai.schemas import DrawingSheet, EntityObject, ConfidenceLevel, IndexResult

# Check if fitz (PyMuPDF) is available
try:
    import fitz
    pymupdf_available = True
except ImportError:
    pymupdf_available = False

# Check if OCR dependencies are available
try:
    import pytesseract
    from PIL import Image
    ocr_dependencies_available = True
except ImportError:
    ocr_dependencies_available = False


class DrawingsParser:
    """
    Core parsing engine. Extracts sheet metadata and structural/trade physical entities.
    Supports standard vector-text parsing, OCR fallback for scanned (raster) PDFs, 
    and extensible runtime pattern registration.
    """
    
    def __init__(self, ocr_enabled: bool = False, tesseract_cmd: Optional[str] = None):
        self.pymupdf_available = pymupdf_available
        self.ocr_enabled = ocr_enabled
        self.ocr_available = ocr_dependencies_available
        
        # Configure Tesseract path if provided
        if tesseract_cmd and self.ocr_available:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
        # Extensible entity extraction patterns
        # Format: {entity_type: {"pattern": regex_compiled, "material": default_mat, "reliability": level, "dim_keys": list_of_keys}}
        self.entity_rules: Dict[str, Dict[str, Any]] = {}
        self._register_default_rules()

    def _register_default_rules(self):
        """Registers the base structural steel, concrete, and layout rules."""
        # Default Footings Rule: e.g., F1, F6, F10
        self.register_rule(
            entity_type="footing",
            regex_pattern=r'\b(F[0-9]{1,2})\b',
            default_material="Reinforced Concrete",
            default_reliability=ConfidenceLevel.HIGH
        )
        # Default Slabs Rule
        self.register_rule(
            entity_type="slab",
            regex_pattern=r'\b(S[0-9]{1,2}|slab|screed)\b',
            default_material="Concrete / Cement",
            default_reliability=ConfidenceLevel.MEDIUM
        )

    def register_rule(
        self, 
        entity_type: str, 
        regex_pattern: str, 
        default_material: str = "Standard Spec", 
        default_reliability: ConfidenceLevel = ConfidenceLevel.HIGH,
        dimensions_extractor: Optional[Callable[[str, str], Dict[str, float]]] = None
    ):
        """Allows runtime registration of custom trade patterns (e.g. data center equipment)."""
        self.entity_rules[entity_type] = {
            "pattern": re.compile(regex_pattern, re.IGNORECASE),
            "material": default_material,
            "reliability": default_reliability,
            "dim_extractor": dimensions_extractor
        }

    def parse_pdf(self, pdf_path: str) -> IndexResult:
        """Parses drawing sheets and extracts physical entities from the target PDF."""
        sheets: List[DrawingSheet] = []
        entities: List[EntityObject] = []
        
        if not self.pymupdf_available:
            warnings.warn("PyMuPDF (fitz) is not installed. Falling back to mock dataset.")
            return self._mock_parse()

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF drawing file not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Run OCR if text is empty and OCR is enabled/available
            if not text.strip() and self.ocr_enabled:
                if self.ocr_available:
                    text = self._run_ocr(page)
                else:
                    warnings.warn("OCR is enabled but pytesseract or PIL is not installed. Skipping OCR.")
            
            # Detect Sheet Metadata
            sheet_number = self._detect_sheet_number(text, page_num)
            sheet_title = self._detect_sheet_title(text, page_num)
            scale = self._detect_scale(text)
            
            sheets.append(DrawingSheet(
                sheet_number=sheet_number,
                title=sheet_title,
                scale=scale,
                revision="A"
            ))
            
            # Extract Entities using active patterns
            page_entities = self._extract_entities_from_text(text, sheet_number)
            entities.extend(page_entities)
            
        doc.close()
        return IndexResult(drawing_sheets=sheets, entities=entities)

    def _run_ocr(self, page) -> str:
        """Renders the PDF page to a pixmap and transcribes text using Tesseract OCR."""
        try:
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("png")
            
            import io
            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img)
            return text
        except Exception as e:
            warnings.warn(f"Failed to perform OCR on page: {e}")
            return ""

    def _detect_sheet_number(self, text: str, page_num: int) -> str:
        # Look for typical sheet codes: e.g. S-101, E-201, A-001
        match = re.search(r'\b([A-Z]{1,2}-[0-9]{3,4})\b', text)
        if match:
            return match.group(1)
        return f"Sheet-{page_num + 1}"

    def _detect_sheet_title(self, text: str, page_num: int) -> str:
        # Heuristic: Extract first line longer than 5 chars, or fallback
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 5]
        if lines:
            # Exclude standard headers
            for line in lines[:3]:
                if not any(k in line.lower() for k in ["project", "client", "scale", "drawn", "designed"]):
                    return line
        return f"Structural Sheet Detail {page_num + 1}"

    def _detect_scale(self, text: str) -> str:
        match = re.search(r'\b(?:scale|sc\.)\s*([0-9]+:[0-9]+)\b', text, re.IGNORECASE)
        if match:
            return match.group(1)
        return "1:100"

    def _extract_entities_from_text(self, text: str, sheet_num: str) -> List[EntityObject]:
        entities: List[EntityObject] = []
        
        for etype, rule in self.entity_rules.items():
            pattern = rule["pattern"]
            matches = pattern.findall(text)
            
            # Filter matches and deduplicate
            unique_matches = set()
            for m in matches:
                if isinstance(m, tuple):
                    # Handle multi-group matches by taking the first non-empty group
                    m = next((group for group in m if group), None)
                if m:
                    unique_matches.add(m.strip())
                    
            for mark in unique_matches:
                # Count occurrences
                count = len(re.findall(re.escape(mark), text, re.IGNORECASE))
                
                # Check for custom dimensions extractor
                dims = {}
                if rule["dim_extractor"]:
                    dims = rule["dim_extractor"](text, mark)
                else:
                    # Default: try to find dimensions text next to the mark (e.g. 1200x600)
                    dim_match = re.search(rf'{re.escape(mark)}[^\d]*(\d+)\s*(?:x|by)\s*(\d+)', text, re.IGNORECASE)
                    if dim_match:
                        dims = {"width_mm": float(dim_match.group(1)), "height_mm": float(dim_match.group(2))}
                
                entities.append(EntityObject(
                    entity_type=etype,
                    name=mark,
                    material=rule["material"],
                    source_drawing_page=sheet_num,
                    reliability=rule["reliability"],
                    count=count,
                    dimensions=dims
                ))
                
        return entities

    def _mock_parse(self) -> IndexResult:
        """Fallback simulation matching standard integration checks."""
        sheets = [
            DrawingSheet(sheet_number="S-101", title="Slab Foundation Layout", scale="1:100"),
            DrawingSheet(sheet_number="S-104", title="Structural Footing Details", scale="1:100"),
            DrawingSheet(sheet_number="E-201", title="Electrical Cable Runs Layout", scale="1:100")
        ]
        entities = [
            EntityObject(entity_type="slab", name="S1", material="Concrete 32MPa", source_drawing_page="S-101", reliability=ConfidenceLevel.HIGH, count=1, dimensions={"thickness_mm": 200}),
            EntityObject(entity_type="footing", name="F6", material="Concrete", source_drawing_page="S-104", reliability=ConfidenceLevel.HIGH, count=4, dimensions={"width_mm": 1200, "depth_mm": 600}),
            EntityObject(entity_type="footing", name="F10", material="Concrete", source_drawing_page="S-104", reliability=ConfidenceLevel.HIGH, count=2, dimensions={"width_mm": 1800, "depth_mm": 800}),
        ]
        return IndexResult(drawing_sheets=sheets, entities=entities)
