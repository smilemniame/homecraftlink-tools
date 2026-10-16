# Bookmarklets — 1, 2, 3, Links, DOM and Source

Six browser bookmarks connect the page you are viewing with the [HomeCraftLink importers](https://homecraftlink.com/top_sites).

**1, 2 and 3 open the corresponding importer. Links, DOM and Source copy content to the clipboard for you to paste manually.**

## Choose a bookmarklet

| Bookmark name | Code file | What it collects | What happens next |
| --- | --- | --- | --- |
| **1** | [open-importer-1.js](open-importer-1.js) | Unique HTTP/HTTPS link addresses from the current page DOM. | Opens Importer 1 and copies the links to the clipboard. |
| **2** | [open-importer-2.js](open-importer-2.js) | Current HTML from the page's `#search` element when present, otherwise its body. | Opens Importer 2 and attempts to transfer HTML directly. A clipboard fallback is available if transfer is not acknowledged. |
| **3** | [open-importer-3.js](open-importer-3.js) | HTML fetched again from the current page URL. | Attempts to copy the HTML, then opens Importer 3 for text extraction and audio work. |
| **Links** | [copy-links.js](copy-links.js) | Unique HTTP/HTTPS link addresses. | Copies the links; paste them into Importer 1. |
| **DOM** | [copy-page-html.js](copy-page-html.js) | The current document HTML, including changes already made by page scripts. | Copies the HTML; paste it into the appropriate HTML input in Importer 2 or 3. |
| **Source** | [copy-page-source.js](copy-page-source.js) | HTML fetched again from the current page URL. | Copies the HTML; paste it into the appropriate HTML input in Importer 2 or 3. |

The existing filename `copy-page-html.js` corresponds to the bookmark labelled **DOM**.

## Install the bookmarks

### From the website

1. Open [HomeCraftLink](https://homecraftlink.com/top_sites).
2. Show your browser's bookmarks bar.
3. Drag each numbered bookmarklet and each copy-only bookmarklet from the website onto the bar.
4. Arrange them as **1, 2, 3, Links, DOM, Source**.

Drag the actual bookmarklet buttons or links, rather than the address of the HomeCraftLink page.

### From these code files

1. Open the linked `.js` file above and use its **Raw** view to copy the complete code.
2. Create a browser bookmark or edit an existing bookmark.
3. Give it the corresponding name, such as **1** or **DOM**.
4. Replace the bookmark's URL/address with the complete code, starting with `javascript:`.
5. Save the bookmark.

The file link on GitHub opens the code. It does not install the bookmarklet. Keep the full code as one line and retain the `javascript:` prefix.

## Use the bookmarks

1. Open the source website and navigate to the content you want to collect.
2. Choose **1 / Links** for link addresses, **2** for images and resources from the current page HTML, or **3** for readable text from fetched HTML.
3. Click the saved bookmark on your bookmarks bar while the source page is active.
4. Allow clipboard access or the importer popup if the browser requests it.
5. In the importer, check that the expected content arrived. If the input is empty and copying succeeded, click its paste/input area and press **Ctrl+V**.
6. Review the result before selecting, exporting, editing or reading it aloud.

For **Links, DOM and Source**, open the importer yourself after copying and paste with **Ctrl+V**. Each successful copy replaces the current clipboard contents.

**Choose the bookmarklet to match the content you need.** A page may return some data even when you choose an unsuitable bookmarklet; that alone does not mean you collected the intended material.

Collection is not limited to the visible viewport. HTML and links may include navigation, footers, hidden elements or other page content. Conversely, content loaded only after scrolling or interaction may need to be loaded before collection. Always inspect the result.

## DOM versus Source

**DOM** captures the document as it currently exists in the browser. It can include changes made by scripts after the page loaded.

**Source** makes another request to the current URL. The response can differ from the page currently displayed and may omit content assembled later by JavaScript. Bookmarklet **3** uses this fetched-HTML approach too. DOM is a useful manual alternative when the desired text exists in the rendered page but is absent from fetched HTML.

Neither method packages the complete website with all its images, stylesheets and scripts. Relative resource addresses and externally loaded content can affect what an importer or HTML preview displays.

## If something does not arrive

- **Importer does not open:** check popup permissions. Bookmarklet 3 opens its tab after an asynchronous fetch/copy attempt, which some browser settings may block. You can open Importer 3 manually.
- **Importer opens with an empty input:** check clipboard permission, return to the source page and run the bookmarklet again. Paste with Ctrl+V if the content is in the clipboard. An opened importer alone does not confirm a successful copy.
- **Importer 2 does not receive HTML automatically:** allow its transfer attempt to finish. Its fallback attempts to copy HTML after about 10 seconds without acknowledgement; then paste manually. Alternatively, use DOM.
- **Links are missing or unrelated:** confirm you ran the bookmarklet on the intended page and that the links were already loaded. Menus and other additional links may also be collected.
- **Source misses visible content:** try DOM and paste the captured HTML manually. A fresh response may contain less than the rendered page.
- **Nothing happens on a special browser page:** try an ordinary HTTP/HTTPS website. Browser internal pages, extension pages and some restricted documents do not permit bookmarklets to operate normally.

Clipboard access, page restrictions and browser permissions can affect the result. Bookmark names can be edited locally; names and messages written into the code are not automatically translated by the browser.

## Detailed guides

- [Importer 1 — links](../docs/IMPORTER1.md)
- [Importer 2 — images and resources](../docs/IMPORTER2.md)
- [Importer 3 — text and audio](../docs/IMPORTER3.md)
- [HTML editor](../docs/HTML_EDITOR.md)
- [Repository overview](../README.md)
