import json
import hashlib
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class ArchitectureCenterETL:
    BASE_URL = "https://aws.amazon.com/architecture/"
    FINAL_OUTPUT = "aws_architecture_center_chunks_deduped.jsonl"
    CHUNK_SIZE = 1000

    def fetch(self):
        print("[ETL] Crawling AWS Architecture Center (Selenium)...")
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)
        visited = set()
        to_visit = [(self.BASE_URL, 0)]
        results = []
        max_depth = 2
        while to_visit:
            url, depth = to_visit.pop(0)
            if url in visited or depth > max_depth:
                continue
            visited.add(url)
            try:
                driver.get(url)
                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                content = self.extract_content(soup, url)
                if content:
                    results.append({"url": url, "content": content})
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("https://aws.amazon.com/") and any(p in href for p in ["/architecture/", "/solutions/", "/patterns/", "/whitepapers/", "/blog/", "/reference-architectures/", ".pdf"]):
                        to_visit.append((href, depth + 1))
            except Exception as e:
                print(f"[ERROR] Failed to load {url}: {e}")
        driver.quit()
        print(f"[ETL] Crawled {len(results)} pages.")
        return results

    def extract_content(self, soup, url):
        main = soup.body
        if not main:
            return None
        content = []
        for tag in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "pre"]):
            if tag.name.startswith("h"):
                content.append({"type": "heading", "level": int(tag.name[1]), "text": tag.get_text(strip=True)})
            elif tag.name == "p":
                content.append({"type": "paragraph", "text": tag.get_text(strip=True)})
            elif tag.name in ["ul", "ol"]:
                items = [li.get_text(strip=True) for li in tag.find_all("li")]
                content.append({"type": tag.name, "items": items})
            elif tag.name == "pre":
                content.append({"type": "pre", "text": tag.get_text()})
        return content

    def chunk(self, entries):
        print("[ETL] Chunking Architecture Center content...")
        chunks = []
        for entry in entries:
            url = entry["url"]
            for idx, block in enumerate(entry["content"]):
                text = block.get("text") or " ".join(block.get("items", []))
                if not text:
                    continue
                for cidx, chunk in enumerate(self.chunk_text(text)):
                    chunk_entry = {
                        "url": url,
                        "chunk": chunk,
                        "chunk_index": f"{idx}_{cidx}",
                        "type": block.get("type"),
                        "level": block.get("level") if "level" in block else None
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
        chunks = self.chunk(entries)
        unique_chunks = self.dedupe(chunks)
        self.save(unique_chunks)

if __name__ == "__main__":
    etl = ArchitectureCenterETL()
    etl.run()
