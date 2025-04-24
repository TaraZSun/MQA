# Scape DailyMed SPL XML files
import os
import time
import requests
from typing import List, Optional
from tqdm import tqdm
from pydantic import BaseModel
from requests.adapters import HTTPAdapter, Retry
import argparse

RETRIES = 3
BACKOFF_FACTOR = 0.3
# 500 → Server Error
# 502 → Bad Gateway
# 503 → Service Unavailable
# 504 → Gateway Timeout
STATUS_FORCELIST = (500, 502, 503, 504)

DRUG_NAMES = [
    "ibuprofen",
    "acetaminophen",
    "naproxen",
    "aspirin",
    "amoxicillin",
    "prednisone",
    "metformin",
    "simvastatin",
    "atorvastatin",
    "levothyroxine",
    "losartan",
    "sertraline",
    "omeprazole",
    "lisinopril",
    "gabapentin",
    "hydrochlorothiazide",
]
class DailyMedError(Exception):
    """Custom exception for DailyMed errors."""
    pass

class SPLRecord(BaseModel):
    """Define a data model for Structured Product Labelling records."""
    setid: str
    title: str


def get_retry_session(retries:int, 
                      backoff_factor: float, 
                      status_forcelist:list[int]
                      ) -> requests.Session:
    session = requests.Session()
    retries=RETRIES
    backoff_factor=BACKOFF_FACTOR 
    # exponential backoff strategy: sleep = backoff_factor * (2 ** (retry_number - 1))
    status_forcelist=STATUS_FORCELIST
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        # Only retry requests that use the HEAD, GET, or OPTIONS HTTP methods.
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class DailyMedScraper:
    # Get all drug label metadata (including setid)
    INDEX_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
    # Download the XML content for each drug label
    XML_URL = "https://dailymed.nlm.nih.gov/dailymed/downloads/labelxml.cfm?setid={setid}"

    def __init__(self, save_dir: str="dailymed_xmls"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.session = get_retry_session(retries=RETRIES,backoff_factor=BACKOFF_FACTOR,status_forcelist=STATUS_FORCELIST)   
        self.records: List[SPLRecord] = []

    def fetch_index(self):
        resp = self.session.get(self.INDEX_URL)
        resp.raise_for_status()
        data = resp.json()
        if "data" in data:
            self.records = [SPLRecord(**entry) for entry in data["data"]]
        else:
            raise ValueError("Unexpected response structure: missing 'data' field")

        print(f"[INFO] Found {len(self.records)} records.")

    def filter_records(self, keyword: str) -> List[SPLRecord]:
        return [rec for rec in self.records if keyword.lower() in rec.title.lower()]

    def download_xml(self, record: SPLRecord) -> bool:
        url = self.XML_URL.format(setid=record.setid)
        print(f"[DEBUG] Trying to download from: {url}")
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                path = os.path.join(self.save_dir, f"{record.setid}.xml")
                with open(path, "wb") as f:
                    f.write(resp.content)
                return True
            else:
                print(f"[WARN] Failed with status {resp.status_code}: {url}")
        except Exception as e:
            print(f"[ERROR] {record.setid} - {e}")
        return False


    def download_batch(self, records: List[SPLRecord], limit: Optional[int] = None, delay: float = 0.5):
        count = 0
        for record in tqdm(records[:limit] if limit else records):
            path = os.path.join(self.save_dir, f"{record.setid}.xml")
            if not os.path.exists(path):
                success = self.download_xml(record)
                if success:
                    count += 1
                    print(f"[INFO] Downloaded: {record.title}")
                time.sleep(delay)
        print(f"[INFO] Completed {count} downloads.")

def download_by_drug_names(self, drug_names: list[str], limit_per_drug: int = 5, delay: float = 0.5):
    """
    Download XML files for a list of drug names.
    :param drug_names: List of strings (e.g. ["ibuprofen", "acetaminophen"])
    :param limit_per_drug: Max number of XMLs to download per drug
    :param delay: Delay between downloads to be gentle on server
    """
    all_matched = []

    for name in drug_names:
        print(f"\n[INFO] Searching for: {name}")
        matched = self.filter_records(name)
        if matched:
            print(f"[INFO] Found {len(matched)} entries for '{name}'. Downloading up to {limit_per_drug}...")
            self.download_batch(matched, limit=limit_per_drug, delay=delay)
            all_matched.extend(matched[:limit_per_drug])
        else:
            print(f"[WARN] No match found for '{name}'")

    print(f"\n[INFO] Finished downloading XMLs for {len(drug_names)} drugs.")




def main() -> None:
    parser = argparse.ArgumentParser(description="Download drug label XMLs from DailyMed")
    parser.add_argument(
        "--drugs", 
        nargs="+", 
        help="List of drug names to download (e.g. ibuprofen metformin)"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=3, 
        help="Number of XMLs to download per drug (default: 3)"
    )
    parser.add_argument(
        "--save_dir", 
        type=str, 
        default="dailymed_xmls", 
        help="Directory to save downloaded XMLs"
    )

    args = parser.parse_args()

    scraper = DailyMedScraper(save_dir=args.save_dir)
    scraper.fetch_index()
    drug_list = args.drugs if args.drugs else DRUG_NAMES
    for drug_name in drug_list:
        print(f"[INFO] Processing drug: {drug_name}")
        records = scraper.filter_records(drug_name)
        scraper.download_batch(records, limit=args.limit)


if __name__ == "__main__":
    main()


