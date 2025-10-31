import asyncio
from scrape import fetch_html

async def fetch_and_save_html(url, filename):
    html = await fetch_html(url)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved HTML from {url} to {filename}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python fetch_and_save_html.py <url> <filename>")
        sys.exit(1)
    url = sys.argv[1]
    filename = sys.argv[2]
    asyncio.run(fetch_and_save_html(url, filename))
