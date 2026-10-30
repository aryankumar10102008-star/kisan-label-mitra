import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import yaml


class TrustResult(dict):
    """Dictionary subclass supporting attribute-style access."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


def _get_data_dir() -> Path:
    current_file = Path(__file__).resolve()
    candidate = current_file.parent.parent / "data"
    if candidate.exists():
        return candidate
    return Path("data")


def _load_yaml(filename: str) -> dict:
    data_dir = _get_data_dir()
    filepath = data_dir / filename
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def lookup_toxicity(colour_text: str | None) -> TrustResult:
    """
    Normalise colour_text, map it to red/yellow/blue/green using toxicity_classes.yaml,
    and return colour, meaning_hi, meaning_en, source, as_of, verify_note.
    If the colour is missing or unknown return colour=None and say so.
    """
    toxicity_data = _load_yaml("toxicity_classes.yaml")
    source = toxicity_data.get("source", "TODO - team must fill the official source")
    as_of = toxicity_data.get("as_of", "TODO")
    verify_note = toxicity_data.get("verify_note", "Please verify against the current official rules.")
    classes_map = toxicity_data.get("classes", toxicity_data)

    if not colour_text or not str(colour_text).strip():
        return TrustResult({
            "colour": None,
            "meaning_hi": None,
            "meaning_en": None,
            "source": source,
            "as_of": as_of,
            "verify_note": verify_note,
            "reason": "Colour is missing or not specified.",
        })

    text = str(colour_text).strip().lower()

    color_keywords = {
        "red": ["red", "लाल"],
        "yellow": ["yellow", "पीला"],
        "blue": ["blue", "नीला"],
        "green": ["green", "हरा"],
    }

    matched_colours = []
    for col, keywords in color_keywords.items():
        if any(kw in text for kw in keywords):
            matched_colours.append(col)

    if len(matched_colours) != 1:
        return TrustResult({
            "colour": None,
            "meaning_hi": None,
            "meaning_en": None,
            "source": source,
            "as_of": as_of,
            "verify_note": verify_note,
            "reason": f"Unknown or ambiguous colour: {colour_text!r}",
        })

    matched_color = matched_colours[0]
    color_info = classes_map.get(matched_color, {})

    return TrustResult({
        "colour": matched_color,
        "meaning_hi": color_info.get("meaning_hi"),
        "meaning_en": color_info.get("meaning_en"),
        "source": source,
        "as_of": as_of,
        "verify_note": verify_note,
        "reason": f"Recognised toxicity colour: {matched_color}",
    })


def compute_safe_harvest(
    spray_date: str,
    waiting_text: str | None,
    suggested_days: int | str | None = None,
) -> TrustResult:
    """
    Compute safe harvest date from spray_date (YYYY-MM-DD) and waiting_text.
    Only accept whole numbers followed by a days word (days, day, दिन).
    If suggested_days is given, it must be one of the numbers found in waiting_text.
    If not exactly one clear number or date is invalid, return date=None with a reason.
    Otherwise return spray_date + days as YYYY-MM-DD with a reason.
    """
    if not spray_date or not isinstance(spray_date, str):
        return TrustResult({
            "date": None,
            "days": None,
            "reason": "Invalid or missing spray_date. Expected format YYYY-MM-DD.",
        })

    try:
        parsed_date = datetime.strptime(spray_date.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return TrustResult({
            "date": None,
            "days": None,
            "reason": f"Invalid spray_date format: {spray_date!r}. Expected YYYY-MM-DD.",
        })

    if not waiting_text or not str(waiting_text).strip():
        return TrustResult({
            "date": None,
            "days": None,
            "reason": "Waiting period text is missing or empty.",
        })

    text = str(waiting_text)
    found_numbers: list[int] = []

    # Check ranges like "10 to 15 days" or "10-15 days" or "10 या 15 दिन"
    range_pattern = r"(?:^|[^\d])(\d+)\s*(?:-|to|से|या|or)\s*(\d+)\s*(?:days?|दिन)(?:$|[^\w])"
    for m in re.finditer(range_pattern, text, flags=re.IGNORECASE):
        num1, num2 = int(m.group(1)), int(m.group(2))
        if num1 not in found_numbers:
            found_numbers.append(num1)
        if num2 not in found_numbers:
            found_numbers.append(num2)

    # Check standalone numbers followed by days word
    single_pattern = r"(?:^|[^\d])(\d+)\s*(?:days?|दिन)(?:$|[^\w])"
    for m in re.finditer(single_pattern, text, flags=re.IGNORECASE):
        num = int(m.group(1))
        if num not in found_numbers:
            found_numbers.append(num)

    if suggested_days is not None:
        try:
            s_days = int(suggested_days)
        except (ValueError, TypeError):
            return TrustResult({
                "date": None,
                "days": None,
                "reason": f"Invalid suggested_days: {suggested_days!r}.",
            })

        if s_days not in found_numbers:
            return TrustResult({
                "date": None,
                "days": None,
                "reason": (
                    f"Suggested days ({s_days}) is not among the numbers found in the "
                    f"printed waiting period text ({found_numbers})."
                ),
            })
        chosen_days = s_days
    else:
        if len(found_numbers) == 0:
            return TrustResult({
                "date": None,
                "days": None,
                "reason": "No valid waiting period number followed by days/day/दिन found in text.",
            })
        if len(found_numbers) > 1:
            return TrustResult({
                "date": None,
                "days": None,
                "reason": f"Ambiguous waiting period: multiple numbers found ({found_numbers}).",
            })
        chosen_days = found_numbers[0]

    safe_harvest_date = parsed_date + timedelta(days=chosen_days)
    safe_date_str = safe_harvest_date.strftime("%Y-%m-%d")

    return TrustResult({
        "date": safe_date_str,
        "days": chosen_days,
        "reason": f"Safe harvest date calculated by adding {chosen_days} day(s) to spray date {spray_date}.",
    })


def _load_crop_synonyms() -> dict[str, str]:
    raw_data = _load_yaml("crop_synonyms.yaml")
    mapping = {}
    if isinstance(raw_data, dict):
        for k, v in raw_data.items():
            if isinstance(v, str):
                mapping[str(k).strip().lower()] = v.strip().lower()
            elif isinstance(v, list):
                canonical = str(k).strip().lower()
                mapping[canonical] = canonical
                for syn in v:
                    mapping[str(syn).strip().lower()] = canonical
            elif isinstance(v, dict):
                canonical = str(v.get("canonical", k)).strip().lower()
                mapping[str(k).strip().lower()] = canonical
                for syn in v.get("synonyms", []):
                    mapping[str(syn).strip().lower()] = canonical
    return mapping


def check_crop(crop: str | None, crops_listed_text: str | None) -> TrustResult:
    """
    Normalise case and spacing, split the printed list on commas, semicolons, "and", "और",
    and use crop_synonyms.yaml.
    Return result "listed", "not_listed" or "unclear" plus the crop.
    Empty or missing list text = "unclear".
    A partial or ambiguous match = "unclear".
    Only return "not_listed" when the printed list is clear and the crop clearly is not in it.
    """
    if not crop or not str(crop).strip():
        return TrustResult({
            "result": "unclear",
            "crop": crop,
            "reason": "Target crop is empty or missing.",
        })

    if not crops_listed_text or not str(crops_listed_text).strip():
        return TrustResult({
            "result": "unclear",
            "crop": crop,
            "reason": "Printed crops list is empty or missing.",
        })

    crop_clean = str(crop).strip().lower()
    crop_clean = re.sub(r"\s+", " ", crop_clean)

    synonyms = _load_crop_synonyms()
    canonical_target = synonyms.get(crop_clean, crop_clean)

    split_tokens = re.split(r"[,;]|\b(?:and|और)\b", str(crops_listed_text), flags=re.IGNORECASE)
    cleaned_items: list[str] = []
    for token in split_tokens:
        tok = re.sub(r"\s+", " ", token.strip().lower())
        if tok:
            cleaned_items.append(tok)

    if not cleaned_items:
        return TrustResult({
            "result": "unclear",
            "crop": crop,
            "reason": "No valid crop names found in printed crops text.",
        })

    has_exact_match = False
    has_partial_match = False

    for item in cleaned_items:
        canonical_item = synonyms.get(item, item)
        if canonical_item == canonical_target or item == crop_clean:
            has_exact_match = True
            break

        if (crop_clean in item or item in crop_clean) and len(crop_clean) >= 3:
            has_partial_match = True

    if has_exact_match:
        return TrustResult({
            "result": "listed",
            "crop": crop,
            "reason": f"Crop '{crop}' is listed on the label.",
        })

    if has_partial_match:
        return TrustResult({
            "result": "unclear",
            "crop": crop,
            "reason": f"Crop '{crop}' has a partial or ambiguous match in the printed list: {cleaned_items}.",
        })

    return TrustResult({
        "result": "not_listed",
        "crop": crop,
        "reason": f"Crop '{crop}' is not listed in label crops: {cleaned_items}.",
    })

