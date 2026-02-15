# Russian Text Adaptation Project (B1/B2 Levels)

A project automated tool designed to adapt Russian technical texts into **B1 (Intermediate)** and **B2 (Upper-Intermediate)** levels using Large Language Models (LLMs)

## Key Features
* **Multi-Prompting Strategy**: Implements *Role-based*, *Decomposition*, and *Zero-shot* prompting techniques to compare output quality.
* **Batch Processing**: Automatically processes multiple `.txt` files from the input directory.
* **Resilient API Integration**: Features an **Exponential Backoff** retry mechanism to handle Rate Limits (Error 429) and automatic **<think> token** stripping for cleaner outputs.
* **Localized Encoding**: Specifically configured with `ensure_ascii=False` to preserve Cyrillic characters in JSON outputs.

## Project Structure
```text
adaption_text_project/
├── venv/                # Python Virtual Environment
├── prompts/             # Prompt templates for each technique (.txt)
├── input_texts/         # Source Russian texts to be adapted
├── results/             # Structured JSON outputs organized by technique
├── scripts/
│   └── run.py           # Main execution script
├── config.py            # API & Model configurations
└── .env                 # API 