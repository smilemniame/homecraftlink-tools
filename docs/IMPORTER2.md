# Gate 2 / Importer 2 — images and resource URLs

Importer 2 extracts resource addresses from pasted HTML or text, displays image previews and lets you select URLs to copy, export or open in a slideshow. This guide describes the full HomeCraftLink interface. Importer 2 and its backend services are not bundled as a working feature in the table demo.

## Illustrated example and automatic transfer

[Try collecting images from the visual guide and see the Gate 2 result](https://homecraftlink.blogspot.com/2026/10/homecraftlink-quick-visual-guide.html#hcl-nav-5). The section includes a button you can run directly on the guide.

For other websites, install [numbered bookmark 2](../bookmarklets/open-importer-2.js), or drag a fresh bookmark 2 button from HomeCraftLink onto your bookmarks bar. Open a source page, let the images load, and click the saved bookmark. It opens Gate 2 in a new tab and transfers the current HTML directly, without clipboard permission or Ctrl+V. Keep the source page open until the import finishes. If the popup is blocked, allow it and run the bookmark again.

The numbered bookmark captures the page's `#search` element when present, otherwise its body. For adding content to an existing Gate 2 tab, use the copy-only DOM bookmark below.

## Collect page HTML without opening the importer

Use the [copy-only DOM bookmarklet](../bookmarklets/copy-page-html.js):

1. Open the linked file, click Raw and copy the entire line, including `javascript:`.
2. Create a browser bookmark named **DOM** and paste the code into its URL field.
3. Open a source page and let the images you want load. Scroll first if the page loads content as you browse.
4. Click the bookmark. It copies `document.documentElement.outerHTML` to the clipboard without opening HomeCraftLink.
5. Open Gate 2 and paste into the large input field with Ctrl+V. Pasting HTML starts extraction automatically.

This captures the current DOM markup, including changes already made by page scripts. It is not the original server response, a screenshot or a download of the image files. After successful copying, the current DOM bookmarklet confirms the content type and character count. If copying fails, it shows an error. Clipboard access may be blocked by browser permissions or page restrictions.

## Import and browse

The input accepts HTML or HTTP/HTTPS resource addresses. Extraction adds newly found URLs to the existing list and skips repeated URLs. Different sizes or variants of the same picture may have different URLs and appear separately; there is no visual duplicate detection.

The importer examines links, image sources, lazy-loading attributes, inline backgrounds and URL text. It classifies resources using address patterns and attempts to recognize additional images by loading them. It does not crawl the complete source website or guarantee that every image will be found.

| Control | Behavior |
| --- | --- |
| Thumbnail | Hover to enlarge the preview. |
| URL | Opens the resource in a new tab. |
| Show all / Images only | Switches between all resources and images. |
| Show others / Show images | Switches between other resources and images. |
| Page arrows | Browse pages of results. |
| Rows per page | Choose 10, 25, 50, 100, 250, 500 or 1000; the preference is stored locally. |
| Load CSV | Adds URLs from a text file with one resource address per line. |
| Clear image importer | Clears the imported list, input and selection. |

Image counts and previews depend on loading results and may change. The illustrated guide includes examples captured at different times: one shows 89 image entries; the direct-transfer example shows 88 resources, including 38 image entries. These are example counts, and image entries can include size variants of the same picture.

## Add images from several pages to the same list

1. Keep the HomeCraftLink tab containing your Gate 2 results open.
2. On another source page, let the images load and run the copy-only **DOM** bookmark.
3. After successful copying, return to that same HomeCraftLink tab, open Gate 2 if needed, and paste into its large input field with **Ctrl+V**.
4. Wait for extraction and repeat for further pages. Review the combined results before copying, exporting or starting a slideshow.

Each extraction appends newly found resource URLs to the existing list. Already stored URLs are skipped after URL cleanup and normalization. Different URLs for different sizes or variants can still produce separate entries; this is address deduplication, not visual image matching. Pasting the exact same HTML again is skipped.

Existing rows keep their stored selection state; newly added rows start unselected. Review your selection after adding content or switching resource filters. The clipboard holds the most recent successful copy; Gate 2 accumulates the results in the open tab. Use **Clear image importer** for a separate collection. Numbered bookmark 2 opens a new importer tab; use DOM and return to the existing tab to build on its list. Do not rely on the collection surviving a page reload or closing the tab.

## Select, copy and export

Use row checkboxes to select resources. With DataTables active, the header checkbox toggles checkboxes across pages of the currently rendered resource table, not only the visible page. Bulk actions collect selected URLs across those pages. Review the selection after switching resource filters.

| Action | Output |
| --- | --- |
| Copy beside a thumbnail | Copies that single image to the clipboard as PNG. |
| Copy selected to clipboard | Copies selected resource URLs as text, one per line. |
| Download selected CSV | Downloads selected URLs, one per line, without a header. |

Image copying uses the dimensions returned by the selected URL; it does not guarantee the largest original version. The frontend tries a direct image request, then the HomeCraftLink image proxy if that request fails. Browser clipboard support, source access and image decoding can affect success. A green check confirms completion; an error indicator means copying failed.

Bulk copying clears the selection after successful copying. CSV export asks for a filename without the extension, suggesting `images`; cancelling the prompt cancels export. The selection clears after triggering the download. CSV contains addresses, not embedded image files.

## External tools and slideshow

Edit with AI and Store image open external service websites. They do not automatically upload or paste an image. Copy an image first, then paste or upload it in the chosen service.

Slideshow selected opens a slideshow using selected resource URLs. Add Files opens a slideshow for local image files selected from disk. Download slideshow requests the separate `/download-slideshow` route; it is not the selected-URL CSV export. The slideshow page and download handler require separate documentation and are not included in the table demo.

## Documentation scope

This guide covers the inspected HomeCraftLink frontend and supplied screenshots. Accumulation and URL deduplication were checked against the updated `clipboard_paste.js`; DOM copy feedback and numbered bookmark 2 follow the current bookmarklet implementations. This documentation update did not include a new end-to-end browser test of accumulation or a backend proxy review. The screenshots illustrate thumbnail enlargement, selection and image-copy feedback.
