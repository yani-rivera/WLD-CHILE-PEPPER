"""Natural Earth (world-atlas TopoJSON) helpers: decode, names, label points."""
import json
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Polygon, MultiPolygon, box


def load_topology(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _decode_arcs(topo: dict) -> list:
    """Quantized, delta-encoded TopoJSON arcs -> absolute lon/lat coordinates."""
    t = topo.get("transform")
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            if t:
                x, y = x + dx, y + dy
                pts.append((x * t["scale"][0] + t["translate"][0], y * t["scale"][1] + t["translate"][1]))
            else:
                pts.append((dx, dy))
        arcs.append(pts)
    return arcs


def _ring(arcs: list, idx: list) -> list:
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else list(reversed(arcs[~i]))
        pts.extend(a if not pts else a[1:])
    return pts


WORLD = box(-180, -90, 180, 90)


def _fix_antimeridian(poly: Polygon) -> list[Polygon]:
    """A ring that jumps across ±180° (Russia's Chukotka, Fiji) would be drawn as a
    band around the whole globe. Unwrap it to 0..360, then cut it back into the
    [-180, 180] world on both sides."""
    xs = [x for x, _ in poly.exterior.coords]
    if not any(abs(a - b) > 180 for a, b in zip(xs, xs[1:])):
        return [poly]
    shift = lambda ring: [((x + 360) if x < 0 else x, y) for x, y in ring]
    unwrapped = Polygon(shift(poly.exterior.coords), [shift(r.coords) for r in poly.interiors]).buffer(0)
    east = unwrapped.intersection(WORLD)
    west = translate(unwrapped.intersection(box(180, -90, 540, 90)), xoff=-360)
    parts = []
    for g in (east, west):
        if g.is_empty:
            continue
        parts.extend(g.geoms if hasattr(g, "geoms") else [g])
    return [p for p in parts if isinstance(p, Polygon) and not p.is_empty]


def _shape(arcs, geom):
    if geom["type"] == "Polygon":
        groups = [geom["arcs"]]
    elif geom["type"] == "MultiPolygon":
        groups = geom["arcs"]
    else:
        return None
    polys = []
    for p in groups:
        rings = [_ring(arcs, r) for r in p]
        polys.extend(_fix_antimeridian(Polygon(rings[0], rings[1:])))
    return polys[0] if len(polys) == 1 else MultiPolygon(polys)


def countries(topo: dict, object_name: str = "countries") -> dict:
    """{m49: {'name': str, 'label': (lon, lat)}} for every feature with an id.
    Label point = a point inside the largest polygon (so France's label is in France,
    not in the ocean between its territories)."""
    arcs = _decode_arcs(topo)
    out = {}
    for g in topo["objects"][object_name]["geometries"]:
        code = g.get("id")
        shp = _shape(arcs, g)
        if not code or shp is None or shp.is_empty:
            continue
        main = max(shp.geoms, key=lambda p: p.area) if isinstance(shp, MultiPolygon) else shp
        pt = main.buffer(0).representative_point()
        out[code] = {"name": (g.get("properties") or {}).get("name", code),
                     "label": (round(pt.x, 3), round(pt.y, 3))}
    return out
