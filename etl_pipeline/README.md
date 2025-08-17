# ETL Pipeline for Knowledge Base Datasets

This folder contains a modular, extensible ETL pipeline for retrieving, cleaning, and preparing authoritative datasets (starting with AWS) for AI chatbot and RAG applications.

## Structure

- `orchestrate_etl.py` — Main script to run ETL for any supported dataset or topic
- `steps/` — Modular scripts/classes for each ETL step:
  - **fetch**: Download/crawl raw data from the source
  - **enrich**: Add metadata or extract additional info (e.g., PDF links)
  - **clean**: Remove noise, standardize content
  - **chunk**: Split content into manageable pieces for RAG/vectorization
  - **dedupe**: Remove duplicate or near-duplicate chunks
- `README.md` — This file

## Supported Topics & Datasets

- **aws** (default)
  - whitepapers
  - well_architected_framework
  - architecture_center

## Usage

### Run all AWS datasets (default):

```sh
python orchestrate_etl.py
```

### Run a specific AWS dataset:

```sh
python orchestrate_etl.py --dataset whitepapers
python orchestrate_etl.py --dataset well_architected_framework
python orchestrate_etl.py --dataset architecture_center
```

### Run all datasets for a different topic (future):

```sh
python orchestrate_etl.py --topic azure
```

### Run a specific dataset for a topic (future):

```sh
python orchestrate_etl.py --topic azure --dataset reference_architectures
```

### Adjustable chunk size (where supported):

```sh
python orchestrate_etl.py --dataset well_architected_framework --chunk_size 2000
```

## Extending to New Topics or Datasets

1. Add a new topic and/or dataset function/class in `orchestrate_etl.py` and `steps/`.
2. Register the new dataset under the appropriate topic in the `PIPELINES` dictionary in `orchestrate_etl.py`.
3. Update this README.

## Output

- All outputs are JSONL, ready for vectorization and ingestion into S3, Bedrock, OpenSearch, DynamoDB, etc.
- Example output files:
  - `aws_whitepapers_chunks_deduped.jsonl`
  - `aws_wa_framework_chunks_deduped.jsonl`
  - `aws_architecture_center_chunks_deduped.jsonl`

## System Requirements & Troubleshooting

- **Python 3.8+**
- **Google Chrome** (for Selenium crawling)
- **ChromeDriver** (must be installed and in your PATH)
- Install Python dependencies: `pip install -r requirements.txt`

If you see errors related to Selenium or ChromeDriver:

- Ensure ChromeDriver is installed and matches your Chrome version ([download here](https://chromedriver.chromium.org/downloads)).
- On macOS, you can install with `brew install chromedriver`.
- If you see `selenium.common.exceptions.WebDriverException`, check your PATH and permissions.

## FAQ & Tips

- To add a new dataset, copy a modular ETL class in `steps/` and register it in `orchestrate_etl.py`.
- For debugging, add `print()` statements or use Python logging in ETL classes.
- For large crawls, increase `--chunk_size` for fewer, larger chunks.

## Contributing

Contributions and new connectors are welcome! Please document new datasets and update this README.

---

This pipeline is designed for easy expansion to new clouds, vendors, or open datasets. Contributions and new connectors are welcome!
