import os
import time
import requests
from typing import List, Optional
from tqdm import tqdm
from pydantic import BaseModel
from requests.adapters import HTTPAdapter, Retry


class SPLRecord(BaseModel):
    setid: str
    title: str


def get_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504)) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class DailyMedScraper:
    INDEX_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
    XML_URL = "https://dailymed.nlm.nih.gov/dailymed/downloads/labelxml.cfm?setid={setid}"

    def __init__(self, save_dir="dailymed_xmls"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.session = get_retry_session()
        self.records: List[SPLRecord] = []

    def fetch_index(self):
        resp = self.session.get(self.INDEX_URL)
        resp.raise_for_status()
        self.records = [SPLRecord(**entry) for entry in resp.json()]
        print(f"[INFO] Found {len(self.records)} records.")

    def filter_records(self, keyword: str) -> List[SPLRecord]:
        return [rec for rec in self.records if keyword.lower() in rec.title.lower()]

    def download_xml(self, record: SPLRecord) -> bool:
        url = self.XML_URL.format(setid=record.setid)
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200 and resp.content.startswith(b"<?xml"):
                path = os.path.join(self.save_dir, f"{record.setid}.xml")
                with open(path, "wb") as f:
                    f.write(resp.content)
                return True
        except Exception as e:
            print(f"[ERROR] Failed: {record.title} ({record.setid}) - {e}")
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
