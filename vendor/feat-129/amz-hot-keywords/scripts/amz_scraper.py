#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMZ123 US Top Keywords Scraper

Scrapes ABA (Amazon Brand Analytics) weekly search term rankings from AMZ123.
Outputs CSV with: search_term, current_rank, last_rank, trend.

Usage:
    python3 amz_scraper.py --keyword "dog bed"
    python3 amz_scraper.py --keyword "yoga mat" --max-results 100
    python3 amz_scraper.py --keyword "pet supplies" --output-dir ./data
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.amz123.com/usatopkeywords"

# Multiple selector strategies to survive page redesigns.
# When AMZ123 changes their frontend class names, update this list.
SELECTORS = {
    "item_container": [
        ".table-body-item",
        ".hotword-item",
        ".keyword-item",
        "[class*='table-body'] > div",
    ],
    "word": [
        ".table-body-item-words-word",
        ".table-body-item-word",
        "[class*='word']",
    ],
    "rank_container": [
        ".table-body-item-rank",
        "[class*='rank']",
    ],
}


def calculate_trend(current_rank: int, last_rank: int) -> str:
    """Determine trend direction from rank changes.

    Lower rank number = higher popularity, so:
      current < last  -> "up"   (popularity rose)
      current > last  -> "down" (popularity fell)
      current == last -> "flat"
      last == 0       -> "new"  (newly appeared on the chart)
    """
    if last_rank == 0:
        return "new"
    if current_rank < last_rank:
        return "up"
    if current_rank > last_rank:
        return "down"
    return "flat"


def setup_driver(headless: bool = True) -> webdriver.Chrome | None:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"[ERROR] Failed to start Chrome: {e}", file=sys.stderr)
        print("[HINT] Ensure Chrome browser is installed. Selenium 4.6+ auto-manages ChromeDriver.", file=sys.stderr)
        return None


def _find_elements(driver, selector_list: list[str]):
    """Try multiple CSS selectors, return elements from the first one that matches."""
    for sel in selector_list:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            if elems:
                return elems, sel
        except Exception:
            continue
    return [], None


def extract_keywords(driver, max_count: int = 200) -> list[dict]:
    """Extract keyword ranking data from the loaded page using JS injection.

    Tries the primary JS extraction first, then falls back to element-by-element
    scraping if the page structure doesn't match the expected selectors.
    """
    # Primary approach: JS extraction with fallback selectors
    for word_sel in SELECTORS["word"]:
        for container_sel in SELECTORS["item_container"]:
            script = f"""
            const items = Array.from(document.querySelectorAll('{container_sel}'));
            return items.slice(0, {max_count}).map(item => {{
              const wordElem = item.querySelector('{word_sel}');
              const word = wordElem ? wordElem.textContent.trim() : '';

              const rankContainer = item.querySelector('{SELECTORS["rank_container"][0]}');
              let currentRank = 0, lastRank = 0;
              if (rankContainer) {{
                const spans = rankContainer.querySelectorAll('span');
                if (spans.length >= 2) {{
                  const ct = spans[0].textContent.trim();
                  const lt = spans[1].textContent.trim();
                  currentRank = /^\\d+$/.test(ct) ? parseInt(ct) : 0;
                  lastRank = /^\\d+$/.test(lt) ? parseInt(lt) : 0;
                }}
              }}
              return {{ word, currentRank, lastRank }};
            }});
            """
            try:
                data = driver.execute_script(script)
                valid = [d for d in data if d.get("word")]
                if valid:
                    print(f"[INFO] Extracted {len(valid)} keywords using selectors: container={container_sel}, word={word_sel}")
                    return valid
            except Exception:
                continue

    # Fallback: try alternate rank selectors
    for rank_sel in SELECTORS["rank_container"][1:]:
        for container_sel in SELECTORS["item_container"]:
            script = f"""
            const items = Array.from(document.querySelectorAll('{container_sel}'));
            return items.slice(0, {max_count}).map(item => {{
              const wordElem = item.querySelector('{SELECTORS["word"][0]}');
              const word = wordElem ? wordElem.textContent.trim() : '';
              const rankContainer = item.querySelector('{rank_sel}');
              let currentRank = 0, lastRank = 0;
              if (rankContainer) {{
                const spans = rankContainer.querySelectorAll('span');
                if (spans.length >= 2) {{
                  const ct = spans[0].textContent.trim();
                  const lt = spans[1].textContent.trim();
                  currentRank = /^\\d+$/.test(ct) ? parseInt(ct) : 0;
                  lastRank = /^\\d+$/.test(lt) ? parseInt(lt) : 0;
                }}
              }}
              return {{ word, currentRank, lastRank }};
            }});
            """
            try:
                data = driver.execute_script(script)
                valid = [d for d in data if d.get("word")]
                if valid:
                    print(f"[INFO] Extracted {len(valid)} keywords using fallback selectors: container={container_sel}, rank={rank_sel}")
                    return valid
            except Exception:
                continue

    return []


def scrape(keyword: str, max_results: int = 200, headless: bool = True) -> list[dict]:
    """Main scraping entry point. Returns list of dicts with search_term, current_rank, last_rank, trend."""
    driver = setup_driver(headless)
    if not driver:
        return []

    try:
        search_url = f"{BASE_URL}?k={keyword}"
        print(f"[INFO] Navigating to: {search_url}")
        driver.get(search_url)

        # Wait for content to render (JS-heavy page)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["word"][0]))
            )
        except TimeoutException:
            print("[WARN] Timed out waiting for primary selector, trying fallbacks...")
            time.sleep(5)

        # Save debug HTML for troubleshooting
        script_dir = os.path.dirname(os.path.abspath(__file__))
        debug_path = os.path.join(script_dir, "debug_page.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        raw_data = extract_keywords(driver, max_results)

        if not raw_data:
            # Scroll to trigger lazy loading, then retry
            print("[WARN] No data found, scrolling page and retrying...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            raw_data = extract_keywords(driver, max_results)

        results = []
        for item in raw_data:
            cr = item["currentRank"]
            lr = item["lastRank"]
            results.append({
                "search_term": item["word"],
                "current_rank": cr,
                "last_rank": lr,
                "trend": calculate_trend(cr, lr),
            })

        print(f"[OK] Scraped {len(results)} keywords for '{keyword}'")
        return results

    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return []

    finally:
        driver.quit()


def save_csv(data: list[dict], keyword: str, output_dir: str) -> str | None:
    if not data:
        print("[ERROR] No data to save")
        return None

    os.makedirs(output_dir, exist_ok=True)
    safe_keyword = keyword.replace(" ", "_").replace("/", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"amz123_hotwords_{safe_keyword}_{ts}.csv")

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"[OK] Saved to {filename}")
    return filename


def main():
    parser = argparse.ArgumentParser(
        description="AMZ123 US Top Keywords Scraper - ABA weekly search term rankings",
    )
    parser.add_argument("--keyword", required=True, help="Search keyword (e.g. 'dog bed')")
    parser.add_argument("--max-results", type=int, default=200, help="Max keywords to scrape (default: 200)")
    parser.add_argument("--output-dir", default=".", help="Directory to save CSV output (default: current dir)")
    parser.add_argument("--headless", type=str, default="true", help="Run Chrome headless (true/false, default: true)")

    args = parser.parse_args()
    headless = args.headless.lower() == "true"

    print(f"[INFO] Keyword: '{args.keyword}' | Max results: {args.max_results} | Headless: {headless}")

    data = scrape(args.keyword, args.max_results, headless)

    if not data:
        print("[ERROR] No results obtained. Check debug_page.html for clues.")
        sys.exit(1)

    csv_path = save_csv(data, args.keyword, args.output_dir)

    # Also print summary to stdout as JSON for agent consumption
    summary = {
        "keyword": args.keyword,
        "total_results": len(data),
        "csv_path": csv_path,
        "sample": data[:5],
    }
    print("\n--- RESULT_JSON ---")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()

