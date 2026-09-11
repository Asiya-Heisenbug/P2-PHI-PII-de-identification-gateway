# Failures & Dead Ends

## 2026-09-04 — Initial project direction

**What I tried:**
Started designing the PHI/PII de-identification gateway according to the internship specification, with ML-based detection, masking, rehydration, and evaluation against Regex and Presidio.

**Why it failed:**
The project requirements were broader than a simple NER model and included document handling, adversarial testing, metrics, baselines, and an end-to-end LLM gateway.

**What I did instead:**
Broke the project into separate detection, transformation, mapping, rehydration, LLM, and evaluation components.

**Lesson:**
An end-to-end privacy gateway requires more than just a PHI detection model.

---

## 2026-09-05 — Pretrained model approach

**What I tried:**
Tried to use a pretrained Hugging Face transformer for PHI/PII token classification.

**Why it failed:**
The environment could not reliably access Hugging Face to download the required pretrained model/tokenizer.

**What I did instead:**
Moved toward a locally constructed transformer-based model and synthetic training data.

**Lesson:**
Model availability and environment restrictions must be considered before committing to a training approach.

---

## 2026-09-06 — Training from scratch

**What I tried:**
Trained a local DeBERTa-style token classification model using synthetic PHI/PII data.

**Why it failed:**
The model was randomly initialized and CPU training was extremely slow. Training steps could take around 96 seconds, making full experimentation impractical.

**What I did instead:**
Added smaller training runs, checkpointing, resume support, sample limits, and reduced training budgets.

**Lesson:**
Training a transformer from scratch on CPU is expensive and does not provide the advantages of pretrained language representations.

---

## 2026-09-07 — Synthetic data and class imbalance

**What I tried:**
Used Faker-generated synthetic clinical examples to train the PHI/PII NER model.

**Why it failed:**
The dataset was highly imbalanced because most tokens were `O` rather than PHI. Synthetic examples also did not fully represent realistic clinical documents.

**What I did instead:**
Added class-weighted loss and kept a separate held-out clinical document for final testing.

**Lesson:**
Synthetic data is useful for controlled experiments but may not represent real clinical-document complexity.

---

## 2026-09-08 — Model produced fragmented predictions

**What I tried:**
Ran the trained detector through the masking pipeline on the provided clinical document.

**Why it failed:**
The model produced incorrect fragmented spans, causing surrogate placeholders to appear inside ordinary words.

**What I did instead:**
Inspected the label mapping, span resolver, pseudonymizer, and transformation pipeline. The label mapping and downstream logic were largely correct, so the main issue was traced to poor model predictions.

**Lesson:**
A de-identification pipeline cannot compensate for fundamentally incorrect NER spans.

---

## 2026-09-09 — Clinical PDF contains tables and structured layouts

**What I tried:**
Considered processing the internship-provided clinical PDF directly with the text-based NER model.

**Why it failed:**
The document contains tables, headings, key-value fields, vital signs, medication tables, and narrative sections. A text NER model does not inherently understand visual table layout.

**What I did instead:**
Separated document extraction/layout normalization from PHI detection. Tables can be converted into structured text such as `Patient: ...`, `MRN: ...`, and `Arrival: ...` before NER processing.

**Lesson:**
PDF/table extraction and PHI detection should be separate stages.

---

## 2026-09-09 — Date replacement looked like a detection error

**What I tried:**
Compared dates in the original document with dates in the masked output.

**Why it appeared to fail:**
Dates were changed during transformation.

**What I did instead:**
Confirmed that DATE entities are intentionally passed through the date-shifting component.

**Lesson:**
De-identification can intentionally modify dates while preserving useful temporal relationships.

---

## 2026-09-10 — Training configuration/import problems

**What I tried:**
Started the training pipeline using `configs/train.yaml`.

**Why it failed:**
The configuration file contained training-script content instead of the expected YAML configuration. After correcting this, running the script directly produced a Python package import error.

**What I did instead:**
Created the proper YAML configuration and ran the training script as a module using:

`python -m model.train --config configs/train.yaml`

**Lesson:**
Project structure, configuration files, and Python package execution need to be kept separate and consistent.

---

## 2026-09-10 — Pivot to a simpler working architecture

**What I tried:**
Continued attempting to make the custom transformer-based pipeline reliable enough for the final demonstration.

**Why it failed:**
Limited CPU training, unavailable pretrained weights, synthetic-data limitations, and poor generalization made the custom model unreliable under the available time constraints.

**What I did instead:**
Built the final PHI SHIELD architecture around a practical privacy gateway:

- Streamlit interface
- PHI/PII detection
- Regex/name fallback
- Local mapping store
- Placeholder-based masking
- Ollama local LLM
- Llama 3.2 for response generation
- Local rehydration
- Regex and Microsoft Presidio comparison baselines

**Lesson:**
A smaller reliable end-to-end system was more useful for the final demonstration than an unreliable model trained from scratch.

---

## 2026-09-11 — Trained model weights not loaded in final evaluation

**What I tried:**
Evaluated the final application expecting the trained transformer detector to be used.

**Why it failed:**
The stored evaluation results showed fallback mode rather than the trained model. The trained `model.safetensors` checkpoint was not being loaded correctly.

**What I did instead:**
Used the available fallback detector for the working demonstration and documented that the evaluation results represent fallback mode rather than successful deployment of the trained model.

**Lesson:**
A model being trained successfully and a model being correctly loaded into the production inference pipeline are two separate engineering steps.

---

## 2026-09-11 — Final PHI SHIELD implementation

**What I tried:**
Completed the end-to-end privacy gateway despite the model limitations.

**Result:**
PHI SHIELD accepts clinical text, detects sensitive information, replaces it with placeholders, stores the mapping locally, sends only masked text to the local Ollama/Llama 3.2 model, and rehydrates the response locally.

**Known limitation:**
The current evaluation results are based on synthetic test data and fallback detection. They should not be interpreted as proof of complete PHI protection on real clinical documents.

**Lesson:**
The final system demonstrates the complete privacy-gateway architecture while clearly documenting the limitations of the current ML detector.

---