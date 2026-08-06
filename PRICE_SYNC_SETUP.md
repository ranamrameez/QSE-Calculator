# Setting up automatic QSE price sync on GitHub Pages

The workbook reads a same-origin `prices.json` file on navigation to the
Dashboard or Portfolio pages (and once on load). It never calls an external
API directly from the browser — that's what the GitHub Action below is for.

## 1. Repo layout
Put these at the **root** of your GitHub Pages repo, alongside
`qse-trading-workbook.html` (rename to `index.html` if you want it at your
Pages root URL):

```
your-repo/
├── qse-trading-workbook.html   (or index.html)
├── prices.json                 (created automatically by the Action — don't create by hand)
├── scripts/
│   └── fetch_prices.py
└── .github/
    └── workflows/
        └── update-prices.yml
```

## 2. Get a free Twelve Data API key
Sign up at twelvedata.com (free "Basic" plan, no card required) and copy your
API key from the dashboard.

## 3. Add it as a repo secret
In your GitHub repo: **Settings → Secrets and variables → Actions → New
repository secret**
- Name: `TWELVEDATA_API_KEY`
- Value: (paste your key)

This keeps the key server-side only — it's never sent to anyone's browser.

## 4. Enable the Action
Push these files. The workflow runs automatically at 10:30 UTC (~13:30 Doha
time, shortly after QSE's 13:15 close) on Sunday–Thursday. You can also
trigger it manually any time from the repo's **Actions** tab →
"Update QSE prices" → **Run workflow** — handy for testing.

## 5. Adding new tickers
The script pulls its ticker list straight from the `TICKER_NAMES` map inside
`qse-trading-workbook.html`. Add a new symbol there (e.g. `"NEWSYM: 'Company
Name',"`) and the next Action run will pick it up automatically — nothing
else to configure.

## What this does and doesn't give you
- **Does:** end-of-day QSE closing prices, refreshed once a day, no manual
  entry needed, no server/domain to pay for.
- **Doesn't:** intraday/real-time ticking prices — that's a paid product on
  every QSE data vendor, free or otherwise. If you ever need that, the
  workbook's manual "Market" price field still works exactly as before.
