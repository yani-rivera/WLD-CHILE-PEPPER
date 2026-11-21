# Changelog

Version lives in `cs/__init__.py`; printed by `python build.py --version` and stored in every
`provenance.json`.

## 0.2.0 — 2026-11-12
- Renamed to **WLD-CHILE-PEPPER** (was `chile_spotlight`); `__project__` and provenance carry the new name.
- **Measure switch:** "All peppers" (green + dry) or "Dry chillies only", each with its own classes (`measures` in
  the config, replacing `map.breaks`). Rank, share and "Who's next?" follow the selected measure.
- **Phone layout:** docked, fold-away controls; title strip with "i"; legend details and sources start folded;
  a tapped country is moved above the dock and its popup opens upward; attribution starts folded on phones.
- **Map library pinned** with Subresource Integrity hashes for the script and the stylesheet (`library` in the config).
- **Publish step:** each build also writes `docs/index.html` and `docs/provenance.json` (`run.publish_dir`;
  `--no-publish` to skip).
- "Who's next?" links work from the keyboard; flights use the country's label point for every country.
- Credit line carries the author's ORCID.
- Not tested on a physical phone; the unpkg copies of the library were not reachable from the build machine to
  confirm the hashes against the CDN (they were computed from the npm package, which unpkg serves).

## 0.1.1 — 2026-11-05
- Note under "Who's next?": absence from the spotlight lists isn't absence of heat
  (pickles, pastes, chilli oil; home markets).

## 0.1.0 — 2026-11-05
- First version: production choropleth 2020–2024 (year slider; Day 23 poster classes and colours),
  spotlight circles for Hot Ones, European chilli awards, TasteAtlas, Notes from the Road, Curated
  and All; country popups (production, rank, share, makers with places and sources, Hot Ones
  sauces by season); "Who's next?" list; Sources block.
- Joins on M49; join report and count cross-checks against `hot_sauce_by_country.csv`
  (0 issues, 0 differences on the 2026-10-08 inputs).
- Antimeridian fix for Russia and Fiji; name overrides (Türkiye, Czechia, Eswatini, North Macedonia).
