import json
import logging
import re
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification


BASE_DIR = Path(__file__).resolve().parent.parent
ADAPTER_DIR = BASE_DIR / "model" / "final_model"
LABEL_LIST_FILE = ADAPTER_DIR / "label_list.json"
MODEL_WEIGHTS = (
    ADAPTER_DIR / "model.safetensors",
    ADAPTER_DIR / "pytorch_model.bin",
)

LOGGER = logging.getLogger(__name__)

REGEX_PATTERNS = {
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "URL": r"\bhttps?://[^\s]+",
    "IP": r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b",
    "DATE_TIME": r"\b(?:0?[1-9]|[12]\d|3[01])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\s+\d{1,2}:\d{2}\b",
    "DATE": r"\b(?:0?[1-9]|[12]\d|3[01])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b",
    "AGE": r"\b(?:age\s*[:=]?\s*|\(|\b)(?:[1-9]\d?)(?:\s*-?\s*years?\s*-?\s*old)?(?=\)|\s*(?:years?\s*old|yo\b))",
    "OTHER_ID": r"\b[A-Z]{2,}[A-Z0-9]*-\d{4}-\d{3,}\b",
    "ZIP": r"\b(?:ZIP(?:\s*code)?|postal(?:\s*code)?)\s*[:#-]?\s*\d{5}(?:-\d{4})?\b|\b\d{5}(?:-\d{4})?\b",
    "AGE_OVER_89": r"\b(?:age\s*[:=]?\s*|aged\s+|(?:pt|patient)\s+(?:is|aged?)\s+)?(?:9\d|[1-9]\d{2,})(?:\s*-?\s*years?\s*-?\s*old|\s+y/?o\b|\s*[MF]\b)\b|\bage\s*[:=]?\s*(?:9\d|[1-9]\d{2,})\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "PHONE": r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b",
    "FAX": r"\b(?:Fax\s*)?(?:0\d{2,4}[-\s]?)?\d{6,8}\b",
    "MRN": r"\b(?:MRN[\s:#-]*)?[A-Z]{0,3}\d{5,10}\b",
    "ACCOUNT_NUM": r"\b(?:ACC|ACCOUNT)[-_]?\d{5,12}\b",
    "HEALTH_PLAN": r"\b(?:HP|PLAN|MEMBER)[-_]?\d{5,12}\b",
    "LICENSE": r"\b(?:LIC|LICENSE)[-_]?\d{5,12}\b",
    "VEHICLE": r"\b[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{3,4}\b",
    "DEVICE": r"\b(?:DEV|DEVICE|SERIAL)[-_]?\d{5,15}\b",
    "BIOMETRIC": r"\b(?:fingerprint|retina|iris|voiceprint|face\s*id)\b",
    "UNIQUE_ID": r"\b(?:UID|ID)[-_]?[A-Z0-9]{5,15}\b",
}

_MODEL = None
_TOKENIZER = None
_LABEL_LIST = None


def _load_model():
    global _MODEL, _TOKENIZER, _LABEL_LIST

    if _MODEL is not None:
        return

    if not (ADAPTER_DIR / "config.json").exists():
        LOGGER.warning("NER model configuration is missing: %s", ADAPTER_DIR)
        return

    if not any(path.exists() for path in MODEL_WEIGHTS):
        LOGGER.warning("NER model weights are missing: %s", ADAPTER_DIR)
        return

    try:
        _TOKENIZER = AutoTokenizer.from_pretrained(str(ADAPTER_DIR))
        _MODEL = AutoModelForTokenClassification.from_pretrained(str(ADAPTER_DIR))

        if LABEL_LIST_FILE.exists():
            with open(LABEL_LIST_FILE, "r", encoding="utf-8") as f:
                _LABEL_LIST = json.load(f)

        _MODEL.eval()
    except Exception:
        LOGGER.exception("Failed to load NER model from %s", ADAPTER_DIR)
        _MODEL = None
        _TOKENIZER = None
        _LABEL_LIST = None


def _fine_tuned_detect(text):
    _load_model()

    if _MODEL is None or _TOKENIZER is None:
        return []

    encoding = _TOKENIZER(
        text,
        return_tensors="pt",
        return_offsets_mapping=True,
        truncation=True,
        max_length=512,
    )

    offset_mapping = encoding.pop("offset_mapping")[0].tolist()

    with torch.no_grad():
        outputs = _MODEL(**encoding)

    predictions = torch.argmax(outputs.logits, dim=-1)[0].tolist()

    results = []

    current_start = None
    current_end = None
    current_label = None

    for prediction, (start, end) in zip(predictions, offset_mapping):
        if start == end:
            continue

        if _LABEL_LIST and prediction < len(_LABEL_LIST):
            label = _LABEL_LIST[prediction]
        else:
            label = "O"

        if label.startswith("B-"):
            if current_label is not None:
                results.append(
                    (current_start, current_end, current_label)
                )

            current_start = start
            current_end = end
            current_label = label[2:]

        elif label.startswith("I-") and current_label == label[2:]:
            current_end = end

        else:
            if current_label is not None:
                results.append(
                    (current_start, current_end, current_label)
                )

            current_start = None
            current_end = None
            current_label = None

    if current_label is not None:
        results.append(
            (current_start, current_end, current_label)
        )

    normalized = []
    for start, end, label in results:
        value = text[start:end]
        value = value.strip(" \t\r\n.,:;()[]{}")
        if not value:
            continue

        start = text.find(value, start, end)
        end = start + len(value)

        if label == "EMAIL" and "@" not in value:
            continue

        if label == "DATE" and not re.search(r"\d[-/]\d", value):
            continue

        if label == "LOCATION" and not re.search(
            r"(?:Receiving Facility|Route\s+\d+)",
            text[max(0, start - 80):min(len(text), end + 80)],
            flags=re.IGNORECASE,
        ):
            continue

        normalized.append((start, end, label))

    return normalized


def _regex_detect(text):
    results = []

    for label, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            results.append(
                (
                    match.start(),
                    match.end(),
                    label,
                )
            )

    return results


def _contextual_detect(text):
    results = []

    patterns = (
        (r"\bRoute\s+\d+\b", "GEO"),
        (r"(?<=Receiving Facility )[^\n,]+?(?=,\s*ED\b)", "GEO"),
    )

    for pattern, label in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            results.append((match.start(), match.end(), label))

    return results


def _name_detect(text):
    results = []

    pattern = (
        r"\b(?:Patient|Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+"
        r"(?!Name\b)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    )

    for match in re.finditer(pattern, text):
        results.append(
            (
                match.start(1),
                match.end(1),
                "NAME",
            )
        )

    contextual_patterns = (
        r"\bPatient(?:\s+Name)?\s+"
        r"([A-Z][A-Za-z'-]+,\s*[A-Z][A-Za-z'-]+(?:\s+[A-Z]\.)?)",
        r"(?:\bCrew:\s*|/\s*)([A-Z]\.\s*[A-Z][a-z]+)",
    )

    for name_pattern in contextual_patterns:
        for match in re.finditer(name_pattern, text):
            for group in match.groups():
                if group:
                    start = match.start() + match.group(0).find(group)
                    results.append((start, start + len(group), "NAME"))

    return results


def _dob_detect(text):
    results = []
    pattern = (
        r"\b(?:DOB|Date\s+of\s+Birth)\s*[:=-]?\s*"
        r"((?:0?[1-9]|[12]\d|3[01])[-/](?:0?[1-9]|[12]\d|3[01])[-/]"
        r"(?:19|20)\d{2})\b"
    )

    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        results.append((match.start(1), match.end(1), "DATE"))

    return results


def _merge_detections(detections):
    detections.sort(
        key=lambda x: (
            x[0],
            -(x[1] - x[0]),
        )
    )

    selected = []

    for candidate in detections:
        start, end, label = candidate

        overlaps = False

        for existing in selected:
            existing_start, existing_end, _ = existing

            if (
                start < existing_end
                and end > existing_start
            ):
                overlaps = True
                break

        if not overlaps:
            selected.append(candidate)

    selected.sort(key=lambda x: x[0])

    return selected


def detect(text):
    if not text or not text.strip():
        return []

    model_results = _fine_tuned_detect(text)
    regex_results = _regex_detect(text) + _contextual_detect(text)
    name_results = _name_detect(text)
    dob_results = _dob_detect(text)

    rule_results = _merge_detections(
        regex_results + name_results + dob_results
    )
    model_results = [
        candidate for candidate in model_results
        if not any(
            candidate[0] < existing[1]
            and candidate[1] > existing[0]
            for existing in rule_results
        )
    ]

    return _merge_detections(rule_results + model_results)


def mode():
    if (
        (ADAPTER_DIR / "config.json").exists()
        and any(path.exists() for path in MODEL_WEIGHTS)
    ):
        return "fine_tuned"

    return "fallback"