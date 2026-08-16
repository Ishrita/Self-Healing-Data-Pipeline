"""
pipeline.py

A self-healing data pipeline. If incoming data has a schema mismatch
against what's expected, instead of crashing with a KeyError, it asks a
local LLM (phi3, via Ollama) to semantically map the mismatched columns
to the expected schema, and continues running.
"""

import pandas as pd
import requests
import json

# The schema our downstream database strictly requires
EXPECTED_SCHEMA = ["transaction_id", "customer_email", "purchase_amount", "purchase_date"]

# The messy data we actually received today
incoming_data = pd.DataFrame({
    "txn_id": ["A1", "A2"],
    "email_address": ["alice@test.com", "bob@test.com"],
    "total_cost": [150.00, 89.50],
    "date": ["2026-05-26", "2026-05-26"]
})


def heal_schema(expected_cols, actual_cols):
    """
    Asks a local LLM to map unknown columns to the expected schema.
    """
    prompt = f"""
    You are a data engineer system. Your job is to map actual data columns to the expected schema.

    Expected columns: {expected_cols}
    Actual columns: {actual_cols}

    Match the actual columns to the expected columns based on semantic meaning.
    Return ONLY a valid JSON object where the keys are the actual columns and the values are the expected columns.
    Do not include any markdown, explanations, or text outside the JSON.
    """

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "phi3",
        "prompt": prompt,
        "stream": False,
        "format": "json"  # This forces Ollama to output valid JSON
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        # Extract the JSON string from the response
        result_text = response.json().get("response", "{}")
        mapping = json.loads(result_text)
        return mapping

    except Exception as e:
        print(f"CRITICAL: LLM healing failed. Error: {e}")
        return None


def process_data(df, expected_schema):
    actual_cols = list(df.columns)

    # Check if schemas match exactly
    if set(actual_cols) == set(expected_schema):
        print("Schema validation passed. Proceeding with pipeline...")
        return df

    print("WARNING: Schema mismatch detected. Initiating self-healing...")

    # Attempt to heal
    mapping = heal_schema(expected_schema, actual_cols)

    if mapping:
        print(f"Healing successful. Applying mapping: {mapping}")
        df = df.rename(columns=mapping)

        # Verify if healing caught everything
        missing_cols = [col for col in expected_schema if col not in df.columns]
        if missing_cols:
            print(f"ERROR: Healing incomplete. Still missing: {missing_cols}")
            # Trigger PagerDuty/Email alert here
            raise KeyError("Unrecoverable schema drift.")
        else:
            print("Pipeline successfully healed. Continuing data transformations...")
            return df
    else:
        raise RuntimeError("Self-healing failed to return a valid mapping.")


if __name__ == "__main__":
    healed_df = process_data(incoming_data, EXPECTED_SCHEMA)
    print("\nFinal DataFrame:")
    print(healed_df.head())
