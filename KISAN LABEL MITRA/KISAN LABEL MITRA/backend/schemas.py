from typing import Any, Literal, Optional, List
from pydantic import BaseModel, Field

ConfidenceLevel = Literal["high", "medium", "low", "unknown"]


class ExtractedField(BaseModel):
    value: Optional[Any] = None
    supporting_text: Optional[str] = None
    confidence: ConfidenceLevel = "unknown"
    # Backward compatibility with existing callers/tests:
    text: str = ""
    found: bool = False
    verification_required: bool = False
    verification_reason: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        # If legacy code provided text and found, but not value
        if self.text and self.value is None and self.found:
            self.value = self.text
            if not self.supporting_text:
                self.supporting_text = self.text
            if self.confidence == "unknown":
                self.confidence = "high"
        # If value is provided, sync text and found
        elif self.value is not None:
            if not self.text:
                self.text = str(self.value)
            self.found = bool(self.confidence != "unknown" and self.value is not None)
        else:
            self.found = False
            self.text = ""


# Alias for backward compatibility with existing tests
LabelField = ExtractedField


class Label(BaseModel):
    # Required fields from Task 4:
    product_name: ExtractedField = Field(default_factory=ExtractedField)
    active_ingredient: ExtractedField = Field(default_factory=ExtractedField)
    concentration: ExtractedField = Field(default_factory=ExtractedField)
    formulation: ExtractedField = Field(default_factory=ExtractedField)
    registered_crops: ExtractedField = Field(default_factory=ExtractedField)
    waiting_period: ExtractedField = Field(default_factory=ExtractedField)
    dose: ExtractedField = Field(default_factory=ExtractedField)
    warning_statements: ExtractedField = Field(default_factory=ExtractedField)

    # Legacy fields for full backward compatibility:
    crops_listed: Optional[ExtractedField] = None
    protective_gear: Optional[ExtractedField] = None
    first_aid: Optional[ExtractedField] = None

    # Quality and manual verification metadata:
    image_quality: str = "clear"  # clear, blurry, incomplete, unreadable, partial
    is_readable: bool = True
    warnings: List[str] = Field(default_factory=list)
    needs_manual_verification: bool = False

    def model_post_init(self, __context: Any) -> None:
        # Sync crops_listed and registered_crops
        if self.crops_listed is not None and (self.registered_crops.value is None and not self.registered_crops.text):
            self.registered_crops = self.crops_listed
        elif self.crops_listed is None and (self.registered_crops.value is not None or self.registered_crops.text):
            self.crops_listed = self.registered_crops
        elif self.crops_listed is None:
            self.crops_listed = ExtractedField()

        if self.protective_gear is None:
            self.protective_gear = ExtractedField()
        if self.first_aid is None:
            self.first_aid = ExtractedField()
