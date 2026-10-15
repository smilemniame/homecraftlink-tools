# Slideshow — selected images and local files

The HomeCraftLink slideshow displays a large image with a thumbnail strip, manual navigation, timed playback and click-to-zoom. This guide describes the full interface linked to [Importer 2](IMPORTER2.md). The slideshow is not bundled as a working feature in the table demo.

## Open a gallery

From Gate 2 / Importer 2:

1. Import image addresses and select the rows you want.
2. Choose **Slideshow selected** to open those addresses in a new slideshow tab.
3. Alternatively, choose **Add Files** and select local image files.

The selected-address route reads `slideshow_selected` from session storage. It is a temporary browser handoff, not a permanent saved gallery or shareable image list. Opening the selected-mode page without that data displays a message that no selected images are available.

## Controls

| Control | What it does |
| --- | --- |
| Previous / Next arrows | Move backward or forward through the gallery. |
| Left / Right arrow keys | Navigate through images. |
| Thumbnail | Jump directly to that image. |
| Image counter | Shows the current position and gallery total; the supplied screenshot shows 33 / 125. |
| Go to # number field | Enter an image number and confirm the change to jump there. Values are constrained to the gallery range. |
| Delay slider | Set 1–60 seconds between automatic image changes; 0 disables automatic playback. |
| Delay progress bar | Shows the remaining time against a fixed 60-second scale. It resets when the image changes. |
| Hide Thumbs / Show Thumbs | Hide or restore the thumbnail strip. The T key also toggles it. |
| Fullscreen button | Enter or leave full-screen view using the browser's fullscreen API. |
| Main image click | Toggle 2× zoom around the clicked point. Moving to another image resets the zoom. |

The delay setting is remembered in local storage. Changing it stops the previous playback cycle and starts a fresh one when the value is above zero. Manual navigation does not permanently disable timed playback. With more than one image, the gallery is configured to loop.

Keyboard shortcuts are handled at document level in the reviewed implementation. When editing the number field, remember that Left / Right and T are also gallery shortcuts.

## Load another set

Each load operation replaces the current gallery rather than appending to it.

| Control | Expected input |
| --- | --- |
| Load CSV | A plain text file containing one image URL per line. |
| Load Files | One or more local image files. |
| Load Folder | Images supplied by the browser's folder picker, where supported. |

For Load CSV, blank lines are ignored and surrounding whitespace is trimmed. This is a line-based URL reader, not a general CSV parser: do not include a header, quoted fields or extra columns.

Example file:

```text
https://example.com/images/photo-1.jpg
https://example.com/images/photo-2.jpg
```

The local-file and folder routes accept files whose browser-reported MIME type starts with `image/`. They create browser object URLs for display. The reviewed slideshow code does not upload those local image files to a server.

## Image availability and dependencies

Remote image addresses are loaded from their source websites. A URL may stop working or be blocked. An image that triggers a loading error is removed together with its thumbnail, and the gallery total is recalculated. This can reduce the count while browsing.

The supplied page loads Swiper 6.8.4 JavaScript and styles from the unpkg CDN. It therefore depends on those external assets being available; selecting local images alone does not make the page a fully self-contained offline package.

The separate **Download slideshow** control in Importer 2 requests `/download-slideshow`. Its backend handler and generated download contents were not inspected for this guide. The selected-URL CSV export and slideshow download are separate actions.

## Documentation scope

Based on the owner's supplied slideshow HTML and screenshot reviewed on 15 October 2026. The source was inspected for loading modes, navigation, delay handling, thumbnail toggling, fullscreen and zoom. The Blogger preview confirms the documentation layout, not an end-to-end test of every gallery control. No new automated slideshow test or download-handler review was performed.
