"""
Baseline 1: pure regex PHI/PII detector. No ML at all.
Deliberately naive — this is meant to be beaten by your fine-tuned model,
and the gap is part of your evaluation story.
"""

import re

PATTERNS = {
    "DATE": r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    "PHONE": r"\b\d{10}\b",
    "EMAIL": r"[\w.\-]+@[\w.\-]+\.\w+",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "MRN": r"\bMRN\d{5,8}\b",
    "ACCOUNT_NUM": r"\bACC\d{6,10}\b",
    "URL": r"https?://\S+",
    "IP": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}


def detect(text):
    """Returns list of (start, end, label). Cannot detect NAME or LOCATION —
    that's the point: regex has no notion of context."""
    spans = []
    for label, pattern in PATTERNS.items():
        for m in re.finditer(pattern, text):
            spans.append((m.start(), m.end(), label))
    return sorted(spans)


if __name__ == "__main__":
    sample = "Patient John Smith, DOB 12/05/1985, phone 9876543210, MRN12345."
    for s in detect(sample):
        print(s, sample[s[0]:s[1]])
