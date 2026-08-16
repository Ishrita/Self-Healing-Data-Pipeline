# Self-Healing Data Pipeline

A data pipeline that doesn't crash the moment an upstream team renames a column. Instead of throwing a `KeyError` on schema drift, it pauses, asks a local LLM to semantically map the mismatched columns to the expected schema, and continues running — logging a warning instead of failing the job.

> Based on the tutorial ["Implementing a Self-Healing Data Pipeline"](https://amanxai.com/2026/05/27/implementing-a-self-healing-data-pipeline/) by Aman Kharwal.

---

## The Problem

Traditional pipelines are rigid. If code expects `['id', 'price', 'transaction_date']` and receives `['user_id', 'cost', 'date_of_purchase']`, the script throws a `KeyError` and stops. Someone gets paged, a sprint gets derailed fixing a fragile mapping — for what is often just a renamed column.

##  How It Works

1. **Detection** — the pipeline compares incoming data columns to the expected schema.
2. **Evaluation** — on a mismatch, the expected and actual schemas are passed to a lightweight local LLM.
3. **Healing** — the LLM returns a JSON mapping dictionary used to dynamically rename the columns.
4. **Execution & Alerting** — the pipeline proceeds with the transformation and logs a non-fatal warning so the engineering team knows the schema changed.

```
Incoming data ─▶ Schema check ─▶ (mismatch?) ─▶ phi3 via Ollama ─▶ column mapping (JSON) ─▶ renamed DataFrame ─▶ pipeline continues
```

Only column **names** are sent to the LLM — never row-level data — so inference is fast, cheap, and nothing about your actual records leaves your machine.

**Note:** this pattern is for schema-level healing (metadata), not row-level cleaning. Don't route millions of individual rows through an LLM in real time — use it for structural decisions, and let plain Python handle the data itself.

---

##  Project Structure

```
self-healing-data-pipeline/
├── pipeline.py           # Core pipeline: schema check, LLM healing, integration
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

##  Requirements

- Python 3.9+
- [Ollama](https://ollama.com/download) installed and running locally
- The `phi3` model pulled via Ollama

---

##  Setup

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/self-healing-data-pipeline.git
cd self-healing-data-pipeline
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama and pull the model

Download and install Ollama from [ollama.com/download](https://ollama.com/download), then pull `phi3`:

```bash
ollama pull phi3
```

Make sure the Ollama service is running before executing the pipeline.

### 5. Run the pipeline

```bash
python pipeline.py
```

You should see the schema mismatch get detected, healed via the LLM mapping, and the corrected DataFrame printed out.

---

##  Example

**Expected schema:**
```python
["transaction_id", "customer_email", "purchase_amount", "purchase_date"]
```

**Incoming (messy) data columns:**
```python
["txn_id", "email_address", "total_cost", "date"]
```

**Pipeline output:**
```
WARNING: Schema mismatch detected. Initiating self-healing...
Healing successful. Applying mapping: {'txn_id': 'transaction_id', 'email_address': 'customer_email', 'total_cost': 'purchase_amount', 'date': 'purchase_date'}
Pipeline successfully healed. Continuing data transformations...
```

---

## Why This Matters

Teams can lose significant sprint time fixing fragile column mappings whenever an upstream source changes its schema. Automating that mapping with a small local LLM turns a page-worthy failure into a self-recovering, logged event — a small but real step toward more resilient, adaptive data infrastructure.

---

## Tech Stack

- Python
- Pandas
- [Ollama](https://ollama.com/) running Microsoft's `phi3` (local LLM, no API costs, no data leaves your machine)
- `requests` for the Ollama REST API

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Credits

Tutorial and original code by [Aman Kharwal](https://amanxai.com/). Check out his book **[Hands-On GenAI, LLMs & AI Agents](https://amzn.in/d/0gl5nIfa)** for more real-world AI project walkthroughs.
