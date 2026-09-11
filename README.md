# PHI SHIELD — PHI/PII De-identification Gateway

PHI SHIELD is a privacy-preserving clinical AI gateway that protects sensitive patient information before it is processed by a Large Language Model (LLM).

The system:

1. Detects PHI/PII from clinical text.
2. Replaces detected identifiers with reversible placeholders.
3. Keeps the original identifiers in a local mapping.
4. Sends only the de-identified text to a locally running Ollama LLM.
5. Receives the AI response.
6. Replaces known placeholders with the original values locally.

```text
Raw Clinical Text
       ↓
PHI/PII Detection
       ↓
De-identification
       ↓
Protected Clinical Text
       ↓
Local Ollama LLM
       ↓
AI Response
       ↓
Rehydration
       ↓
Final Response
```

## Key Features

* Fine-tuned DistilBERT-based PHI/PII detector
* Clinical PHI/PII detection
* Reversible de-identification
* Local mapping of original identifiers
* Local LLM inference using Ollama
* No external AI API
* Secure rehydration of protected information
* Unknown placeholder detection
* Streamlit-based interface
* Regex and Presidio baseline comparison
* Synthetic clinical data for training and evaluation

---

# Privacy Architecture

PHI SHIELD creates a privacy boundary between patient information and the LLM.

```text
Original Clinical Text
        ↓
   PHI/PII Detector
        ↓
   De-identification
        ↓
 ┌──────────────────────┐
 │ Local Mapping Store  │
 │ Original values stay │
 │ inside the application│
 └──────────────────────┘
        ↓
 Protected Clinical Text
        ↓
 Ollama - llama3.2
        ↓
      AI Response
        ↓
    Rehydration
        ↓
    Final Response
```

### Privacy Boundary

Only de-identified clinical text is sent to the local LLM.

Original patient identifiers remain inside PHI SHIELD and are not sent to an external AI service.

### External API

```text
None
```

### Local LLM

```text
Ollama
Model: llama3.2:latest
```

---

# Requirements

Before running PHI SHIELD, the user needs:

* Python 3.10 or newer
* Ollama
* `llama3.2:latest`
* Git (optional)
* Windows 10/11, Linux, or macOS

The application runs the LLM locally through Ollama.

---

# Project Files

The main project files are:

```text
PHI-SHIELD/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── detector.py
│   ├── deidentifier.py
│   ├── rehydrator.py
│   ├── security.py
│   ├── llm.py
│   └── generate_synthetic_data.py
│
├── model/
│   ├── final_model/
│   │   ├── config.json
│   │   ├── label_list.json
│   │   ├── tokenizer.json
│   │   ├── tokenizer_config.json
│   │   └── model.safetensors
│   │
│   └── training/
│       └── train.py
│
├── data/
├── baselines/
├── evaluation/
└── tests/
```

> **Important:** `model.safetensors` is provided separately through the GitHub Release because the file is excluded from the normal Git repository using `.gitignore`.

---

# Step 1 — Clone the Repository

Open PowerShell or a terminal and run:

```bash
git clone https://github.com/Asiya-Heisenbug/P2-PHI-PII-de-identification-gateway.git PHI-SHIELD
cd PHI-SHIELD
```

---

# Step 2 — Download the Trained Model

The trained model weights are provided in the project's **GitHub Release v1.0**.

Open the **Releases** section of this repository and download:

```text
model.safetensors
```

Place the downloaded file here:

```text
model/final_model/model.safetensors
```

The final model directory should contain:

```text
model/final_model/
├── config.json
├── label_list.json
├── tokenizer.json
├── tokenizer_config.json
└── model.safetensors
```

The model weights are kept in the Release instead of the normal Git repository to avoid storing a large model file in Git history.

---

# Step 3 — Create a Virtual Environment

### Windows PowerShell

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

---

# Step 4 — Install Python Dependencies

Run:

```bash
pip install -r requirements.txt
```

---

# Step 5 — Install and Start Ollama

Install Ollama on the computer.

Then download the required LLM:

```bash
ollama pull llama3.2:latest
```

Check that the model is installed:

```bash
ollama list
```

The output should contain:

```text
llama3.2:latest
```

If Ollama is not already running, start it:

```bash
ollama serve
```

Keep Ollama running while using PHI SHIELD.

---

# Step 6 — Run PHI SHIELD

From the project root, run:

```bash
streamlit run app.py
```

Streamlit will provide a local address, normally:

```text
http://localhost:8501
```

Open that address in a browser.

---

# How the Application Works

When a user enters clinical text:

### 1. PHI/PII Detection

The fine-tuned DistilBERT model identifies sensitive information.

Example:

```text
Patient John Anderson, DOB 14/06/1978,
phone 9876543210.
```

### 2. De-identification

Sensitive information is replaced with placeholders:

```text
Patient NAME_001, DOB DATE_001,
phone PHONE_001.
```

### 3. Local Mapping

The original values are stored locally:

```text
NAME_001  → John Anderson
DATE_001  → 14/06/1978
PHONE_001 → 9876543210
```

This mapping is not sent to Ollama.

### 4. Local LLM Processing

Only the protected text is sent to:

```text
Ollama → llama3.2:latest
```

### 5. Rehydration

Known placeholders in the AI response are replaced locally with the original values.

Unknown placeholders are not silently replaced and are reported as a security signal.

---

# Example

### Original Input

```text
Patient John Anderson, date of birth 14/06/1978,
phone 9876543210, email john.anderson@example.com,
MRN MRN458921.

He has a blood sugar level of 180 mg/dL.
What could be the possible causes?
```

### Protected Text Sent to Ollama

```text
Patient NAME_001, date of birth DATE_001,
phone PHONE_001, email EMAIL_001,
MRN MRN_001.

He has a blood sugar level of 180 mg/dL.
What could be the possible causes?
```

The original identifiers are not included in the text sent to the LLM.

---

# PHI/PII Detection

PHI SHIELD uses a fine-tuned DistilBERT token-classification model.

Base model:

```text
distilbert-base-uncased
```

The detector is designed to identify sensitive information including:

* Names
* Dates
* Phone numbers
* Email addresses
* Medical record numbers
* Account numbers
* URLs
* IP addresses
* Social Security Numbers
* Health-plan identifiers
* License identifiers
* Device identifiers
* Vehicle identifiers
* Other unique identifiers

Rule-based protection is also used for structured identifiers where appropriate.

---

# De-identification

Detected identifiers are replaced with reversible placeholders.

Example:

```text
John Anderson
```

becomes:

```text
NAME_001
```

and:

```text
9876543210
```

becomes:

```text
PHONE_001
```

The original values are maintained in the local mapping store.

---

# Local LLM

PHI SHIELD uses Ollama for local LLM inference.

```text
LLM Platform: Ollama
Model: llama3.2:latest
External AI API: None
```

The LLM communication is implemented in:

```text
src/llm.py
```

No OpenAI or Anthropic API key is required.

---

# Evaluation

The detector was evaluated against:

1. Regex-based detection
2. Microsoft Presidio
3. PHI SHIELD detector

Results:

| System                              | Precision | Recall |    F1 | Leak Rate |
| ----------------------------------- | --------: | -----: | ----: | --------: |
| Regex                               |     1.000 |  0.798 | 0.887 |     0.202 |
| Presidio                            |     0.916 |  0.718 | 0.803 |     0.282 |
| PHI SHIELD (fine-tuned)                 |     0.964 |  0.917 | 0.939 |     0.083 |
| PHI SHIELD adversarial (fine-tuned)     |     0.928 |  0.928 | 0.928 |     0.072 |

The current synthetic evaluation produced a measured leak rate of:

```text
0.083
```

The current result is reported as `fine_tuned`. The trained weights are stored
in `model/final_model/model.safetensors`.

These results apply to the current synthetic evaluation dataset and should not be interpreted as a guarantee of zero PHI leakage on arbitrary real-world clinical text.

Evaluation results are stored in:

```text
evaluation/results.csv
```

Run the evaluation with:

```bash
python evaluation/evaluate.py --test data/test.json
```

---

# Training

Synthetic clinical data is used for development and evaluation.

Data generation:

```text
src/generate_synthetic_data.py
```

Training script:

```text
model/training/train.py
```

Training can be performed using:

```bash
python model/training/train.py --data_dir data --out_dir model/adapter
```

The resulting inference-ready model is placed in:

```text
model/final_model/
```

Training checkpoints are not required for normal application inference.

---

# Baselines

### Regex

Implementation:

```text
baselines/regex_baseline.py
```

Run:

```bash
python baselines/regex_baseline.py
```

### Presidio

Implementation:

```text
baselines/presidio_baseline.py
```

Run:

```bash
python baselines/presidio_baseline.py
```

---

# Security Considerations

PHI SHIELD is a privacy-preserving prototype.

The main security principles are:

* PHI/PII is detected before LLM processing.
* Detected identifiers are replaced before reaching the LLM.
* Original identifiers remain local.
* Placeholder mappings are not sent to the LLM.
* Ollama runs the LLM locally.
* No external AI API is required.
* Unknown placeholders are reported during rehydration.
* Synthetic data is used for development and evaluation.

For production use, additional controls would be required, including:

* Encryption at rest
* Authentication
* Access control
* Secure session management
* Audit logging
* Secure secrets management
* Key management
* Network isolation
* Production-grade storage
* Testing on representative clinical datasets

---

# Limitations

PHI SHIELD is a prototype and is not a certified medical or HIPAA-compliant production system.

The detector is evaluated using synthetic data and may perform differently on real-world clinical text.

Further testing with diverse and representative clinical datasets would be required before production deployment.

---

# Development Documentation

Development issues, debugging problems, and their resolutions are documented in:

```text
FAILURES.md
```

The project also includes:

```text
MODEL_CARD.md
```

which provides information about the trained model.

---

# Current Configuration

```text
PHI Detection: Active
De-identification: Active
Detector Mode: fine_tuned

Foundation LLM: Ollama
LLM Model: llama3.2:latest

External API: None

Privacy Boundary:
Only de-identified clinical text is passed to the local LLM.
Original identifiers remain inside PHI SHIELD.
```

---

# Project Goal

The goal of PHI SHIELD is to demonstrate how sensitive clinical information can be separated from the LLM processing layer while maintaining a useful clinical AI interaction.

The core workflow is:

```text
Detect → Protect → Process Locally → Rehydrate
```

PHI SHIELD demonstrates a privacy-first approach to using local foundation models with sensitive clinical text.

---

# Running the Project — Quick Version

After cloning the repository and downloading the model from **Release v1.0**:

```bash
cd PHI-SHIELD

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

ollama pull llama3.2:latest

streamlit run app.py
```

Then open the Streamlit URL shown in the terminal.

---

# Release

The trained model weights are provided separately in:

**PHI SHIELD v1.0**

Download:

```text
model.safetensors
```

and place it at:

```text
model/final_model/model.safetensors
```

This is required because the model weights are excluded from the normal Git repository to keep the repository lightweight.

---

# License

This project is provided for educational and assessment purposes.
