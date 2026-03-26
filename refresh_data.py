"""
NBA Chart Data Refresher
=========================
Automatically fetches the latest BBRef standings pages
and regenerates chart.html — all in one command.

Usage:
    python refresh_data.py

Run this from your Coding folder whenever you want fresh data.
"""

from playwright.sync_api import sync_playwright
import subprocess, sys, time, os

EAST_URL = "https://www.basketball-reference.com/leagues/NBA_2026_standings_by_date_eastern_conference.html"
WEST_URL = "https://www.basketball-reference.com/leagues/NBA_2026_standings_by_date_western_conference.html"

def fetch_page(page, url, save_as):
    print(f"  Loading {save_as}...")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    # Wait for the standings table to actually appear
    page.wait_for_selector("table#standings_by_date", timeout=20000)
    html = page.content()
    with open(save_as, "w", encoding="utf-8") as f:
        f.write(html)
    size_kb = os.path.getsize(save_as) // 1024
    print(f"  Saved {save_as} ({size_kb} KB)")

def main():
    print("NBA Chart Refresher")
    print("=" * 40)

    print("\nStep 1: Fetching data from Basketball Reference...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            fetch_page(page, EAST_URL, "bbref_east.html")
            time.sleep(2)  # polite pause between requests
            fetch_page(page, WEST_URL, "bbref_west.html")
        except Exception as e:
            print(f"\nERROR fetching data: {e}")
            print("BBRef may be blocking the request. Try again in a few minutes.")
            browser.close()
            sys.exit(1)

        browser.close()

    print("\nStep 2: Generating chart...")
    result = subprocess.run([sys.executable, "generate_chart.py"], capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print("ERROR:", result.stderr)
        sys.exit(1)

    print("\nDone! Open chart.html in your browser.")
    print("Tip: If chart.html is already open, just refresh the tab.")

if __name__ == "__main__":
    main()
