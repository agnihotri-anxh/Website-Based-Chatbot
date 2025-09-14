import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_urls(page_url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    response = requests.get(page_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    urls = set()
    for link in soup.find_all("a", href=True):
        full_url = urljoin(page_url, link["href"])
        urls.add(full_url)

    return urls


if __name__ == "__main__":
    page = "https://sybrant.com/apis/"
    all_urls = extract_urls(page)

    # Save to file
    with open("extracted_links1.txt", "w", encoding="utf-8") as f:
        for u in sorted(all_urls):   # sorted for consistency
            f.write(u + "\n")

    print(f"✅ {len(all_urls)} links saved to extracted_links.txt")
