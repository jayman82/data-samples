import requests
import json
import hashlib
import time
from bs4 import BeautifulSoup


class WhitepaperETL:
    API_URL = "https://aws.amazon.com/api/dirs/items/search?item.directoryId=whitepapers-cards-interactive-whitepapers&item.locale=en_US&tags.id=%21GLOBAL%23local-tags-content-type%23reference-arch-diagram&tags.id=%21GLOBAL%23local-tags-content-type%23reference-material&sort_by=item.additionalFields.publishedDate&sort_order=desc&size=1000"
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    CHUNK_SIZE = 1000
    FINAL_OUTPUT = "aws_whitepapers_chunks_deduped.jsonl"

    def fetch(self):
        print("[ETL] Fetching whitepapers metadata from AWS API...")
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://aws.amazon.com/whitepapers/",
            "Accept-Language": "en-US,en;q=0.9"
        }
        resp = requests.get(self.API_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        print(f"[ETL] Found {len(items)} whitepapers/guides.")
        return [self.process_whitepaper(item) for item in items]

    def process_whitepaper(self, item):
        fields = item.get("item", {}).get("additionalFields", {})
        tags = [t.get("name") for t in item.get("tags", []) if t.get("name")]
        return {
            "id": item.get("item", {}).get("id"),
            "title": fields.get("title"),
            "summary": fields.get("body"),
            "url": fields.get("primaryCTALink") or fields.get("ctaLink"),
            "badge": fields.get("badge"),
            "publishedDate": fields.get("publishedDate"),
            "tags": tags
        }

    def enrich_with_pdf(self, entries):
        print("[ETL] Enriching with PDF URLs...")
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        for entry in entries:
            html_url = entry.get("url")
            pdf_url = None
            if html_url and html_url.endswith(".html"):
                try:
                    resp = requests.get(html_url, headers=headers, timeout=15)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            if href.lower().endswith(".pdf"):
                                pdf_url = href if href.startswith("http") else "https://docs.aws.amazon.com" + href
                                break
                        if not pdf_url and html_url.endswith(".html"):
                            pdf_url_guess = html_url[:-5] + ".pdf"
                            head = requests.head(
                                pdf_url_guess,
                                headers=headers,
                                timeout=10
                                )
                            if head.status_code == 200:
                                pdf_url = pdf_url_guess
                    time.sleep(0.5)
                except Exception:
                    pdf_url = None
            entry["pdf_url"] = pdf_url
        return entries

    def chunk(self, entries):
        print("[ETL] Chunking whitepaper summaries...")
        chunks = []
        for entry in entries:
            text = entry.get("summary") or entry.get("body") or ""
            if not text:
                continue
            for idx, chunk in enumerate(self.chunk_text(text)):
                chunk_entry = {
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "chunk": chunk,
                    "chunk_index": idx,
                    "source_url": entry.get("url"),
                    "tags": entry.get("tags", []),
                    "pdf_url": entry.get("pdf_url")
                }
                chunks.append(chunk_entry)
        print(f"[ETL] Chunked into {len(chunks)} total chunks.")
        return chunks

    def chunk_text(self, text):
        for i in range(0, len(text), self.CHUNK_SIZE):
            yield text[i:i + self.CHUNK_SIZE]

    def dedupe(self, chunks):
        print("[ETL] Deduplicating chunks...")
        seen_hashes = set()
        unique_chunks = []
        for chunk in chunks:
            chunk_hash = hashlib.sha256(chunk["chunk"].strip().encode("utf-8")).hexdigest()
            if chunk_hash not in seen_hashes:
                seen_hashes.add(chunk_hash)
                unique_chunks.append(chunk)
        print(f"[ETL] Deduplication complete. {len(unique_chunks)} unique chunks.")
        return unique_chunks

    def save(self, chunks):
        print(f"[ETL] Saving final output to {self.FINAL_OUTPUT}")
        with open(self.FINAL_OUTPUT, "w", encoding="utf-8") as fout:
            for chunk in chunks:
                fout.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        print("[ETL] Done.")

    def run(self):
        entries = self.fetch()
        entries = self.enrich_with_pdf(entries)
        chunks = self.chunk(entries)
        unique_chunks = self.dedupe(chunks)
        self.save(unique_chunks)


if __name__ == "__main__":
    etl = WhitepaperETL()
    etl.run()
