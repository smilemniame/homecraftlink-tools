# Video.js player — local video and audio

Use the player on [HomeCraftLink](https://homecraftlink.com/top_sites/) to watch videos and listen to audio stored on your computer. Select files or a folder, then click a playlist title to play it.

This document describes the player embedded in the website. It is not a standalone player download.

## Quick start

1. Open the Video.js player section.
2. Click **Add Files** and select one or more local recordings. Alternatively, choose **Add Folder…** from its menu.
3. Click a title in the playlist to start playback.
4. Use Play / Pause, Previous / Next, the playback bar and volume controls.
5. The right column starts in **EQ** view. Click **PLAYLIST** to display the list, or **EQ** to return to the equalizer. The older **VIS** toolbar is currently hidden.

The selected files are opened through local browser object URLs. This player does not upload their contents to the server. Loading the website and its external libraries can still require network access; do not assume the complete application is available offline.

## File formats

The file-extension filter in the player accepts:

| Video | Audio |
| --- | --- |
| MP4, WebM, MKV | MP3, WAV, OGG, M4A |

An accepted extension does not guarantee playback. The browser and device must support the actual audio and video codecs inside the file. MKV in particular should not be treated as universally supported.

The file picker's `accept` setting currently lists MP4, MP3, WAV and OGG MIME types. If another accepted format is hidden, select **All files** in the system dialog where available, or try folder selection. Files with other extensions and names beginning with a dot are skipped by the import filter.

## Playlist

- **Add Files** appends selected recordings to the list and shows the playlist view.
- **Add Folder…** adds accepted media from the selected folder, including files supplied from its subfolders by the browser.
- Click a title to play that item. The active item is highlighted and brought into view.
- The header shows the selected item's position, the item count and the combined known duration. Duration totals update as metadata becomes available; unreadable items can contribute zero.
- Hover over a playlist title to reveal its **×** removal button. The header **×** clears the whole playlist.
- Removing an item does not delete the original file from your computer.

The importer skips duplicates based on the parsed performer and title. Separate files with matching parsed names may therefore be treated as duplicates.

The playlist lives in the current page session. Reloading the page clears it: select your local files again after a reload.

You can also drag files or folders onto the playlist area, or onto the EQ area while that view is displayed. Folder dropping depends on browser support. A local `file://` copy can handle dropping differently from the player served over HTTP by HomeCraftLink.

## Playback controls

| Control | Action |
| --- | --- |
| Play / Pause | Start or pause the current recording. |
| Previous / Next | Select and play an adjacent playlist item. These buttons wrap around at the ends. |
| Playback bar | Seek within the current recording. |
| VOL / mute | Adjust the 0–100% volume setting using the coloured slider. The number appears above its bar, and the speaker icon toggles mute. The VOL display is a setting, not a live signal meter. |
| BAL | Adjust the left/right channel balance from its centre position. |
| Speed | Choose 0.5, 0.75, 1, 1.25, 1.5 or 2×. The selected rate is reapplied when another file loads. |
| Full screen | Expand the player into full-screen view where available. |
| Picture-in-picture | Open a floating video window where supported by the browser and media. |

While focus is outside an input or textarea, **Left / Right arrows** seek backward or forward by five seconds, and **Space** toggles playback. Keyboard behavior can also depend on which player control has focus.

### ALL / 1 / MODE

Click the mode button to cycle through these behaviors:

| Label | At the end of the current recording |
| --- | --- |
| ALL | Play the next playlist item, wrapping back to the first after the last. |
| 1 | Restart the same recording. |
| MODE | Stop when the current recording ends; do not automatically advance. |

The initial mode is **ALL**. Previous and Next remain available in every mode.

## Equalizer

The equalizer and playlist occupy the same right-hand column. The button reads **PLAYLIST** while EQ is shown; click it to show the playlist, then **EQ** to return. They are alternative views, not overlapping panels.

The ten-band EQ has frequency sliders from **31 Hz to 16 kHz** and presets such as **Flat**, **Rock**, **Bass Boost**, **Vocal** and **Cinema**. Adjust the sliders manually or choose a preset. Flat resets band gains to zero.

The current implementation saves the preset label and the 60 Hz–16 kHz slider values in this browser's local storage. The 31 Hz slider is not included in that saved band list, so do not rely on its manual setting surviving a reload. Storage settings or clearing browser data can also remove saved EQ settings.

The EQ/Playlist toggle switches the right column between views. **Add Files** also brings the playlist into view so newly added recordings can be selected.

## Audio meters: stereo L/R, VU and Peak Hold

The EQ view shows separate **L/R stereo level bars** driven by the signal after the equalizer. Their moving fills and peak markers respond independently to each channel. **Peak Hold** briefly retains a recent maximum. The needle-style **VU indicators** follow signal movement rather than simply showing the maximum peak.

The level displays use green, yellow and red regions (approximately **66.7% / 18.3% / 15%**). The EQ area also has ten band-level visual overlays with peak markers. These displays help assess the signal but are not calibrated loudness or hearing-safety guarantees.

## Visualizations (VIS)

The older oscilloscope, circular and linear visualizations remain in the player code, but their **VIS toolbar is currently hidden**. There are no visible VIS buttons to activate in the current interface. This does not disable the EQ, stereo meters or VU indicators.

## Troubleshooting

- **A file does not appear:** check its extension and the file-picker filter. A matching parsed title and performer may already be in the playlist.
- **A file appears but does not play:** its container or codec may be unsupported. Try another recording known to play in the same browser.
- **Playback does not start automatically:** click a playlist title or Play; browser autoplay rules can require a user action.
- **No sound or inactive level meters:** check the current media, VOL/mute and whether playback has started. The VOL display shows the selected setting, not a measured audio level. The old VIS toolbar is deliberately hidden.
- **The playlist disappeared after refresh:** add the local files again; the player does not persist the playlist.
- **The duration total looks incomplete:** allow time for metadata to load. Unsupported or unreadable files may not provide a duration.

[Back to repository overview](../README.md)
