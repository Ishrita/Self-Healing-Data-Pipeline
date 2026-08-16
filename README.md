# Self-Healing-Data-Pipeline
A data pipeline that doesn't crash the moment an upstream team renames a column. Instead of throwing a KeyError on schema drift, it pauses, asks a local LLM to semantically map the mismatched columns to the expected schema, and continues running — logging a warning instead of failing the job.
