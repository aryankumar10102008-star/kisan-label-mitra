import json
import pytest
from unittest import mock

from backend.schemas import Label, ExtractedField
from backend.gemma import (
    _parse_and_validate,
    _validate_extracted_values,
    generate_explanation,
    extract_label,
)
from backend.trust import lookup_toxicity, compute_safe_harvest, check_crop


MOCK_LABEL1_RAW = {
    "product_name": {
        "value": "TestKill 20 EC",
        "supporting_text": "Product Name: TestKill 20 EC",
        "confidence": "high",
    },
    "active_ingredient": {
        "value": "Cypermethrin",
        "supporting_text": "Active Ingredient: Cypermethrin 10%",
        "confidence": "high",
    },
    "concentration": {
        "value": "10%",
        "supporting_text": "Cypermethrin 10%",
        "confidence": "high",
    },
    "formulation": {
        "value": "EC",
        "supporting_text": "TestKill 20 EC",
        "confidence": "high",
    },
    "registered_crops": {
        "value": "Cotton, Wheat",
        "supporting_text": "Crops: Cotton, Wheat",
        "confidence": "high",
    },
    "waiting_period": {
        "value": "15 days",
        "supporting_text": "Waiting Period: 15 days",
        "confidence": "high",
    },
    "dose": {
        "value": None,
        "supporting_text": None,
        "confidence": "unknown",
    },
    "warning_statements": {
        "value": "Wash skin with soap and water.",
        "supporting_text": "First Aid: Wash skin with soap and water.",
        "confidence": "high",
    },
    "image_quality": "clear",
    "is_readable": True,
}


class TestConsistencyAndReliability:
    def test_five_identical_runs_consistency(self):
        """Test the same pesticide label 5 times to prove zero variance in extracted fields."""
        results = []
        for i in range(5):
            parsed = _parse_and_validate(json.dumps(MOCK_LABEL1_RAW))
            results.append(parsed.model_dump())

        first = results[0]
        differences = []
        for idx, res in enumerate(results[1:], start=2):
            for field in [
                "product_name",
                "active_ingredient",
                "concentration",
                "formulation",
                "registered_crops",
                "waiting_period",
                "dose",
                "warning_statements",
            ]:
                val1 = first[field]["value"]
                val2 = res[field]["value"]
                if val1 != val2:
                    differences.append(f"Run 1 vs Run {idx} mismatch in {field}: {val1} != {val2}")

        assert len(differences) == 0, f"Differences found across runs: {differences}"
        assert first["dose"]["value"] is None
        assert first["dose"]["confidence"] == "unknown"
        assert first["waiting_period"]["value"] == "15 days"
        assert first["concentration"]["value"] == "10%"

    def test_never_guess_missing_info(self):
        """Ensure missing fields return null and unknown."""
        raw = dict(MOCK_LABEL1_RAW)
        raw["dose"] = {"value": "none", "supporting_text": "n/a", "confidence": "high"}
        parsed = _parse_and_validate(json.dumps(raw))
        assert parsed.dose.value is None
        assert parsed.dose.supporting_text is None
        assert parsed.dose.confidence == "unknown"
        assert parsed.dose.found is False

    def test_waiting_period_non_negative_validation(self):
        """Negative waiting period must be flagged for manual verification."""
        raw = dict(MOCK_LABEL1_RAW)
        raw["waiting_period"] = {
            "value": "-5 days",
            "supporting_text": "Wait -5 days",
            "confidence": "high",
        }
        parsed = _parse_and_validate(json.dumps(raw))
        assert parsed.waiting_period.verification_required is True
        assert parsed.waiting_period.confidence == "low"
        assert parsed.needs_manual_verification is True

    def test_crop_names_checked_against_printed_label(self):
        """Hallucinated crops not in supporting text must be flagged."""
        raw = dict(MOCK_LABEL1_RAW)
        raw["registered_crops"] = {
            "value": "Cotton, Wheat, Sugarcane",
            "supporting_text": "Crops: Cotton, Wheat",
            "confidence": "high",
        }
        parsed = _parse_and_validate(json.dumps(raw))
        # Sugarcane is not on label, Cotton and Wheat are
        assert "Sugarcane" not in parsed.registered_crops.value
        assert "Cotton" in parsed.registered_crops.value
        assert parsed.registered_crops.verification_required is True

    def test_concentration_preserves_units(self):
        """Concentration without units must be restored from supporting text or flagged."""
        raw = dict(MOCK_LABEL1_RAW)
        raw["concentration"] = {
            "value": "10",
            "supporting_text": "Cypermethrin 10% EC",
            "confidence": "high",
        }
        parsed = _parse_and_validate(json.dumps(raw))
        assert "%" in parsed.concentration.value

    def test_trust_py_authoritative_for_safety(self):
        """Ensure trust.py is the authority for toxicity, crop check, and harvest date."""
        tox = lookup_toxicity("yellow band")
        assert tox["colour"] == "yellow"
        assert tox["meaning_en"] == "highly toxic"

        crop_res = check_crop("Cotton", "Cotton, Wheat")
        assert crop_res["result"] == "listed"

        harvest_res = compute_safe_harvest("2026-10-30", "15 days")
        assert harvest_res["date"] == "2026-11-14"
        assert harvest_res["days"] == 15

