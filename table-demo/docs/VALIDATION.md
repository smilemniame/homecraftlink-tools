# Validation checklist

## Confirmed local demo checks

- Python syntax and required dependencies in the owner's existing environment.
- Flask full page, two pages, coffee and .org filters, two snapshots, empty results, suffix statistics, three static CSV resources, GET query rejection and POST header enforcement: 13 tests passed (report 000827).
- Preview startup on 127.0.0.1:5057 (report 000828).
- Browser scan: snapshot 202609, coffee filter, 20 results, page 2.
- Owner confirmed global dropdown counts of 2 and clipboard output for coffee2.example.com and coffee20.example.com.
- Fresh virtual-environment installation, pip check and all 13 Flask tests passed (report 000830).

## Repository package review — 16 October 2026

- Repository upload completed; the downloaded main-branch ZIP was inspected.
- The inspected package contained 35 files, including the table demo, seven feature guides and six bookmarklets with their usage guide.
- All 38 relative Markdown file links resolved to existing package files.
- Python and JavaScript syntax checks passed for the included code files.
- Numbered bookmarklets 1, 2 and 3, plus DOM and Source, matched the supplied website HTML.

This package review inspected files and syntax. It did not rerun the demo, reinstall dependencies, test external links or verify every live website feature.

## Pending checks

- Check the demo in a browser using the fresh virtual environment; the earlier browser checks used the previous environment.
- Recheck demo attribution in the rendered page after the documentation patch.

## Sample-data limitation

The two demo snapshots intentionally contain identical rankings; this validates switching and loading, not historical changes.

[Back to demo overview](../README.md)
