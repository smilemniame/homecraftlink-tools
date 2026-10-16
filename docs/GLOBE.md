# Interactive globe — day, night, ISS and trading sessions

The globe on [HomeCraftLink](https://homecraftlink.com/top_sites/) combines an interactive Earth view with time-based lighting, ISS tracking, recorded country visits and calculated trading-session indicators.

This document describes the globe embedded in the website. It is not a standalone globe download.

## Quick start

1. Open the globe from the main page.
2. Drag the Earth to rotate the view and use the mouse wheel over the globe to zoom.
3. Open **Layers** to change the visible layers or automatic rotation.
4. Click a country visit flag or a trading-session row to focus the view on that location.
5. Open **ISS** to inspect station telemetry. Click the flag inside that panel to centre the view on the station.
6. Use **Close** to return to the main page.

## Real-time day and night

With **Day / Night R** enabled, the lighting is calculated from the current date and time rather than being a fixed decorative texture.

- **Terminator:** the boundary between the day and night sides of the Earth.
- **Solar zenith point / subsolar point:** the geographical location where the Sun is directly overhead.
- **Day-side illumination:** uses the same calculated Sun direction as the terminator and the zenith highlight.

The model updates immediately when enabled and then every **30 seconds**. It uses the device clock, so an incorrect system date or time can affect the display. These are calculated positions in a visualization, not live satellite photographs or a weather map.

### Lighting versus rotation

Automatic rotation changes the viewing angle. Its speed and direction controls do not change the real date or time used for solar lighting. A faster-spinning view does not make the day/night calculation run faster.

## Layers and view controls

| Control | Action |
| --- | --- |
| Day / Night R | Show or hide the calculated day/night layer. |
| Borders | Show or hide country borders. |
| Grid | Show or hide the coordinate grid. |
| Auto rotate | Enable or disable automatic rotation of the view. |
| Speed | Adjust the visual rotation speed. |
| Direction | Reverse the automatic rotation direction. |
| Reset | Reset the view rotation and return to the close zoom setting. |

The current mouse controls support dragging and wheel zoom. Availability on touch devices should be checked separately rather than assumed to match desktop controls.

## Clickable flags and markers

### Country visit flags

The flags beside the globe summarize recorded website visits by country. Each entry shows a country code and its recorded count.

- Hover over a flag to highlight its corresponding globe marker.
- Click a flag to turn the globe towards that country.
- The list is ordered by visit count and displays up to **60 countries**.

These are recorded country-level visit totals, not a list of people currently online. The page requests visit data on load; do not assume the visible totals continuously refresh. IP-based country assignments can be approximate.

### Trading-session flags and rows

Open **Trading Sessions** to see the configured centres, their local times and their calculated **OPEN / CLOSED** status. The current configuration tracks **20 centres**.

Click a city's row, including its flag, to focus the globe on that centre. Hovering highlights its marker. Keyboard users can focus a row and activate it with Enter or Space.

The summary shows how many tracked centres are currently scheduled open. The list and marker statuses refresh every **30 seconds**. Local time is formatted using each centre's configured timezone, including the browser's timezone rules for daylight saving.

These indicators are calculated from configured weekly windows and calendar exceptions. They are not live exchange connectivity, price or market-status feeds.

The supplied implementation contains holiday and early-close exceptions for 2026–2027, with a declared calendar end date of **2027-12-31**. This does not establish that every exceptional closure is covered. After that date the calendar needs review. The small on-screen note still says holidays will be added separately; that label lags behind the embedded calendar implementation.

### ISS flag

The flag inside the ISS telemetry panel relates to the station's displayed location, rather than website visit counts. Click it to centre the view on the station. Over international waters the display can use the UN flag.

## ISS tracking

The **ISS** panel lets you show or hide the station and inspect:

- altitude;
- speed;
- latitude and longitude;
- an approximate orbital-period label of 93 minutes.

The station position is requested from the Where the ISS at API. The orbit graphic provides context for the station display; it should not be treated as a precise future-pass prediction.

Tracking depends on the external service and network access. If an update fails, the display may remain at its last successful position. A moving globe alone does not prove that the ISS data is fresh.

## Your Connection

Expand **Your Connection** to view the public IP address and available location, coordinates, timezone, ISP and ASN information.

IP geolocation describes the connection and may differ from your physical location, particularly with VPNs, mobile networks or provider gateways. It is not GPS positioning.

## World population link

**World population — live counter** opens the external Worldometer population counter in a new tab. It is a link to that service, not a population value calculated by this globe.

## Dependencies and availability

The globe needs browser WebGL support and loads external resources, including rendering libraries, geographical border data, flag images and ISS telemetry. Country visit information comes from the HomeCraftLink backend.

Opening a copy of the HTML alone does not recreate those backend endpoints. A failed resource can affect an individual layer or panel even if the rest of the globe is visible.

## Troubleshooting

- **Blank globe:** check browser WebGL support and whether required scripts and resources loaded.
- **Lighting appears wrong:** check the device date and time, and confirm Day / Night R is enabled. Rotate the view to inspect another part of the Earth.
- **Country flags show Waiting for signal:** the backend may have no usable visit entries or the data request may have failed.
- **ISS is missing or stationary:** check that its layer is enabled and tracking data is available. A failed request can leave old telemetry on screen.
- **A trading status looks unexpected:** check the centre's local time, configured session windows and calendar exceptions. The indicator is schedule-based.
- **The globe keeps turning while inspecting a location:** turn off Auto rotate in Layers.

[Back to repository overview](../README.md)
