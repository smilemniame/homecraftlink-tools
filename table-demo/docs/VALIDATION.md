# Validation checklist

Confirmed:
- Python syntax and required dependencies in the existing environment.
- Flask full page, two pages, coffee and .org filters, two snapshots, empty results, suffix statistics, three static CSV resources, GET query rejection and POST header enforcement: 13 tests passed (report 000827).
- Preview startup on 127.0.0.1:5057 (report 000828).
- Browser scan: snapshot 202609, coffee filter, 20 results, page 2.
- Owner confirmed global dropdown counts of 2 and clipboard output for coffee2.example.com and coffee20.example.com.

Additional confirmation:
- Fresh-environment installation and backend tests passed (report 000830).

Pending:
- Confirmed in report 000830: fresh virtual-environment installation, pip check and all 13 Flask tests passed.
- Recheck demo attribution after the documentation patch.
- Package review and repository upload.

The two demo snapshots intentionally contain identical rankings; this validates switching and loading, not historical changes.
