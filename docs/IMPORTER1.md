# Gate 1 / Importer 1 — domain lists

Importer 1 turns pasted links or a text file into a domain list that you can review, select, copy and export. This guide describes the full HomeCraftLink interface; Importer 1 is not bundled as a working feature in the table demo.

## Illustrated examples

- [Collect links from the visual guide and see the Gate 1 result](https://homecraftlink.blogspot.com/2026/10/homecraftlink-quick-visual-guide.html#hcl-nav-3). This section includes a button you can try directly on the guide.
- [Inspect a domain: illustrated analysis example](https://homecraftlink.blogspot.com/2026/10/homecraftlink-quick-visual-guide.html#hcl-nav-4).

## Add domains

1. Open the green Gate 1 panel.
2. Paste domains, URLs, HTML or text containing links into the large input field. Pasting triggers automatic import.
3. For manually entered text, press Enter to import. Alternatively, use the file control to load a domain list.
4. Review the imported domains and available titles and status results.

The input field is cleared after a successful import. The imported table remains visible. The current implementation limits input to 2,000,000 characters, files to 5 MiB and extracted domain lists to 10,000 entries.

## Add more links to the same list

You can collect links from several source pages into one Gate 1 list without clearing its earlier results:

1. Keep the HomeCraftLink tab containing your current Gate 1 results open.
2. On another source page, run the copy-only **Links** bookmark. After successful copying, return to that same HomeCraftLink tab.
3. Open Gate 1 if its panel is collapsed and paste into its input field with **Ctrl+V**. Pasting starts the next import automatically.
4. Repeat for further pages, then review and select domains from the combined list.

Each import merges the extracted domains with the existing list, removes duplicate domain entries and sorts the combined list alphabetically. Several different URLs can resolve to the same domain entry. For example, if the list already contains `example.com` and the next paste contains `example.com` and `example.org`, the combined list contains those two domains once each.

**A new import clears the current checkbox selections, while keeping the accumulated domain list.** Finish collecting before making your final selection for copying or CSV export. The clipboard holds only the most recent successful copy; the importer performs the accumulation.

Use **Clear importer** (the trash icon) when you want a separate list. Keep using the same open tab for accumulation; numbered bookmark 1 opens a new importer tab. Do not rely on the list surviving a page reload or closing the tab.

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

Install the [numbered bookmark 1](../bookmarklets/open-importer-1.js) on your bookmarks bar, or drag a fresh bookmark 1 button from HomeCraftLink. Run it on a source page to collect HTTP/HTTPS links. It opens Gate 1 in a new tab and transfers the links directly for automatic import, without using the clipboard. Keep the source page open until the import finishes. If the popup is blocked, allow it for the source page and run the bookmark again. For adding links to a Gate 1 tab you already have open, use the copy-only Links bookmark described below.

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

This guide covers the inspected HomeCraftLink frontend. The accumulation, duplicate handling and selection-reset notes were checked against the updated `main.20250720.js`; the numbered bookmark 1 description follows the current direct-transfer implementation. This documentation update did not include a new end-to-end browser test of accumulation. Importer 1 is not included as a runnable feature in the table demo.

The Open quicklinks and Download quicklinks controls are visible in the HTML, but their handlers were not found in the supplied JavaScript. Their behavior is outside the scope of this guide. The separate dropdown training example is not part of Importer 1 documentation.

## Copy links without opening the importer

Use the [copy-only bookmarklet](../bookmarklets/copy-links.js) to collect links without opening HomeCraftLink automatically.

1. Open the linked file and click Raw.
2. Copy the entire line, including the `javascript:` prefix.
3. Create a browser bookmark named "Copy links" and paste the code into its URL field.
4. Open a source page and click the bookmark.
5. Open Gate 1 and paste with Ctrl+V.

The bookmark copies unique HTTP/HTTPS link addresses from the currently loaded page, including navigation and external links. Importer 1 then extracts domains, so several links may produce the same domain. Clipboard permission may be required.
