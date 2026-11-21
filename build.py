"""Build the WLD-CHILE-PEPPER interactive map.

    python build.py                 # -> outputs/<run_id>/map.html (+ checks, provenance), copied to docs/index.html
    python build.py --no-publish    # outputs/ only
    python build.py --version
"""
import argparse

from cs import __project__, __version__
from cs.config import load_config
from cs.provenance import Run, publish
from cs import data, geo, checks, render


def main():
    ap = argparse.ArgumentParser(description=f"{__project__} v{__version__}")
    ap.add_argument("--version", action="version", version=f"{__project__} {__version__}")
    ap.add_argument("--config", default="config/config.yaml")
    ap.add_argument("--no-publish", action="store_true", help="build into outputs/ only; leave the published page alone")
    args = ap.parse_args()

    cfg = load_config(args.config)
    keys = list(cfg["spotlights"])
    run = Run(cfg)
    print(f"{__project__} v{__version__} → {run.dir}")

    production = data.load_production(cfg["inputs"]["production_by_year"])
    makers = data.load_makers(cfg["inputs"]["makers"], keys)
    sauces = data.load_hot_ones_sauces(cfg["inputs"]["hot_ones_sauces"])
    counts = data.spotlight_counts(makers, keys)
    run.log_step("load", years=list(production),
                 producers_per_year={str(y): len(r) for y, r in production.items()},
                 maker_countries=len(makers), makers=sum(len(v) for v in makers.values()),
                 hot_ones_countries=len(sauces))

    topo = geo.load_topology(cfg["inputs"]["boundaries"])
    places = geo.countries(topo)

    join = checks.join_report(production, makers, sauces, places)
    cross = (checks.crosscheck_counts(cfg["inputs"]["by_country"], counts, sauces)
             + checks.crosscheck_hot_ones_makers(cfg["inputs"]["by_country"], makers)
             if cfg["inputs"].get("by_country") else [])
    checks.write_csv(join, run.dir / "join_report.csv")
    checks.write_csv(cross, run.dir / "crosscheck_report.csv")
    run.log_step("checks", join_issues=len(join), crosscheck_differences=len(cross))
    print(f"checks: {len(join)} join issues, {len(cross)} count differences")

    html = render.build_html(cfg, run.dir.name, topo, places, production, makers, sauces, counts)
    out = run.dir / "map.html"
    out.write_text(html, encoding="utf-8")
    run.log_step("map", output=out.name, size_mb=round(out.stat().st_size / 1e6, 2))
    print(f"map: {out} ({out.stat().st_size / 1e6:.2f} MB)")

    if cfg["run"].get("publish_dir") and not args.no_publish:
        print(f"published: {publish(run, out, cfg['run']['publish_dir'])}")


if __name__ == "__main__":
    main()
