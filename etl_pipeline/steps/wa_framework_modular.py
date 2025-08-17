import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class WellArchitectedETL:
    """ETL for AWS Well-Architected Framework docs."""
    BASE_URL = "https://docs.aws.amazon.com/wellarchitected/latest/framework/"
    FINAL_OUTPUT = "aws_wa_framework_chunks_deduped.jsonl"

    def __init__(self, chunk_size=1000):
        """Initialize with adjustable chunk size."""
        self.CHUNK_SIZE = chunk_size

    def fetch(self):
        """Crawl all Well-Architected Framework docs using Selenium."""
        print(
            "[ETL] Crawling Well-Architected Framework docs (Selenium)..."
        )
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)
        visited = set()
        to_visit = [self.BASE_URL]
        results = []
        url_counter = 0

        def is_framework_url(href):
            # Accept both absolute and relative links within the framework
            if (
                href.startswith("/wellarchitected/latest/framework/") or
                href.startswith("wellarchitected/latest/framework/")
            ):
                return True
            if href.startswith(self.BASE_URL):
                return True
            return False

        while to_visit:
            url = to_visit.pop(0)
            if url in visited:
                continue
            url_counter += 1
            print(
                f"[ETL] Visiting ({url_counter}) {url} "
                f"(Visited: {len(visited)}, Queue: {len(to_visit)})"
            )
            visited.add(url)
            try:
                driver.get(url)
                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                content = self.extract_content(soup, url)
                if content:
                    print(
                        f"[ETL]   Extracted content from {url} "
                        f"({len(content)} blocks)"
                    )
                    results.append({"url": url, "content": content})
                new_links = 0
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if not href or href.endswith(".pdf"):
                        continue
                    # Normalize href to absolute URL
                    if href.startswith("/"):
                        next_url = "https://docs.aws.amazon.com" + href
                    elif href.startswith("http"):
                        next_url = href
                    else:
                        next_url = urljoin(url, href)
                    # Only crawl framework pages, skip anchors/fragments
                    if (
                        is_framework_url(next_url)
                        and ("#" not in next_url)
                        and (next_url not in visited)
                        and (next_url not in to_visit)
                    ):
                        to_visit.append(next_url)
                        new_links += 1
                if new_links > 0:
                    print(
                        f"[ETL] Found {new_links} internal links from {url}"
                    )
            except Exception as e:
                print(f"[ERROR] Failed to load {url}: {e}")
        driver.quit()
        print(f"[ETL] Crawled {len(results)} pages.")
        return results

    def extract_content(self, soup, url):
        """Extracts structured content blocks from the main body of a page."""
        main = soup.find("div", id="main-col-body") or soup.body
        if not main:
            return None
        content = []
        for tag in main.find_all([
            "h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "pre"
        ]):
            if tag.name.startswith("h"):
                content.append({
                    "type": "heading",
                    "level": int(tag.name[1]),
                    "text": tag.get_text(strip=True)
                })
            elif tag.name == "p":
                content.append({
                    "type": "paragraph",
                    "text": tag.get_text(strip=True)
                })
            elif tag.name in ["ul", "ol"]:
                items = [
                    li.get_text(strip=True) for li in tag.find_all("li")
                ]
                content.append({
                    "type": tag.name,
                    "items": items
                })
            elif tag.name == "pre":
                content.append({
                    "type": "pre",
                    "text": tag.get_text()
                })
        return content

    def chunk(self, entries):
        """Chunks extracted content into fixed-size segments."""
        print("[ETL] Chunking Well-Architected content...")
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
                        "level": (
                            block.get("level") if "level" in block else None
                        )
                    }
                    chunks.append(chunk_entry)
        print(f"[ETL] Chunked into {len(chunks)} total chunks.")
        return chunks

    def chunk_text(self, text):
        """Yield text in self.CHUNK_SIZE character segments."""
        for i in range(0, len(text), self.CHUNK_SIZE):
            yield text[i:i + self.CHUNK_SIZE]

    def dedupe(self, chunks):
        """Remove duplicate chunks from the same page/position."""
        print("[ETL] Deduplicating chunks...")
        seen_keys = set()
        unique_chunks = []
        for chunk in chunks:
            key = (chunk["url"], chunk["chunk_index"], chunk["chunk"].strip())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_chunks.append(chunk)
        print(
            f"[ETL] Deduplication complete. {len(unique_chunks)} chunks."
        )
        return unique_chunks

    def save(self, chunks):
        """Save chunks to the output JSONL file."""
        print(f"[ETL] Saving final output to {self.FINAL_OUTPUT}")
        with open(self.FINAL_OUTPUT, "w", encoding="utf-8") as fout:
            for chunk in chunks:
                fout.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        print("[ETL] Done.")

    def run(self):
        """Run the full ETL pipeline."""
        entries = self.fetch()
        chunks = self.chunk(entries)
        unique_chunks = self.dedupe(chunks)
        self.save(unique_chunks)



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Well-Architected ETL")
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=1000,
        help="Chunk size in characters"
    )
    args = parser.parse_args()
    etl = WellArchitectedETL(chunk_size=args.chunk_size)
    etl.run()
