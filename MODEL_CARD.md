# Model Card —  PHI/PII Detector

- **Base model:** distilbert-base-uncased (66M params)
- **Task:** Token classification (BIO tagging) for PHI/PII entities
- **Labels:** NAME, DATE, PHONE, EMAIL, LOCATION, MRN, SSN, URL, IP, ACCOUNT_NUM
- **Training data:** Synthetic clinical notes generated via
  `src/generate_synthetic_data.py` (Faker-based), no real patient data used.
- **Intended use:** Pre-processing gateway to strip identifiers from
  clinical text before sending to a third-party LLM. Not a certified
  HIPAA de-identification tool — recall numbers below should inform
  whether it's fit for a given real-world use, not assumed sufficient.
- **Known limitations:**
  - Standalone first-name references (without surname) may be missed —
    see FAILURES.md.
  - Ambiguous surnames used as eponymous disease names (e.g. "Dr.
    Parkinson" vs "Parkinson's disease") are a documented hard case;
    see adversarial test results.
  - Does not handle images, audio, or biometric identifiers — text only.
- **Evaluation:** see `evaluation/results.csv` — precision, recall, F1,
  and leak rate against regex and Presidio baselines, plus an
  adversarial-only slice.
- **Training details:** six epochs, learning rate `5e-5`, batch size `8`,
  weight decay `0.01`; the best checkpoint was selected by validation recall.
  (epochs, learning rate, final metrics).
