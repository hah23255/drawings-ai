from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class ConfidenceLevel(str, Enum):
    HIGH = "High"       # Mapped from schedules or explicit text tags
    MEDIUM = "Medium"   # Extracted from plans or standard symbols
    LOW = "Low"         # Inferred/heuristic matches

class DrawingSheet(BaseModel):
    sheet_number: str = Field(description="Detected drawing sheet code, e.g., S-101, E-201")
    title: str = Field(description="Title block name of the drawing sheet")
    scale: Optional[str] = Field(default="1:100", description="Drawing scale, e.g., 1:50, 1:100")
    revision: Optional[str] = Field(default="A", description="Revision code of the drawing sheet")

class EntityObject(BaseModel):
    entity_type: str = Field(description="Physical category of the object, e.g., footing, slab, battery_bank")
    name: str = Field(description="Name or specific mark of the physical object")
    material: Optional[str] = Field(default=None, description="Material composition description")
    source_drawing_page: str = Field(description="The sheet number from which this object was extracted")
    reliability: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH)
    count: int = Field(default=1, description="Quantity count of this object on the layout page")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Key-value float dimensions in millimeters/meters")

class IndexResult(BaseModel):
    drawing_sheets: List[DrawingSheet] = Field(default_factory=list, description="List of all registered sheets")
    entities: List[EntityObject] = Field(default_factory=list, description="List of all physical objects extracted")
