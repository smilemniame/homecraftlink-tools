# HomeCraftLink Table Demo

A local demonstration of the HomeCraftLink domain table, with monthly snapshots, keyword filters, dropdowns, pagination and clipboard export.

## Quick start

Requires Python 3.11 and an internet connection for Bootstrap, icons and flag styles loaded from CDNs.

From this folder on Windows:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe preview_table_demo.py
```

Open http://127.0.0.1:5057/top_sites_fast . Stop the foreground server with Ctrl+C. Port 5057 must be free. An existing background preview must be stopped before launching another copy.

## Included sample data

Two snapshots, 202609 and 202610, contain the same 40 synthetic domains beneath example.com and example.org. These are demonstration rows, not a Tranco ranking or verified live websites. Matching sample statistics supply the dropdowns.

- Monthly ranking: YYYYMM.csv, no header, rank/domain columns.
- Suffix counts: YYYYMMp.csv, tld/count.
- Monthly words: word_counts_YYYYMM.csv, word/count.
- Global words: word_counts_global_rank.csv, word/total_count/months_present. The global dropdown displays and sorts by months_present.
- Categories: categories.csv, category followed by keyword fields. These filters match words in domains; they do not verify page topics.

## Demo scope

The launcher disables outgoing backend HTTP requests and dotenv loading. Live status, metadata and IP/GEO analysis are outside this demo. Titles may remain empty and status badges may show unavailable results. Browser requests for CDN styles and favicons still use external services.

The copied backend also contains routes for other HomeCraftLink features whose templates are not included. Use /top_sites_fast for this package. Atlas, importers, globe and slideshow are not bundled.

## Technology and validation

Python, Flask and Jinja render CSV-backed pages; JavaScript updates table rows over POST; Bootstrap provides the interface. No MySQL dependency was installed for the successful table test.

Validation on the owner's existing Python 3.11.6 environment: 13 Flask tests passed; browser scan showed the coffee filter and second page; owner confirmed the global month counts and copying two selected domains.

Fresh virtual-environment installation from requirements.txt passed on the owner's Windows machine (report 000830). pip check found no broken requirements and all 13 Flask tests passed again. Browser checks were performed in the previous environment; the fresh environment has not been checked in a browser. This is a local demo, not a production deployment package.
