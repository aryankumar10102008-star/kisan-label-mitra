import os
import tempfile
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

try:
    from backend.gemma import extract_label, generate_explanation
    from backend.trust import lookup_toxicity, compute_safe_harvest, check_crop
except ImportError:
    from gemma import extract_label, generate_explanation
    from trust import lookup_toxicity, compute_safe_harvest, check_crop

app = FastAPI(title="Kisan Label Mitra API")

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(default=None),
    crop: str = Form(default=""),
    spray_date: str = Form(default=""),
):
    if image is None or not image.filename:
        return JSONResponse(
            status_code=400,
            content={"error": "An image file is required."},
        )

    content_type = (image.content_type or "").lower().split(";")[0].strip()
    if content_type == "image/jpg":
        content_type = "image/jpeg"

    if content_type not in ALLOWED_MIME_TYPES:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid file type. Only image/jpeg and image/png are accepted."},
        )

    if not crop or not crop.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Crop field is required."},
        )

    if not spray_date or not spray_date.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "spray_date is required."},
        )

    try:
        datetime.strptime(spray_date.strip(), "%Y-%m-%d")
    except (ValueError, TypeError):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid spray_date format. Expected format is YYYY-MM-DD."},
        )

    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=413,
            content={"error": "File size exceeds 5 MB limit."},
        )

    if len(contents) == 0:
        return JSONResponse(
            status_code=400,
            content={"error": "Uploaded file is empty."},
        )

    suffix = ".jpg" if content_type == "image/jpeg" else ".png"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name
    try:
        temp_file.write(contents)
        temp_file.close()

        # Step 1: AI Vision Extraction (Strict extraction only; no safety decisions)
        validated_label = extract_label(temp_path, content_type)
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={"error": f"Failed to extract label from image: {str(e)}"},
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    label_data = (
        validated_label.model_dump()
        if hasattr(validated_label, "model_dump")
        else validated_label.dict()
        if hasattr(validated_label, "dict")
        else validated_label
    )

    # Step 2: Separate authoritative safety calculations (backend/trust.py is the ONLY authority)
    # Toxicity Classification
    toxicity_source_text = None
    if validated_label.warning_statements and validated_label.warning_statements.supporting_text:
        toxicity_source_text = validated_label.warning_statements.supporting_text
    elif validated_label.warning_statements and validated_label.warning_statements.value:
        toxicity_source_text = str(validated_label.warning_statements.value)
    toxicity_result = lookup_toxicity(toxicity_source_text)

    # Authoritative Crop Safety Check
    crops_text = (
        validated_label.registered_crops.text
        if hasattr(validated_label, "registered_crops") and validated_label.registered_crops.text
        else validated_label.crops_listed.text
        if hasattr(validated_label, "crops_listed") and validated_label.crops_listed and validated_label.crops_listed.text
        else ""
    )
    crop_result = check_crop(crop, crops_text)

    # Authoritative Safe Harvest Date Calculation
    waiting_text = (
        validated_label.waiting_period.supporting_text
        if hasattr(validated_label, "waiting_period") and validated_label.waiting_period.supporting_text
        else validated_label.waiting_period.text
        if hasattr(validated_label, "waiting_period") and validated_label.waiting_period.text
        else ""
    )
    harvest_result = compute_safe_harvest(spray_date, waiting_text)

    safety_bundle = {
        "toxicity": toxicity_result,
        "crop_check": crop_result,
        "safe_harvest": harvest_result,
    }

    # Step 3: Collect warnings (blurry image, unreadable, manual verification needed)
    warnings = list(getattr(validated_label, "warnings", []))
    if not getattr(validated_label, "is_readable", True) or getattr(validated_label, "image_quality", "clear") in (
        "blurry",
        "incomplete",
        "unreadable",
        "partial",
    ):
        quality_warning = "The image appears blurry, incomplete, or unreadable. Please upload a clear photo of the entire label."
        if quality_warning not in warnings:
            warnings.append(quality_warning)

    if getattr(validated_label, "needs_manual_verification", False):
        verification_warning = "One or more label fields were flagged for manual verification before spraying."
        if verification_warning not in warnings:
            warnings.append(verification_warning)

    # Step 4: Farmer-friendly Explanation using already validated facts + safety results
    explanation = None
    try:
        explanation = generate_explanation(
            label_data,
            crop=crop,
            spray_date=spray_date,
            safety=safety_bundle,
            warnings=warnings,
        )
    except Exception:
        pass

    response_content = {
        "label": label_data,
        "safety": safety_bundle,
        "warnings": warnings,
    }
    if explanation:
        response_content["explanation"] = explanation

    return response_content
