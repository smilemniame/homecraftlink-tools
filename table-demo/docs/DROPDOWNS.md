# Monthly snapshots and dropdown filters

This guide explains the domain table controls and the CSV files used by the local [Table Demo](../README.md). It also explains how the small demonstration differs from the full HomeCraftLink service.

## Controls at a glance

| Control | Purpose | What its numbers mean |
| --- | --- | --- |
| Month | Select the monthly domain snapshot shown in the table. | A snapshot identifier, displayed as a month. |
| Country | Choose a country-code domain suffix, such as `.pl` or `.uk`. | Suffix counts for the selected monthly snapshot. |
| Top names (this) | Select a word from the selected month's word statistics. | The word's count in that month's statistics. |
| Top names (all) | Select a word from the global word statistics. | In this demo: the number of monthly snapshots containing the word. In the full service: the sum of its monthly counts across the accumulated archive. |
| Categories | Browse predefined groups and select a keyword. | No statistical count; these are keyword groups. |

The monthly dropdown statistics describe the full snapshot. Filtering the table does not recalculate those statistics for the visible results.

## Selecting a month or filter

Selecting a month updates the table's active snapshot and returns pagination to page one. Country and Top names (this) load statistics for that snapshot.

Selecting a dropdown keyword updates the search query and requests the first page of matching domains in the active month. Top names (all) supplies keywords from the global list; it does not turn the table into an archive-wide search.

Categories contains parent groups and child keywords. Choose a child keyword to filter domain names. These groups do not inspect website content or verify that a website belongs to a topic.

Dropdowns remain open while selecting items inside them. Longer word lists are rendered in batches as the menu is scrolled. Clicking the Total rows control clears the search query and returns to the first page while keeping the selected month.

## CSV files

All paths below are relative to `table-demo/static/csv/`.

| File | Format | Used for |
| --- | --- | --- |
| `YYYYMM.csv` | No header; `rank,domain` rows. | The monthly domain table. |
| `YYYYMMp.csv` | Header `tld,count`, followed by suffix counts. | Monthly suffix statistics returned by `/api/prefix_stats?snapshot=YYYYMM`. |
| `word_counts_YYYYMM.csv` | Header `word,count`. | Top names (this). |
| `word_counts_global_rank.csv` | Header `word,total_count,months_present`. | Top names (all); this demo displays and sorts by the third column. |
| `categories.csv` | Header row; each data row starts with a category followed by its keywords. | Categories and their child menus. |

Country displays only two-letter suffixes from the supplied suffix statistics, sorted by count. It adds country labels and flags; `.uk` uses the GB flag. The demonstration contains only `example.com` and `example.org` domains, so it has no country-code entries to show in this menu.

Top names (this) loads the monthly word CSV, sorts entries by count and renders them in batches of 150. Top names (all) loads the global CSV, sorts by `months_present` and renders batches of 500. Categories loads its groups and keywords from `categories.csv`.

These files supply precomputed statistics. The frontend reads them; it does not generate the monthly or global counts. This package does not include the full service's statistics-building pipeline.

## Demo versus the full service

The demonstration includes two snapshots, `202609` and `202610`, with the same 40 synthetic domains. Its monthly word menu contains 20 coffee names and 20 tea names. Changing between these sample months intentionally shows the same domain data.

The global CSV separates two measures:

- `total_count`: the sum of the monthly counts.
- `months_present`: the number of monthly snapshots in which the word appears.

For the demo's coffee and tea samples, these values are 40 and 2 respectively. The bundled JavaScript displays **2**, using `months_present`.

The owner's full service instead displays the **sum of monthly word counts** in Top names (all), as confirmed by the owner for the archive containing 92 months at the time of documentation. A domain present in several months can contribute in each month, so this aggregate is not a count of distinct domains across the archive. Adding another month can extend the accumulated total.

Screenshots from the full service therefore illustrate the real interface and larger statistics, but their All badges do not have the same meaning as the demo's All badges.

The demo also disables outgoing backend HTTP requests. Live titles, status checks and IP/GEO analysis are outside its scope. See the [demo README](../README.md) for setup instructions and limitations.

## Relevant implementation files

- [`templates/top_sites_fast.html`](../templates/top_sites_fast.html): table controls and dropdown containers.
- [`static/js/table_fast.js`](../static/js/table_fast.js): table requests, filter selection, pagination, global words and categories.
- [`static/js/country_dropdown_refresh.js`](../static/js/country_dropdown_refresh.js): monthly Country and Top names (this) refresh logic, including protection against outdated responses after switching months.

For installation and validation results, see the [README](../README.md) and [validation notes](VALIDATION.md).
