# DailyMed Drug Label Scraper

A Python-based CLI tool to download structured drug labeling (SPL) XML files from the [FDA DailyMed](https://dailymed.nlm.nih.gov/dailymed/) website, using official public APIs.

This tool is designed for data scientists, healthcare researchers, and engineers who want to build drug information retrieval or question answering systems from real drug labels.

---

## Features

- Fetch the full drug index from DailyMed
- Search for drugs by name (exact or partial match)
- Download drug label XML files by `setid`
- Command-line interface using `argparse`
- Support for batch downloads
- Optional: default fallback drugs when no input is provided

---

## Installation

```bash
git clone https://github.com/yourusername/dailymed_scraper.git
cd dailymed_scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


Download specific drug labels:
```python scrap_data/dailymed_scaper.py --drugs ibuprofen metformin --limit 3 --save_dir ./xmls```
Use default drug list:
```python scrap_data/dailymed_scaper.py```

## Arguments:
Argument | Description | Default
--drugs | List of drug names to search & download | Optional
--limit | Max XML files to download per drug | 3
--save_dir | Directory to save the downloaded XML files | dailymed_xmls


### Downloaded XMLs will be saved as:
dailymed_xmls/
├── 6ae0e6ac-3e4c-4c7f-a848-97a6ee660d84.xml
├── b6559fb9-2dea-49c0-a274-3e77741a0ffd.xml
...
