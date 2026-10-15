# Gate 1 / Importer 1 — domain lists

Importer 1 turns pasted links or a text file into a domain list that you can review, select, copy and export. This guide describes the full HomeCraftLink interface; Importer 1 is not bundled as a working feature in the table demo.

## Add domains

1. Open the green Gate 1 panel.
2. Paste domains, URLs, HTML or text containing links into the large input field. Pasting triggers automatic import.
3. For manually entered text, press Enter to import. Alternatively, use the file control to load a domain list.
4. Review the imported domains and available titles and status results.

The input field is cleared after a successful import. The imported table remains visible. The current implementation limits input to 2,000,000 characters, files to 5 MiB and extracted domain lists to 10,000 entries.

## Review and select

The table shows an Imported counter, page navigation, domain names, titles, analysis controls and status badges. It displays 10 rows per page.

Select individual domains with the checkboxes beside their rows. The header checkbox toggles the row checkboxes currently present in the table. Selections are tracked by domain and restored when pages are redrawn. Copy and export use the tracked selection, including selected domains from other pages.

Copy and export buttons are disabled when nothing is selected. Use Clear importer (the trash icon) to clear the importer.

## Copy and export

| Action | Output | Selection afterwards |
| --- | --- | --- |
| Copy selected to clipboard | Domain names separated by line breaks. | Cleared after successful copying. |
| Export selected to CSV | A downloaded file containing one domain per line, without a header, titles or status columns. | Cleared after triggering the download. |

CSV export asks for a file name. Its default is `domains_YYYY-MM-DD.csv`. Cancelling the name prompt cancels the export.

Example exported content:

```text
example.com
example.org
```

If clipboard access is unavailable or denied, follow the browser prompt and try again. The copy helper also includes a fallback copying method.

## Collect links with bookmark 1

Drag the bookmarklet marked 1 to your browser's bookmarks bar. On a source page, activate that bookmark to collect its HTTP/HTTPS links and open Importer 1. The importer attempts to read and import the copied links automatically. If automatic clipboard reading is blocked, paste manually into the input field with Ctrl+V.

The imported result is a domain list; it should not be treated as a complete archive of all pages on the source website.

## Interpret live results

Titles and status information depend on the responses returned by external websites. A status of 200 indicates a successful HTTP response, but that response can still contain a CAPTCHA, consent page or access-block message. It does not establish that the intended page content was accessible.

Results can change between runs. A row may show a 200 badge alongside a title describing a browser check or blocked request.

## Inspect a domain

Click the small arrow in a domain row to open its analysis. Click it again to close the panel.

| Control or field | Meaning |
| --- | --- |
| Server | IP address and available country, region, city and ISP information. IP geolocation describes infrastructure, may be approximate and does not identify the website owner's location. |
| Home links / External links | Two groups of addresses extracted from the analysed response. These lists are not a complete crawl of the website. |
| GRelated | Opens Google with a `related:domain` query. Results depend on Google; similar-site matches are not guaranteed. |
| GRelated IP | Opens a Google search for the displayed IP address. |
| Expand / Collapse | Expands or compacts both link lists. |

The supplied commons.wikimedia.org example shows 289 Home links and 402 External links. These are example response counts, not fixed totals. Counts and available information may change between requests. Analysis may be incomplete when a website returns a challenge, block page or unavailable response.

## Documentation scope

This guide is based on the owner's supplied `top_sites.html`, `main.20250720.js` and Importer 1 screenshot reviewed on 14 October 2026. It documents the inspected frontend behavior; no new end-to-end importer test was performed for this documentation.

The Open quicklinks and Download quicklinks controls are visible in the HTML, but their handlers were not found in the supplied JavaScript. Their behavior is outside the scope of this guide. The separate dropdown training example is not part of Importer 1 documentation.

## Copy links without opening the importer

Use the [copy-only bookmarklet](../bookmarklets/copy-links.js) to collect links without opening HomeCraftLink automatically.

1. Open the linked file and click Raw.
2. Copy the entire line, including the `javascript:` prefix.
3. Create a browser bookmark named "Copy links" and paste the code into its URL field.
4. Open a source page and click the bookmark.
5. Open Gate 1 and paste with Ctrl+V.

The bookmark copies unique HTTP/HTTPS link addresses from the currently loaded page, including navigation and external links. Importer 1 then extracts domains, so several links may produce the same domain. Clipboard permission may be required.
