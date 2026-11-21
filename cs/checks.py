"""ABC checks: join coverage between data and boundaries, and spotlight counts
recomputed from makers_all versus the author's own by-country summary."""
import csv
from pathlib import Path

from .data import m49


def join_report(production: dict, makers: dict, sauces: dict, geo: dict) -> list[dict]:
    rows = []
    prod_codes = {c: v["country"] for yr in production.values() for c, v in yr.items()}
    for code, name in sorted(prod_codes.items()):
        if code not in geo:
            rows.append({"m49": code, "name": name, "table": "production",
                         "issue": "no boundary polygon (not drawn)"})
    for code, lst in sorted(makers.items()):
        if code not in geo:
            rows.append({"m49": code, "name": lst[0]["maker"] + " …", "table": "makers",
                         "issue": "no boundary polygon (circle not drawn)"})
    for code in sorted(sauces):
        if code not in geo:
            rows.append({"m49": code, "name": "", "table": "hot_ones_sauces",
                         "issue": "no boundary polygon"})
    return rows


def crosscheck_counts(by_country_path, counts: dict, sauces: dict) -> list[dict]:
    """Compare per-country counts recomputed here with hot_sauce_by_country.csv."""
    pairs = {  # column in by_country -> how we computed it
        "hot_ones_sauces": lambda code: len({s["sauce"] for s in sauces.get(code, [])}),
        "notes_from_the_road_count": lambda code: counts.get(code, {}).get("notes_from_the_road", 0),
        "european_awards_count": lambda code: counts.get(code, {}).get("european_awards", 0),
        "curated_count": lambda code: counts.get(code, {}).get("curated", 0),
    }
    out = []
    with Path(by_country_path).open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            code = m49(r["m49"])
            for col, fn in pairs.items():
                theirs = int(float(r[col] or 0))
                ours = fn(code)
                if theirs != ours:
                    out.append({"m49": code, "country": r["country"], "column": col,
                                "by_country": theirs, "recomputed": ours})
    return out


def crosscheck_hot_ones_makers(by_country_path, makers: dict) -> list[dict]:
    """Hot Ones maker names per country: makers_all vs hot_sauce_by_country."""
    out = []
    with Path(by_country_path).open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            code = m49(r["m49"])
            theirs = {x.strip() for x in (r.get("hot_ones_makers") or "").split(";") if x.strip()}
            ours = {e["maker"] for e in makers.get(code, []) if "hot_ones" in e["sources"]}
            if theirs != ours:
                out.append({"m49": code, "country": r["country"], "column": "hot_ones_makers",
                            "by_country": "; ".join(sorted(theirs - ours)),
                            "recomputed": "; ".join(sorted(ours - theirs))})
    return out


def write_csv(rows: list[dict], path):
    if not rows:
        Path(path).write_text("no issues\n", encoding="utf-8")
        return
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
