"""Build the self-contained map.html from the prepared data."""
import json
import math
import re
from html import escape
from pathlib import Path

from shapely.geometry import mapping

from . import __project__, __version__
from .geo import _decode_arcs, _shape

TEMPLATE = Path(__file__).with_name("map_template.html")
EXCLUDE = {"010"}  # Antarctica: no data, takes a fifth of the map


def _clean(o):
    if isinstance(o, float):
        return None if not math.isfinite(o) else round(o, 2)
    if isinstance(o, (list, tuple)):
        return [_clean(x) for x in o]
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    return o


def _json(o) -> str:
    """Strict JSON, safe inside <script type="application/json">."""
    s = json.dumps(_clean(o), separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return s.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def country_features(topo: dict, production: dict, measures: dict, simplify: float = 0.02) -> dict:
    """GeoJSON countries with one property per measure and year (total2024, dry2024 …), for styling."""
    arcs = _decode_arcs(topo)
    feats = []
    for g in topo["objects"]["countries"]["geometries"]:
        code = g.get("id")
        if not code or code in EXCLUDE:
            continue
        shp = _shape(arcs, g)
        if shp is None or shp.is_empty:
            continue
        shp = shp.buffer(0).simplify(simplify, preserve_topology=True)
        geom = json.loads(json.dumps(mapping(shp)), parse_float=lambda x: round(float(x), 3))
        props = {"id": code}
        for yr, rows in production.items():
            for key, measure in measures.items():
                value = rows.get(code, {}).get(measure["field"])
                if value is not None and value > 0:
                    props[f"{key}{yr}"] = value
        feats.append({"type": "Feature", "properties": props, "geometry": geom})
    return {"type": "FeatureCollection", "features": feats}


def spotlight_points(geo: dict, counts: dict) -> dict:
    feats = []
    for code, c in counts.items():
        if code not in geo:
            continue
        lon, lat = geo[code]["label"]
        feats.append({"type": "Feature", "properties": {"id": code, **c},
                      "geometry": {"type": "Point", "coordinates": [lon, lat]}})
    return {"type": "FeatureCollection", "features": feats}


def build_html(cfg, run_id, topo, geo, production, makers, sauces, counts) -> str:
    m = cfg["map"]
    measures = cfg["measures"]
    countries = country_features(topo, production, measures)
    points = spotlight_points(geo, counts)
    # Natural Earth's short names, then FAOSTAT's for anything missing, then config overrides
    names = {code: v["name"] for code, v in geo.items()}
    for rows in production.values():
        for code, r in rows.items():
            names.setdefault(code, r["country"])
    names.update({str(k).zfill(3): v for k, v in (m.get("name_overrides") or {}).items()})
    settings = {
        "years": list(production),
        "defaultYear": m["default_year"],
        "defaultSpotlight": m["default_spotlight"],
        "defaultMeasure": m["default_measure"],
        "spotlights": cfg["spotlights"],
        "measures": {k: {"label": v["label"], "field": v["field"], "legend": v["legend"],
                         "breaks": v["breaks"], "note": v.get("note", "")} for k, v in measures.items()},
        "colors": m["colors"],
        "noData": m["no_data_color"],
        "ocean": m["ocean_color"],
        "circle": m["circle_color"],
    }
    detail = {
        "production": {str(y): rows for y, rows in production.items()},
        "makers": makers,
        "sauces": sauces,
        "counts": counts,
        "names": names,
        "labels": {code: list(v["label"]) for code, v in geo.items()},
    }
    srcs = cfg["sources"]
    sources_html = "".join(f"<li>{x}</li>" for x in [
        f"<b>Production:</b> {escape(srcs['production'])}",
        f"<b>Spotlight:</b> {escape(srcs['spotlight'])}",
        f"<b>Boundaries:</b> {escape(srcs['boundaries'])}",
        escape(m.get("credit", "")),
        f"Built with {escape(__project__)} v{escape(__version__)}, run {escape(run_id)}.",
    ] if x)
    values = {
        "__TITLE__": escape(m["title"]),
        "__SUBTITLE__": escape(m.get("subtitle", "")),
        "__LIB_VERSION__": escape(str(cfg["library"]["maplibre_version"])),
        "__LIB_JS_SRI__": escape(cfg["library"]["js_integrity"]),
        "__LIB_CSS_SRI__": escape(cfg["library"]["css_integrity"]),
        "__SOURCES__": sources_html,
        "__SETTINGS__": _json(settings),
        "__COUNTRIES__": _json(countries),
        "__POINTS__": _json(points),
        "__DETAIL__": _json(detail),
    }
    pattern = re.compile("|".join(re.escape(k) for k in values))
    return pattern.sub(lambda mt: values[mt.group(0)], TEMPLATE.read_text(encoding="utf-8"))
