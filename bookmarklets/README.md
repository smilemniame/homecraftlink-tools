# Bookmarklets — 1, 2, 3, Links, DOM and Source

Six browser bookmarks connect the page you are viewing with the [HomeCraftLink importers](https://homecraftlink.com/top_sites).

**1, 2 and 3 open the corresponding importer and transfer data directly, without using the clipboard. Links, DOM and Source copy content to the clipboard for you to paste manually.**

## Choose a bookmarklet

| Bookmark name | Code file | What it collects | What happens next |
| --- | --- | --- | --- |
| **1** | [open-importer-1.js](open-importer-1.js) | Unique HTTP/HTTPS link addresses from the current page DOM. | Opens Gate 1 and transfers links directly for automatic domain import. |
| **2** | [open-importer-2.js](open-importer-2.js) | Current HTML from the page's `#search` element when present, otherwise its body. | Opens Gate 2 and transfers HTML directly for image and resource extraction. |
| **3** | [open-importer-3.js](open-importer-3.js) | HTML fetched again from the current page URL. | Opens Gate 3 immediately, then transfers the fetched HTML for text extraction. |
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

### Automatic transfer: 1, 2 and 3

1. Open the source website and navigate to the content you want to collect. Load any images or text you need before running the bookmark.
2. Click **1** for link addresses, **2** for images and resources from the current page HTML, or **3** for text extracted from fetched HTML.
3. The corresponding Gate opens in a new HomeCraftLink tab. Allow the popup if your browser blocks it, then run the bookmark again.
4. Keep the source page open until the import finishes. The numbered bookmarks transfer data directly; clipboard permission and Ctrl+V are not needed for this transfer.
5. Check the import status and review the result before selecting, exporting, editing or reading it aloud. Gate 3 playback starts when you press Play.

If you installed an older numbered bookmark, replace its saved URL with the current code or drag a fresh button from HomeCraftLink onto your bookmarks bar. Updating the repository does not update bookmarks already saved in your browser.

### Manual copying: Links, DOM and Source

1. On the source page, click **Links** for link addresses, **DOM** for the current document HTML, or **Source** for freshly fetched HTML.
2. Allow clipboard access if the browser requests it. If copying fails, resolve the reported problem before pasting; your clipboard may still contain earlier content.
3. Open HomeCraftLink or switch to an existing HomeCraftLink tab. These three bookmarks do not open it automatically.
4. Open Gate 1 for Links, or the appropriate HTML input in Gate 2, Gate 3 or the HTML editor for DOM/Source, then paste with **Ctrl+V**.
5. Check and review the imported content. Each successful copy replaces the current clipboard contents.

**Choose the bookmarklet to match the content you need.** A page may return some data even when you choose an unsuitable bookmarklet; that alone does not mean you collected the intended material.

Collection is not limited to the visible viewport. HTML and links may include navigation, footers, hidden elements or other page content. Conversely, content loaded only after scrolling or interaction may need to be loaded before collection. Always inspect the result.

## DOM versus Source

**DOM** captures the document as it currently exists in the browser. It can include changes made by scripts after the page loaded.

**Source** makes another request to the current URL. The response can differ from the page currently displayed and may omit content assembled later by JavaScript. Bookmarklet **3** uses this fetched-HTML approach too. DOM is a useful manual alternative when the desired text exists in the rendered page but is absent from fetched HTML.

Neither method packages the complete website with all its images, stylesheets and scripts. Relative resource addresses and externally loaded content can affect what an importer or HTML preview displays.

## If something does not arrive

- **Importer does not open:** allow popups for the source website and run the numbered bookmark again. All three numbered bookmarks open the importer tab before waiting for transfer or fetching to finish.
- **Automatic import does not finish:** keep the source page open and check the status in the importer tab. If the source reports that transfer was not confirmed, check whether data arrived before trying again. The numbered bookmarks do not copy a fallback into the clipboard.
- **You need a manual alternative:** use Links for Gate 1, or DOM/Source for an HTML input in Gate 2 or Gate 3, then paste with Ctrl+V. Clipboard permissions apply to this separate copying step.
- **Links are missing or unrelated:** confirm you ran the bookmarklet on the intended page and that the links were already loaded. Menus and other additional links may also be collected.
- **Source misses visible content:** try DOM and paste the captured HTML manually. A fresh response may contain less than the rendered page.
- **Nothing happens on a special browser page:** try an ordinary HTTP/HTTPS website. Browser internal pages, extension pages and some restricted documents do not permit bookmarklets to operate normally.

Page restrictions, popup settings and browser permissions can affect the result. Clipboard permissions apply to the copy-only bookmarks and to copying results from the tools. Bookmark names can be edited locally; names and messages written into the code are not automatically translated by the browser.

## Illustrated examples

See the [six bookmarks overview](https://homecraftlink.blogspot.com/2026/10/homecraftlink-quick-visual-guide.html#hcl-nav-9) in the visual guide, or try the numbered bookmarks directly on the guide:

- [Gate 1: collect links and build a domain list](https://homecraftlink.blogspot.com/2026/10/homecraftlink-quick-visual-guide.html#hcl-nav-3)
- [Gate 2: collect and preview images](https://homecraftlink.blogspot.com/2026/10/homecraftlink-quick-visual-guide.html#hcl-nav-5)
- [Gate 3: extract, read and translate text](https://homecraftlink.blogspot.com/2026/10/homecraftlink-quick-visual-guide.html#hcl-nav-7)

## Detailed guides

- [Importer 1 — links](../docs/IMPORTER1.md)
- [Importer 2 — images and resources](../docs/IMPORTER2.md)
- [Importer 3 — text and audio](../docs/IMPORTER3.md)
- [HTML editor](../docs/HTML_EDITOR.md)
- [Repository overview](../README.md)
