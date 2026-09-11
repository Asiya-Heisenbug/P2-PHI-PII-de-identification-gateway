"""
Baseline 2: Microsoft Presidio (spaCy-backed NER + recognizers).

Setup:
    pip install presidio-analyzer presidio-anonymizer spacy
    python -m spacy download en_core_web_lg

Presidio ships recognizers for PERSON, DATE_TIME, PHONE_NUMBER, EMAIL_ADDRESS,
LOCATION, US_SSN, IP_ADDRESS, URL out of the box. It does NOT know about
MRNs or hospital-billing account numbers, which is a useful gap to point out
in your evaluation write-up (domain-specific identifiers need custom recognizers
or a fine-tuned model — exactly the case your project makes).
"""

from presidio_analyzer import AnalyzerEngine

# Map Presidio's entity names -> our label scheme, for apples-to-apples scoring
LABEL_MAP = {
    "PERSON": "NAME",
    "DATE_TIME": "DATE",
    "PHONE_NUMBER": "PHONE",
    "EMAIL_ADDRESS": "EMAIL",
    "LOCATION": "LOCATION",
    "US_SSN": "SSN",
    "IP_ADDRESS": "IP",
    "URL": "URL",
}

_analyzer = None


def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
    return _analyzer


def detect(text):
    analyzer = get_analyzer()
    results = analyzer.analyze(text=text, language="en")
    spans = []
    for r in results:
        label = LABEL_MAP.get(r.entity_type)
        if label:
            spans.append((r.start, r.end, label))
    return sorted(spans)


if __name__ == "__main__":
    sample = "Patient John Smith, DOB 12/05/1985, phone 9876543210, MRN12345."
    for s in detect(sample):
        print(s, sample[s[0]:s[1]])
