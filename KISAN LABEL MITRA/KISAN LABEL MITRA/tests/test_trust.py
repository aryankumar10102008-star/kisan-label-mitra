import pytest

try:
    from backend.trust import lookup_toxicity, compute_safe_harvest, check_crop
except ImportError:
    from trust import lookup_toxicity, compute_safe_harvest, check_crop


class TestLookupToxicity:
    def test_normal_cases(self):
        # red
        red = lookup_toxicity("red")
        assert red["colour"] == "red"
        assert red["meaning_en"] == "extremely toxic"
        assert red["meaning_hi"] == "अत्यधिक विषैला"
        assert "TODO" in red["source"]
        assert red["verify_note"] is not None

        # yellow
        yellow = lookup_toxicity("Yellow Triangle")
        assert yellow["colour"] == "yellow"
        assert yellow["meaning_en"] == "highly toxic"
        assert yellow["meaning_hi"] == "अधिक विषैला"

        # blue
        blue = lookup_toxicity("blue")
        assert blue["colour"] == "blue"
        assert blue["meaning_en"] == "moderately toxic"
        assert blue["meaning_hi"] == "मध्यम विषैला"

        # green
        green = lookup_toxicity("green band")
        assert green["colour"] == "green"
        assert green["meaning_en"] == "slightly toxic"
        assert green["meaning_hi"] == "कम विषैला"

    def test_hindi_colour_name(self):
        red_hi = lookup_toxicity("लाल")
        assert red_hi["colour"] == "red"

        yellow_hi = lookup_toxicity("पीला")
        assert yellow_hi["colour"] == "yellow"

        blue_hi = lookup_toxicity("नीला")
        assert blue_hi["colour"] == "blue"

        green_hi = lookup_toxicity("हरा")
        assert green_hi["colour"] == "green"

    def test_missing_field_and_unknown(self):
        missing_none = lookup_toxicity(None)
        assert missing_none["colour"] is None
        assert "missing" in missing_none["reason"].lower()

        missing_empty = lookup_toxicity("")
        assert missing_empty["colour"] is None
        assert "missing" in missing_empty["reason"].lower()

        unknown = lookup_toxicity("purple")
        assert unknown["colour"] is None
        assert "unknown" in unknown["reason"].lower() or "ambiguous" in unknown["reason"].lower()


class TestComputeSafeHarvest:
    def test_normal_cases(self):
        res = compute_safe_harvest("2026-10-30", "Waiting period: 14 days")
        assert res["date"] == "2026-11-13"
        assert res["days"] == 14
        assert "14" in res["reason"]

        res_single = compute_safe_harvest("2026-10-30", "1 day before harvest")
        assert res_single["date"] == "2026-10-31"
        assert res_single["days"] == 1

    def test_hindi_days(self):
        res = compute_safe_harvest("2026-10-30", "फसल कटाई से 10 दिन पहले")
        assert res["date"] == "2026-11-09"
        assert res["days"] == 10

    def test_suggested_days_valid(self):
        res = compute_safe_harvest("2026-10-30", "14 days waiting period", suggested_days=14)
        assert res["date"] == "2026-11-13"
        assert res["days"] == 14

    def test_number_not_in_printed_text(self):
        res = compute_safe_harvest("2026-10-30", "Wait 14 days", suggested_days=21)
        assert res["date"] is None
        assert "not among" in res["reason"].lower() or "not in" in res["reason"].lower()

    def test_invalid_date(self):
        res_invalid_format = compute_safe_harvest("30-10-2026", "14 days")
        assert res_invalid_format["date"] is None
        assert "invalid" in res_invalid_format["reason"].lower()

        res_invalid_date = compute_safe_harvest("2026-02-31", "14 days")
        assert res_invalid_date["date"] is None
        assert "invalid" in res_invalid_date["reason"].lower()

    def test_waiting_period_with_no_number(self):
        res = compute_safe_harvest("2026-10-30", "Harvest when crops are mature")
        assert res["date"] is None
        assert "no valid waiting period" in res["reason"].lower() or "not found" in res["reason"].lower()

        res_empty = compute_safe_harvest("2026-10-30", "")
        assert res_empty["date"] is None
        assert "missing" in res_empty["reason"].lower()

    def test_number_not_followed_by_days(self):
        res = compute_safe_harvest("2026-10-30", "Mix 500 ml in 200 liters of water")
        assert res["date"] is None
        assert "no valid waiting period" in res["reason"].lower() or "not found" in res["reason"].lower()


class TestCheckCrop:
    def test_normal_cases(self):
        res_listed = check_crop("cotton", "Wheat, Cotton, Paddy")
        assert res_listed["result"] == "listed"
        assert res_listed["crop"] == "cotton"

        res_not_listed = check_crop("mustard", "Wheat, Cotton, Paddy")
        assert res_not_listed["result"] == "not_listed"
        assert res_not_listed["crop"] == "mustard"

    def test_hindi_crop_name(self):
        res_hindi_input = check_crop("कपास", "Wheat, Cotton, Paddy")
        assert res_hindi_input["result"] == "listed"
        assert res_hindi_input["crop"] == "कपास"

        res_hindi_printed = check_crop("cotton", "गेहूं, कपास, धान")
        assert res_hindi_printed["result"] == "listed"

        res_paddy_dhan = check_crop("धान", "Rice, Wheat")
        assert res_paddy_dhan["result"] == "listed"

    def test_crop_synonyms(self):
        res_paddy = check_crop("paddy", "Rice, Wheat")
        assert res_paddy["result"] == "listed"

        res_corn = check_crop("corn", "Maize, Sugarcane")
        assert res_corn["result"] == "listed"

    def test_partial_match(self):
        res_partial = check_crop("cotton", "cottonseed, wheat")
        assert res_partial["result"] == "unclear"
        assert "partial" in res_partial["reason"].lower() or "ambiguous" in res_partial["reason"].lower()

    def test_missing_fields(self):
        res_empty_text = check_crop("cotton", "")
        assert res_empty_text["result"] == "unclear"

        res_none_text = check_crop("cotton", None)
        assert res_none_text["result"] == "unclear"

        res_empty_crop = check_crop("", "Wheat, Cotton")
        assert res_empty_crop["result"] == "unclear"

    def test_delimiters(self):
        printed = "Wheat; Cotton and Paddy और Tomato"
        assert check_crop("wheat", printed)["result"] == "listed"
        assert check_crop("cotton", printed)["result"] == "listed"
        assert check_crop("rice", printed)["result"] == "listed"
        assert check_crop("tomato", printed)["result"] == "listed"
        assert check_crop("potato", printed)["result"] == "not_listed"

