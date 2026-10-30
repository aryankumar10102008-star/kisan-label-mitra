import base64
import json
import os
import re
from typing import Any, Optional
from dotenv import load_dotenv
import numpy as np
from PIL import Image
import requests

try:
    from backend.schemas import Label, ExtractedField
except ImportError:
    from schemas import Label, ExtractedField

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")


class OllamaModelNotFoundError(RuntimeError):
    """Raised when the requested model is not found in Ollama."""
    pass


SYSTEM_INSTRUCTION = (
    "You are a strict pesticide label reader and transcriber. "
    "You copy text EXACTLY as printed on the label. "
    "NEVER guess, assume, or invent doses, crops, waiting periods, or ingredients. "
    "For every field, return an object with:\n"
    "- 'value': the extracted clean value (string or null if not found)\n"
    "- 'supporting_text': the exact printed text snippet from the label (string or null if not found)\n"
    "- 'confidence': 'high', 'medium', 'low', or 'unknown'\n"
    "If a field is not explicitly printed on the label or is unreadable, set value to null, "
    "supporting_text to null, and confidence to 'unknown'.\n"
    "Preserve original units for concentration (e.g. '%', 'w/w', '20% EC').\n"
    "Never accept or generate free-form text. Output valid JSON strictly conforming to the requested schema."
)

PROMPT = (
    "Extract information from this pesticide label image and return valid JSON only.\n"
    "The JSON must have exactly these keys:\n"
    "- product_name: {\"value\": <string or null>, \"supporting_text\": <string or null>, \"confidence\": <\"high\"|\"medium\"|\"low\"|\"unknown\">}\n"
    "- active_ingredient: {\"value\": <string or null>, \"supporting_text\": <string or null>, \"confidence\": <\"high\"|\"medium\"|\"low\"|\"unknown\">}\n"
    "- concentration: {\"value\": <string or null>, \"supporting_text\": <string or null>, \"confidence\": <\"high\"|\"medium\"|\"low\"|\"unknown\">}\n"
    "- formulation: {\"value\": <string or null>, \"supporting_text\": <string or null>, \"confidence\": <\"high\"|\"medium\"|\"low\"|\"unknown\">}\n"
    "- registered_crops: {\"value\": <string or null>, \"supporting_text\": <string or null>, \"confidence\": <\"high\"|\"medium\"|\"low\"|\"unknown\">}\n"
    "- waiting_period: {\"value\": <string or null>, \"supporting_text\": <string or null>, \"confidence\": <\"high\"|\"medium\"|\"low\"|\"unknown\">}\n"
    "- dose: {\"value\": <string or null>, \"supporting_text\": <string or null>, \"confidence\": <\"high\"|\"medium\"|\"low\"|\"unknown\">}\n"
    "- warning_statements: {\"value\": <string or null>, \"supporting_text\": <string or null>, \"confidence\": <\"high\"|\"medium\"|\"low\"|\"unknown\">}\n"
    "- image_quality: \"clear\" | \"blurry\" | \"incomplete\" | \"unreadable\" | \"partial\"\n"
    "- is_readable: true | false\n\n"
    "CRITICAL: If a field is not printed or unreadable, return value: null, supporting_text: null, and confidence: \"unknown\"."
)

EXPLANATION_SYSTEM_INSTRUCTION = (
    "You are an agricultural safety communicator for Indian farmers. "
    "Given the already validated pesticide label data and authoritative safety calculations, "
    "generate clear, simple, farmer-friendly explanations in both Hindi (सरल हिंदी) and English. "
    "Never invent or alter dosages, crops, waiting periods, or safety classifications. "
    "Rely ONLY on the validated facts provided."
)


def _strip_markdown_code_fences(text: str) -> str:
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if match:
        return match.group(1).strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return cleaned


def detect_image_issues(image_path: str) -> tuple[str, bool, list[str]]:
    """
    Check if image is blurry, incomplete, or unreadable using Laplacian variance and resolution.
    Returns (quality_str, is_readable, warnings_list).
    """
    warnings: list[str] = []
    quality = "clear"
    is_readable = True

    try:
        if not os.path.exists(image_path):
            return "unreadable", False, ["Image file does not exist."]

        with Image.open(image_path) as img:
            width, height = img.size
            if width < 250 or height < 250:
                quality = "incomplete"
                is_readable = False
                warnings.append("Image resolution is very low; label details may not be readable.")

            gray = img.convert("L")
            arr = np.array(gray, dtype=np.float32)
            if arr.shape[0] > 10 and arr.shape[1] > 10:
                lap = (
                    arr[1:-1, 2:] + arr[1:-1, :-2] + arr[2:, 1:-1] + arr[:-2, 1:-1]
                    - 4 * arr[1:-1, 1:-1]
                )
                variance = float(lap.var())
                if variance < 30.0:
                    quality = "blurry"
                    is_readable = False
                    warnings.append("Image is severely blurry; label details could not be reliably verified.")
                elif variance < 80.0:
                    quality = "blurry"
                    warnings.append("Image is somewhat blurry; manual verification is advised.")
    except Exception:
        pass

    return quality, is_readable, warnings


def _clean_and_normalize_field(raw_val: Any) -> ExtractedField:
    """Normalize raw AI field data into a standard ExtractedField."""
    if isinstance(raw_val, dict):
        # Support both new schema ('value') and legacy schema ('text', 'found')
        val = raw_val.get("value")
        sup = raw_val.get("supporting_text")
        conf = str(raw_val.get("confidence", "")).lower()

        # Legacy format support
        if val is None and "text" in raw_val:
            found = bool(raw_val.get("found", False))
            txt = str(raw_val.get("text", "")).strip()
            if found and txt:
                val = txt
                sup = txt
                conf = "high"
            else:
                val = None
                sup = None
                conf = "unknown"

        # Check for placeholder strings meaning empty
        if val is not None:
            s_val = str(val).strip()
            if s_val.lower() in ("", "null", "none", "n/a", "not specified", "unknown", "not found", "false"):
                val = None
                sup = None
                conf = "unknown"

        if conf not in ("high", "medium", "low", "unknown"):
            conf = "unknown" if val is None else "medium"

        if val is None:
            conf = "unknown"
            sup = None

        return ExtractedField(
            value=val,
            supporting_text=sup,
            confidence=conf,
            text=str(val) if val is not None else "",
            found=bool(val is not None and conf != "unknown"),
        )
    elif isinstance(raw_val, str) and raw_val.strip():
        s = raw_val.strip()
        if s.lower() in ("null", "none", "n/a", "unknown", "not specified"):
            return ExtractedField(value=None, supporting_text=None, confidence="unknown", text="", found=False)
        return ExtractedField(value=s, supporting_text=s, confidence="medium", text=s, found=True)
    else:
        return ExtractedField(value=None, supporting_text=None, confidence="unknown", text="", found=False)


def _validate_extracted_values(
    fields: dict[str, ExtractedField],
    full_text_corpus: str,
    warnings: list[str],
) -> dict[str, ExtractedField]:
    """
    Validate extracted values according to strict rules:
    - Waiting period must be a valid non-negative number.
    - Crop names must be checked against the actual printed label.
    - Concentration must preserve its original units.
    - Conflicting or unreadable values must be flagged for manual verification.
    """
    # 1. Validate Waiting Period
    wp = fields.get("waiting_period")
    if wp and wp.value is not None:
        wp_val_str = str(wp.value).strip()
        wp_sup_str = str(wp.supporting_text or "").strip()

        # Check for negative numbers
        if re.search(r"-\s*\d+", wp_val_str) or re.search(r"-\s*\d+", wp_sup_str):
            wp.verification_required = True
            wp.verification_reason = "Waiting period cannot be negative."
            wp.confidence = "low"
            warnings.append("Waiting period contains a negative value; manual verification required.")
        else:
            # Check for range / conflicting numbers (e.g., "10-15 days" or "10 to 15 days")
            range_match = re.search(r"(\d+)\s*(?:-|to|से|या|or)\s*(\d+)\s*(?:days?|दिन)?", wp_sup_str, re.IGNORECASE)
            if range_match:
                n1, n2 = int(range_match.group(1)), int(range_match.group(2))
                if n1 != n2:
                    wp.verification_required = True
                    wp.verification_reason = f"Waiting period has range/conflicting numbers: {n1} to {n2} days."
                    wp.confidence = "medium"
                    warnings.append(f"Waiting period contains a range ({n1}-{n2} days); manual verification required.")

            nums = re.findall(r"\d+", wp_val_str)
            if not nums and wp_sup_str:
                nums = re.findall(r"\d+", wp_sup_str)

            if not nums:
                wp.verification_required = True
                wp.verification_reason = "No valid numeric waiting period found."
                wp.confidence = "low"
                warnings.append("Waiting period does not contain a clear number; manual verification required.")
            else:
                num = int(nums[0])
                if num < 0:
                    wp.verification_required = True
                    wp.confidence = "low"
                else:
                    wp.value = f"{num} days"
                    wp.text = f"{num} days"
                    wp.found = True

    # 2. Validate Registered Crops against actual printed label text
    crops_field = fields.get("registered_crops") or fields.get("crops_listed")
    if crops_field and crops_field.value is not None:
        raw_crops = crops_field.value
        if isinstance(raw_crops, list):
            crop_tokens = [str(c).strip() for c in raw_crops if str(c).strip()]
        else:
            crop_tokens = [c.strip() for c in re.split(r"[,;]|\b(?:and|और)\b", str(raw_crops)) if c.strip()]

        sup_corpus = (str(crops_field.supporting_text or "") + " " + full_text_corpus).lower()
        verified_crops = []
        unverified_crops = []

        for crop in crop_tokens:
            c_clean = crop.lower()
            if c_clean in sup_corpus or (len(c_clean) >= 4 and c_clean[:4] in sup_corpus):
                verified_crops.append(crop)
            else:
                unverified_crops.append(crop)

        if unverified_crops:
            crops_field.verification_required = True
            crops_field.verification_reason = f"Extracted crop(s) {unverified_crops} not verified in printed label text."
            warnings.append(f"Crop(s) {', '.join(unverified_crops)} not found in printed text; flagged for verification.")

        if verified_crops:
            crops_field.value = ", ".join(verified_crops)
            crops_field.text = crops_field.value
            crops_field.found = True
        else:
            if unverified_crops:
                crops_field.confidence = "low"
                crops_field.value = ", ".join(unverified_crops)
                crops_field.text = crops_field.value
            else:
                crops_field.value = None
                crops_field.confidence = "unknown"
                crops_field.found = False
                crops_field.text = ""

    # 3. Validate Concentration preserving units
    conc = fields.get("concentration")
    if conc and conc.value is not None:
        conc_val = str(conc.value).strip()
        conc_sup = str(conc.supporting_text or "").strip()

        unit_pattern = r"(?:%|\b(?:w/w|w/v|v/v|ec|wp|sl|sc|g/l|gm/l|mg/l|ppm|gr|sp|fs|wg|cs|as|ol)\b)"
        has_units = bool(re.search(unit_pattern, conc_val, re.IGNORECASE))

        if not has_units and conc_sup:
            match = re.search(r"(\d+(?:\.\d+)?\s*(?:%|\b(?:w/w|w/v|v/v|ec|wp|sl|sc|g/l|ppm)\b))", conc_sup, re.IGNORECASE)
            if match:
                conc.value = match.group(1).strip()
                conc.text = conc.value
                has_units = True

        if not has_units:
            conc.verification_required = True
            conc.verification_reason = "Concentration is missing units; manual verification required."
            conc.confidence = "low"
            warnings.append("Concentration missing units (e.g. %, w/w); flagged for manual verification.")
        else:
            conc.text = str(conc.value)
            conc.found = True

    # 4. Check unreadable or conflicting fields
    for fname, f in fields.items():
        if f.confidence == "low" or f.verification_required:
            f.verification_required = True

    return fields


def _parse_and_validate(raw_text: str, image_quality: str = "clear", is_readable: bool = True) -> Label:
    cleaned = _strip_markdown_code_fences(raw_text)
    data = json.loads(cleaned)

    field_keys = [
        "product_name",
        "active_ingredient",
        "concentration",
        "formulation",
        "registered_crops",
        "waiting_period",
        "dose",
        "warning_statements",
    ]

    warnings: list[str] = []

    # Check model-reported image quality
    reported_quality = str(data.get("image_quality", image_quality)).lower()
    reported_readable = bool(data.get("is_readable", is_readable))

    if reported_quality in ("blurry", "incomplete", "unreadable", "partial") or not reported_readable:
        warning_msg = "Image is blurry, incomplete, or unreadable. Manual verification recommended."
        if warning_msg not in warnings:
            warnings.append(warning_msg)

    # Build corpus of all supporting text to check crops against printed text
    supporting_corpus_parts = []
    for k in field_keys:
        val = data.get(k)
        if isinstance(val, dict):
            sup = val.get("supporting_text") or val.get("text")
            if sup:
                supporting_corpus_parts.append(str(sup))
    full_supporting_corpus = " ".join(supporting_corpus_parts)

    extracted_fields: dict[str, ExtractedField] = {}
    for k in field_keys:
        extracted_fields[k] = _clean_and_normalize_field(data.get(k))

    # Support legacy crops_listed if present in input
    if "crops_listed" in data and extracted_fields["registered_crops"].value is None:
        extracted_fields["registered_crops"] = _clean_and_normalize_field(data.get("crops_listed"))

    # Apply strict validation
    validated_fields = _validate_extracted_values(extracted_fields, full_supporting_corpus, warnings)

    # Check if manual verification is needed across fields
    needs_manual = any(f.verification_required for f in validated_fields.values()) or (reported_quality != "clear")

    # Build Label instance
    label_kwargs = {
        "product_name": validated_fields["product_name"],
        "active_ingredient": validated_fields["active_ingredient"],
        "concentration": validated_fields["concentration"],
        "formulation": validated_fields["formulation"],
        "registered_crops": validated_fields["registered_crops"],
        "waiting_period": validated_fields["waiting_period"],
        "dose": validated_fields["dose"],
        "warning_statements": validated_fields["warning_statements"],
        "crops_listed": validated_fields["registered_crops"],
        "image_quality": reported_quality,
        "is_readable": reported_readable,
        "warnings": warnings,
        "needs_manual_verification": needs_manual,
    }

    # Support legacy protective_gear and first_aid
    if "protective_gear" in data:
        label_kwargs["protective_gear"] = _clean_and_normalize_field(data.get("protective_gear"))
    if "first_aid" in data:
        label_kwargs["first_aid"] = _clean_and_normalize_field(data.get("first_aid"))

    if hasattr(Label, "model_validate"):
        return Label.model_validate(label_kwargs)
    return Label(**label_kwargs)


def _call_ollama_chat(
    messages: list[dict],
    model: str | None = None,
    base_url: str | None = None,
    timeout: int = 120,
    temperature: float = 0.0,
    seed: int = 42,
) -> str:
    """
    Send a chat request to the local/remote Ollama HTTP API.
    Temperature is strictly set to 0.0 for consistent, deterministic outputs.
    """
    target_model = model or os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)
    target_base_url = (base_url or os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL)).rstrip("/")

    payload = {
        "model": target_model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "seed": seed,
        },
    }

    try:
        response = requests.post(
            f"{target_base_url}/api/chat",
            json=payload,
            timeout=timeout,
        )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Ollama server is not running or unreachable at {target_base_url}. "
            "Please ensure Ollama is installed and running (e.g., run 'ollama serve')."
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(
            f"Ollama request to {target_base_url} timed out after {timeout} seconds."
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to communicate with Ollama: {e}")

    if response.status_code == 404:
        raise OllamaModelNotFoundError(
            f"Requested Ollama model '{target_model}' was not found. "
            f"Please run: 'ollama pull {target_model}' to download it."
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Ollama returned HTTP error {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
    except Exception as e:
        raise RuntimeError(f"Invalid JSON response from Ollama: {e}")

    content = data.get("message", {}).get("content", "")
    if not content and "response" in data:
        content = data["response"]

    if not content:
        raise RuntimeError("Ollama returned an empty response.")

    return content


def extract_label(image_path: str, mime_type: str = "image/jpeg") -> Label:
    """
    Uploads the pesticide label image to Ollama vision model,
    extracts structured fields using temperature=0,
    validates with strict Label schema, and retries once if parsing/validation fails.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Check for image blur or low resolution before sending
    img_quality, is_readable, pre_warnings = detect_image_issues(image_path)

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTION,
        },
        {
            "role": "user",
            "content": PROMPT,
            "images": [image_b64],
        },
    ]

    last_error = None
    for attempt in range(2):
        try:
            raw_text = _call_ollama_chat(messages=messages, temperature=0.0)
            label = _parse_and_validate(raw_text, image_quality=img_quality, is_readable=is_readable)
            for w in pre_warnings:
                if w not in label.warnings:
                    label.warnings.append(w)
            return label
        except (ConnectionError, TimeoutError, OllamaModelNotFoundError):
            raise
        except Exception as e:
            last_error = e

    raise ValueError(f"Failed to extract and validate label from image: {last_error}")


def generate_explanation(
    label: Label | dict,
    crop: str = "",
    spray_date: str = "",
    safety: dict | None = None,
    warnings: list[str] | None = None,
) -> dict:
    """
    Second AI call: generates farmer-friendly explanations in Hindi and English
    based STRICTLY on the ALREADY VALIDATED extraction data and authoritative safety calculations.
    Does NOT interpret the image again. Temperature is 0.0.
    """
    label_dict = (
        label.model_dump()
        if hasattr(label, "model_dump")
        else label.dict()
        if hasattr(label, "dict")
        else label
    )

    safety_context = ""
    if safety:
        crop_chk = safety.get("crop_check", {})
        harvest_chk = safety.get("safe_harvest", {})
        tox_chk = safety.get("toxicity", {})

        safety_context = (
            f"\nAuthoritative Safety Checks:\n"
            f"- Toxicity: {tox_chk.get('colour', 'Unknown')} ({tox_chk.get('meaning_en', 'Unknown')})\n"
            f"- Crop check result: {crop_chk.get('result', 'unclear')} ({crop_chk.get('reason', '')})\n"
            f"- Safe harvest date: {harvest_chk.get('date', 'Not calculated')} (Waiting days: {harvest_chk.get('days', 'Unknown')})\n"
        )

    warnings_context = ""
    if warnings:
        warnings_context = "\nWarnings:\n" + "\n".join(f"- {w}" for w in warnings)

    explanation_prompt = (
        f"Validated Pesticide Label Data:\n"
        f"- Product Name: {label_dict.get('product_name', {}).get('value') or 'Not specified'}\n"
        f"- Active Ingredient: {label_dict.get('active_ingredient', {}).get('value') or 'Not specified'}\n"
        f"- Concentration: {label_dict.get('concentration', {}).get('value') or 'Not specified'}\n"
        f"- Formulation: {label_dict.get('formulation', {}).get('value') or 'Not specified'}\n"
        f"- Registered Crops: {label_dict.get('registered_crops', {}).get('value') or 'Not specified'}\n"
        f"- Waiting Period: {label_dict.get('waiting_period', {}).get('value') or 'Not specified'}\n"
        f"- Dose: {label_dict.get('dose', {}).get('value') or 'Not specified on label'}\n"
        f"- Warning Statements: {label_dict.get('warning_statements', {}).get('value') or 'Standard agricultural precautions'}\n"
        f"Target Crop: {crop or 'Not specified'}\n"
        f"Spray Date: {spray_date or 'Not specified'}\n"
        f"{safety_context}"
        f"{warnings_context}\n\n"
        "Instructions:\n"
        "Explain these validated facts simply and clearly in English and Hindi for a farmer.\n"
        "Do NOT invent dosages, crops, or harvest dates. If dose is not specified, state that the farmer must consult an officer.\n"
        "Return valid JSON with keys 'english' and 'hindi' only."
    )

    messages = [
        {
            "role": "system",
            "content": EXPLANATION_SYSTEM_INSTRUCTION,
        },
        {
            "role": "user",
            "content": explanation_prompt,
        },
    ]

    try:
        raw_text = _call_ollama_chat(messages=messages, temperature=0.0)
        cleaned = _strip_markdown_code_fences(raw_text)
        data = json.loads(cleaned)
        return {
            "english": data.get("english", ""),
            "hindi": data.get("hindi", ""),
        }
    except Exception:
        # Fallback explanation constructed safely from validated data without guessing
        prod = label_dict.get("product_name", {}).get("value") or "Pesticide"
        wait = label_dict.get("waiting_period", {}).get("value") or "Check label"
        return {
            "english": f"{prod}: Follow safety precautions. Waiting period: {wait}. Always wear gloves and mask.",
            "hindi": f"{prod}: सुरक्षा नियमों का पालन करें। प्रतीक्षा अवधि: {wait}। हमेशा दस्ताने और मास्क पहनें।",
        }
