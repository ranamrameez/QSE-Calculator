#!/usr/bin/env python3
"""
Fetches end-of-day QSE prices from Twelve Data (free tier, exchange=QE) and
writes prices.json at the repo root, which the static site reads same-origin
(no CORS, no exposed API key — the key only ever lives in this server-side
Action run, via the TWELVEDATA_API_KEY repo secret).

Ticker list is pulled straight out of qse-trading-workbook.html's
TICKER_NAMES map, so you only maintain that list in one place.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

API_KEY = os.environ.get("TWELVEDATA_API_KEY")
HTML_FILE = "qse-trading-workbook.html"
OUTPUT_FILE = "prices.json"
EXCHANGE = "QE"  # Twelve Data's code for the Qatar Stock Exchange

def extract_tickers(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"const TICKER_NAMES\s*=\s*\{(.*?)\};", html, re.S)
    if not m:
        raise RuntimeError("Could not find TICKER_NAMES in " + html_path)
    body = m.group(1)
    # keys look like: VFQS:'Vodafone Qatar',
    return re.findall(r"([A-Z]{2,8}):\s*'", body)

def fetch_batch(symbols):
    joined = ",".join(symbols)
    qs = urllib.parse.urlencode({"symbol": joined, "exchange": EXCHANGE, "apikey": API_KEY})
    url = f"https://api.twelvedata.com/quote?{qs}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode())

def main():
    if not API_KEY:
        print("ERROR: TWELVEDATA_API_KEY is not set (add it as a repo secret).", file=sys.stderr)
        sys.exit(1)

    tickers = extract_tickers(HTML_FILE)
    print(f"Found {len(tickers)} tickers: {tickers}")

    prices = {}
    # Twelve Data batches multiple symbols into one call when comma-separated.
    # Chunk defensively in case the symbol list grows past what one call likes.
    CHUNK = 25
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        try:
            data = fetch_batch(chunk)
        except Exception as e:
            print(f"WARN: batch fetch failed for {chunk}: {e}", file=sys.stderr)
            continue

        # Single-symbol requests return one flat object; multi-symbol requests
        # return {symbol: {...}} per Twelve Data's docs.
        if len(chunk) == 1:
            data = {chunk[0]: data}

        for sym in chunk:
            entry = data.get(sym)
            if not entry or "close" not in entry:
                print(f"WARN: no price for {sym}: {entry}", file=sys.stderr)
                continue
            try:
                prices[sym] = float(entry["close"])
            except (TypeError, ValueError):
                print(f"WARN: bad close value for {sym}: {entry.get('close')}", file=sys.stderr)
        time.sleep(1)  # stay well under the free-tier rate limit

    if not prices:
        print("ERROR: no prices fetched, leaving prices.json untouched.", file=sys.stderr)
        sys.exit(1)

    prices["_updated"] = datetime.now(timezone.utc).isoformat()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, indent=2, sort_keys=True)
    print(f"Wrote {OUTPUT_FILE} with {len(prices)-1} prices.")

if __name__ == "__main__":
    main()
