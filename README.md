# WLD-CHILE-PEPPER

**Version 0.2.0** (2026-11-12) · see [CHANGELOG.md](CHANGELOG.md) · `python build.py --version`

Interactive companion map: **who grows the heat** (FAOSTAT chilli and pepper production,
2020–2024) and **who gets the spotlight** (hot-sauce makers in Hot Ones, European chilli awards,
TasteAtlas, Notes from the Road and a curated list), with a "Who's next?" list of the biggest
growers that no spotlight has reached yet.

World scope (`WLD`), no SDG prefix: chilli is a condiment, and no goal covers taste. Formerly `chile_spotlight` (v0.1.x).

Author: Yanira A. Rivera · ORCID [0000-0003-3309-5256](https://orcid.org/0000-0003-3309-5256)

Not a #30DayMapChallenge entry: the Day 23 poster is the entry, made by hand. This page was built
with AI-assisted code and says so in its credits.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python build.py                # builds, checks, and copies the page to docs/index.html
open docs/index.html
python build.py --no-publish   # builds into outputs/ only
```

**Publishing.** `docs/index.html` is the page GitHub Pages serves (Settings → Pages → branch `main`, folder `/docs`).
`docs/provenance.json` sits next to it and records the run that produced it. `outputs/` is kept out of git.

Each run writes to `outputs/<run_id>/`:

| File | What |
|---|---|
| `map.html` | the interactive map (one file; needs internet for the MapLibre library, which is pinned by integrity hash) |
| `config.yaml` | exact config used |
| `provenance.json` | versions, config hash, SHA-256 and pipeline versions of every input, step counts |
| `join_report.csv` | data rows without a boundary polygon (should say "no issues") |
| `crosscheck_report.csv` | spotlight counts recomputed from `makers_all.csv` vs `hot_sauce_by_country.csv` |

## Inputs (`data/`)

| File | From |
|---|---|
| `chile_producers_by_year.csv` | author's `chile_producers` pipeline (FAOSTAT QCL items 401 + 689) |
| `makers_all.csv`, `hot_ones_sauces_by_season.csv`, `hot_sauce_by_country.csv` | author's `hot_ones_sauces` pipeline |
| `countries-50m.json` | Natural Earth 4.1.0 via world-atlas 2.0.2 (public domain; licence file alongside) |

Countries join on **M49 codes** in both data and boundaries, so no name matching is involved.

## Notes

- **Two measures, switched on the page** (`measures` in the config): *All peppers* (green + dry, the Day 23 poster's
  classes on a log scale: < 5,100 · 5,100–31,600 · 31,600–120,000 · > 120,000 t) and *Dry chillies only* (item 689;
  classes are the rounded quartiles of the 2024 dry figures: 2,000 · 12,000 · 55,000 t). Dry is closer to hot chillies,
  since the total includes sweet peppers, but only about 56 countries report it. Rank, share and "Who's next?" follow
  the selected measure; share is of the total reported for that measure and year.
- Grey = no FAOSTAT figure for the selected measure in that year. Brazil, Russia, Mongolia, Angola, Chad,
  Mauritania, Afghanistan and Somalia have none in any year 2020–2024 (genuine gaps, not join errors).
- Circle size = number of **distinct makers** per country in the selected spotlight (area-proportional).
- Spotlight lists are curated selections, not a measure of sauce production or markets.
- Polygons crossing the 180° meridian (Russia, Fiji) are split so they don't wrap around the map.
- Display names: Natural Earth, with overrides in `config.yaml` (e.g. Türkiye, Czechia).
- **Phones:** the controls dock along the bottom edge and fold away ("Hide controls"); the title sits in a strip with
  an "i" for the subtitle; the circle legend, "Who's next?" and the sources start folded; a tapped country moves just
  above the dock so its popup opens into free map. Upright, a phone cannot show the whole world at once (a limit of
  the Mercator view), so the map is panned sideways; held sideways it fits.
- **Map library:** MapLibre GL JS, version and SHA-384 hashes in `library` in the config. To upgrade, change the
  version and recompute both hashes; the page will not load a file that does not match.

## Structure

```
build.py              CLI
config/config.yaml    settings (inputs, spotlights, measures and classes, map library, colours, sources, name overrides)
cs/config.py          load + validate config
cs/provenance.py      run folder + provenance.json (input hashes and their pipeline versions); publish to docs/
cs/data.py            read the author's tables, keyed by M49
cs/geo.py             TopoJSON decode, antimeridian fix, label points
cs/checks.py          join report, count cross-checks
cs/render.py          GeoJSON + data → map.html
cs/map_template.html  the page (MapLibre): layout, controls, popups
docs/                 the published page and its provenance (GitHub Pages)
```
