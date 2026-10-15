# Importer 3 — extract, read and translate text

Importer 3 (Gate 3 / Text & Audio Importer) turns pasted page HTML into editable text. You can listen to the text, translate it, copy it or save it as TXT.

## Quick start

1. Open a source article and let it load.
2. Run your saved bookmark 3 to copy the page HTML and open Gate 3. If automatic pasting is blocked, click the input field and press Ctrl+V.
3. Review the extracted text and remove anything you do not need.
4. Click **Read** to listen. Select a passage first to read only that passage.
5. Choose a target language and click **Translate**. You can read, copy or save the result.

You can also paste plain text or use **Load TXT**. HTML extraction runs when HTML is pasted; typing plain text does not require extraction.

## Example: NASA Space Place

Source: [Why Is the Sky Blue?](https://spaceplace.nasa.gov/blue-sky/en/).

The illustrated capture produced 3290 characters in English. A French translation contained 4015 characters. The French screenshot shows active playback at 16.6 seconds. These counts describe one capture, not a fixed expected result.

Extraction removes the visual page layout. In this example the output included image-caption and educator-resource text, omitted a three-item list and did not retain paragraph breaks. Always compare important content with the source; the result is not a complete or exact copy of the article.

## Reading controls

| Control | Action |
| --- | --- |
| Read | Read the selected passage, or the whole field if nothing is selected. |
| Pause / Resume | Pause or continue the current reading. |
| Stop | End playback, reset the timer and clear the reading selection. |
| Repeat | Repeat the text used for the current reading. |
| Speed | Choose 0.5–1.5×. Changing speed during playback restarts reading. |
| Chars | Number of characters in the current field. A red counter is not a hard length limit. |
| Scissors counter | Number of selected characters. |
| Read time | Elapsed playback time, not an estimate of the article's reading duration. |

The language badge and flag show the current language state. Language detection runs after text entry or import. The dropdown also changes the language used for reading: choose the language matching the visible text before pressing Read.

Voices come from the browser/device speech system and may differ between computers. If long Japanese passages fail to read, try selecting a shorter passage. Do not assume all voices work offline.

## Translation and returning to the original

1. Select a target language in the dropdown.
2. Click **Translate** and wait for completion.
3. The translated result replaces the text shown in the field.
4. To return to the preserved original, select its source language and click **Translate** again. Changing the dropdown alone does not restore the original.

**Reading selections do not restrict translation.** Translate uses the preserved source text when present, otherwise the current field. Subsequent target languages are translated from that source rather than deliberately chaining translations.

Manual editing establishes a new translation source. Save or copy text you want to keep before editing, clearing, importing another document or refreshing the page. For a separate document, use Clear first so a previously preserved source cannot be reused accidentally.

The menu offers EN, PL, DE, FR, ES, PT, IT, RU, JA and ZH. A menu entry does not guarantee that a particular translation pair is available.

Translation uses Chrome's built-in Translator API when available. First use may download a translation model, with progress shown below the controls. Reading is stopped when translation begins and cannot start while translation is in progress. Machine translation may contain errors; review the result.

This interface has no fixed 60000-character cap. Browser capabilities, model quotas, device resources and service limits can still affect large inputs.

## Files, clipboard and external tools

| Control | Action |
| --- | --- |
| Load TXT (folder) | Load a .txt file into the field. |
| Save TXT | Download the current text as text.txt. |
| Copy | Copy the current text as plain text to the clipboard. |
| Edit with AI | Open ChatGPT, Gemini, DeepSeek or Claude. Paste the text into that service yourself; opening it does not transfer the field automatically. |
| Clear (trash) | Clear the field, preserved source and messages, stop reading and reset the timer/language state. |

## Processing and availability

- Pasted HTML is sent to the website's extraction API.
- Language detection sends a sample of up to 500 characters to the website's language-detection API.
- The active translation button uses Chrome's Translator API.
- Reading uses the browser's speech system; voice availability and network requirements depend on the selected voice.

The complete workflow should not be described as wholly offline or as processing everything only on the device.

## Troubleshooting

- **Nothing pasted automatically:** focus Gate 3's input and press Ctrl+V. Clipboard access may need browser permission.
- **Extraction error or unwanted text:** try plain text instead, or edit the extracted result. Page structure and loaded content affect extraction.
- **Translation unavailable:** check the displayed message. Chrome's Translator API, a language pair or a required model may be unavailable on that device.
- **Wrong reading language:** choose the language matching the visible text and restart reading.
- **Copy failed:** allow clipboard access or select the text and copy it manually.

[Back to repository overview](../README.md)
