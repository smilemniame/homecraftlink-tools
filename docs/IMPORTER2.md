# Gate 2 / Importer 2 — images and resource URLs

Importer 2 extracts resource addresses from pasted HTML or text, displays image previews and lets you select URLs to copy, export or open in a slideshow. This guide describes the full HomeCraftLink interface. Importer 2 and its backend services are not bundled as a working feature in the table demo.

## Collect page HTML without opening the importer

Use the [copy-only HTML bookmarklet](../bookmarklets/copy-page-html.js):

1. Open the linked file, click Raw and copy the entire line, including `javascript:`.
2. Create a browser bookmark named "Copy page HTML" and paste the code into its URL field.
3. Open a source page and let the images you want load. Scroll first if the page loads content as you browse.
4. Click the bookmark. It copies `document.documentElement.outerHTML` to the clipboard without opening HomeCraftLink.
5. Open Gate 2 and paste into the large input field with Ctrl+V. Pasting HTML starts extraction automatically.

This captures the current DOM markup, including changes already made by page scripts. It is not the original server response, a screenshot or a download of the image files. The bookmarklet has no success popup; errors are logged to the browser console. Clipboard access may be blocked by browser permissions or page restrictions.

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

Image counts and previews depend on loading results and may change. The supplied example shows 89 imported images, not a fixed count for the source site.

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

Based on the owner's supplied `clipboard_paste.js` and screenshots reviewed on 15 October 2026. The JavaScript matched SHA256 `f19ed6a4279a168642f60a0c92a710bd36dee06c74ff2d879de5a4db287e0c21`. The screenshots show thumbnail enlargement, selection and a successful image-copy indicator. No new automated end-to-end test or backend proxy review was performed for this guide.
