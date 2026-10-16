# HTML editor and page bookmarks

The HTML editor lets you edit HTML on the left and inspect its rendered preview on the right. Use it for small examples or to inspect markup copied from a web page.

Open the editor on [HomeCraftLink](https://homecraftlink.com/top_sites/). This document describes the editor in the website; it is not a standalone editor download.

## Quick start

1. Open the HTML editor section.
2. Paste HTML into the left field, or use the folder button to load a local HTML file.
3. Edit the code. The preview updates as the field changes.
4. Use **Copy** to copy the current HTML when you are ready to use it elsewhere.

For a small example, paste:

```html
<h1>Hello World!</h1>
<p>Edit this sentence and watch the preview change.</p>
```

## Controls

| Control | Action |
| --- | --- |
| Folder / load HTML | Read a selected local file as text and replace the editor contents. |
| Copy | Copy the code from the left field to the clipboard. |
| Trash | Clear the code and update the preview. |
| Expand / Collapse | Switch the editor layout to give the preview more room, or restore the normal layout. |
| Links / DOM / Source | Copy content from the page where you run the saved bookmarklet; see below. |

Copy copies HTML code, rather than a screenshot or only the visible words. Keep a separate copy of work you need before clearing, loading another file or refreshing the page.

## Save the bookmarks

Drag the bookmarklets offered by HomeCraftLink onto your browser's bookmarks bar. Open a source page and click the saved bookmark there. A normal click on the HomeCraftLink page runs it on HomeCraftLink itself.

Use the bookmark matching the content you want. The result can include menus, captions and other page elements, and is not limited to the area currently visible on screen. Review the collected content before using it.

### Six bookmarks, two ways to work

| Bookmark | Purpose | What happens next |
| --- | --- | --- |
| 1 | Collect links for Importer 1. | Opens the importer; follow its prompt and paste with Ctrl+V if needed. |
| 2 | Collect page HTML for image extraction in Importer 2. | Opens the importer; follow its prompt and paste if needed. |
| 3 | Collect page HTML for text extraction in Importer 3. | Opens the importer; follow its prompt and paste if needed. |
| Links | Copy unique HTTP/HTTPS links, one per line. | Stay on the source page; return to Importer 1 and paste manually. |
| DOM | Copy the current document's HTML. | Stay on the source page; paste manually into the HTML editor or an HTML importer. |
| Source | Fetch the current page URL again and copy the returned HTML. | Stay on the source page; paste manually into the HTML editor or an HTML importer. |

The copy-only bookmarks do not open an importer. Automatic transfer for numbered bookmarks can depend on browser permissions and the source page. A successful copy or a nonempty result does not guarantee that the desired content was collected.

## DOM or Source?

**DOM** copies `document.documentElement.outerHTML`: the current page structure, including changes already made by scripts. Scroll and expand the content you need before copying. It does not automatically include the contents of embedded frames, shadow roots or every part of the page's live application state.

**Source** requests the page URL again with caching disabled and copies the response text. It does not serialize the current DOM. The returned HTML may differ from the page you are looking at, especially on dynamic sites.

Both copy markup, not a complete package of image files, stylesheets, scripts and other resources. Neither bookmark crawls the whole website.

## Use copied HTML

1. Open the source page and let the relevant content load.
2. Run **DOM** or **Source** from your bookmarks bar.
3. Return to HomeCraftLink and paste with Ctrl+V into the HTML editor.
4. Inspect or edit the code and its preview.
5. To extract images or text, copy the code and paste it into the appropriate importer yourself.

See [Importer 1](IMPORTER1.md), [Importer 2](IMPORTER2.md) and [Importer 3](IMPORTER3.md) for their extraction and export workflows.

## Preview limitations

The preview renders HTML in an iframe and adds a default black background with white text. Pasted markup can supply its own styling.

A copied website may look different because relative URLs, external resources and scripts depend on its original environment. The preview is not an exact reconstruction of the source website. Some resources may fail to load.

The preview uses `document.write` and is not a sanitization tool. Scripts and resource requests in supplied HTML may run or load in the preview. Use code you trust; do not treat this editor as an isolated environment for testing hostile HTML.

## Troubleshooting

- **Clipboard copy fails:** allow clipboard access when requested, or copy the code field manually.
- **Source returns unexpected HTML or fails:** the page may return a different response or restrict the request. Try DOM after the intended content has loaded.
- **Images or text are missing:** scroll or expand the source page before copying, then check the markup and extraction result. Copying HTML does not fetch every resource.
- **Preview differs from the original page:** check relative resource URLs and dependencies. This is expected for many complete websites.
- **Bookmark labels or alerts stay in English:** their text is defined in the bookmarklet code. You can rename a saved bookmark; the browser does not automatically translate its script messages.

[Back to repository overview](../README.md)
