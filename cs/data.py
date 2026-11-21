"""Read the author's input tables into plain dictionaries keyed by 3-digit M49 code."""
import csv
from collections import defaultdict
from pathlib import Path


def m49(code) -> str:
    """'36' / '036' / 36.0 -> '036'."""
    s = str(code).strip()
    if not s:
        return ""
    return f"{int(float(s)):03d}"


def _num(x):
    x = (x or "").strip()
    return float(x) if x else None


def _rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def load_production(path) -> dict:
    """{year: {m49: {country, dry_t, green_t, total_t, rank, share}}}"""
    out: dict = defaultdict(dict)
    for r in _rows(path):
        out[int(r["year"])][m49(r["m49"])] = {
            "country": r["country"],
            "dry_t": _num(r["dry_t"]),
            "green_t": _num(r["green_t"]),
            "total_t": _num(r["total_t"]),
            "rank": int(float(r["rank"])) if r.get("rank") else None,
            "share": _num(r["world_share_pct"]),
        }
    return dict(sorted(out.items()))


def load_makers(path, spotlight_keys) -> dict:
    """{m49: [{maker, place, sources:[...]}]} — one entry per maker (distinct by name)."""
    out: dict = defaultdict(dict)
    for r in _rows(path):
        code = m49(r["m49"])
        if not code:
            continue
        sources = [s.strip() for s in (r.get("listed_in") or "").split(";") if s.strip()]
        unknown = [s for s in sources if s not in spotlight_keys]
        if unknown:
            raise ValueError(f"makers_all: unknown listed_in {unknown} for {r['maker']}")
        entry = out[code].setdefault(r["maker"], {"maker": r["maker"], "place": r.get("place") or "",
                                                  "sources": []})
        for s in sources:
            if s not in entry["sources"]:
                entry["sources"].append(s)
    return {k: sorted(v.values(), key=lambda e: e["maker"].lower()) for k, v in out.items()}


def load_hot_ones_sauces(path) -> dict:
    """{m49: [{season, sauce, maker}]} sorted by season."""
    out: dict = defaultdict(list)
    for r in _rows(path):
        code = m49(r["m49"])
        if not code:
            continue
        season = int(float(r["season"])) if r.get("season") else None
        out[code].append({"season": season, "sauce": r["sauce"], "maker": r["maker"]})
    for v in out.values():
        v.sort(key=lambda x: (x["season"] or 0, x["sauce"]))
    return dict(out)


def spotlight_counts(makers: dict, spotlight_keys) -> dict:
    """{m49: {source: n_distinct_makers, ..., 'all': n}}"""
    out = {}
    for code, lst in makers.items():
        c = {k: sum(1 for e in lst if k in e["sources"]) for k in spotlight_keys}
        c["all"] = len(lst)
        out[code] = c
    return out
