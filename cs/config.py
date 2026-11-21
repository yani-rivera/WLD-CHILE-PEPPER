"""Load and validate the YAML config."""
from pathlib import Path
import yaml

REQUIRED = {
    "inputs": ["production_by_year", "makers", "hot_ones_sauces", "boundaries"],
    "map": ["title", "default_year", "default_spotlight", "default_measure", "colors"],
    "library": ["maplibre_version", "js_integrity", "css_integrity"],
}
MEASURE_KEYS = ["label", "field", "legend", "breaks"]
FIELDS = {"total_t", "dry_t", "green_t"}


def load_config(path: str | Path) -> dict:
    path = Path(path)
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    for section, keys in REQUIRED.items():
        missing = [k for k in keys if k not in (cfg.get(section) or {})]
        if missing:
            raise ValueError(f"config [{section}] missing: {missing}")
    measures = cfg.get("measures") or {}
    if not measures:
        raise ValueError("config [measures] needs at least one entry")
    for key, m in measures.items():
        if not str(key).isalpha():
            raise ValueError(f"measures.{key}: the key must be letters only (it prefixes map properties)")
        missing = [k for k in MEASURE_KEYS if k not in m]
        if missing:
            raise ValueError(f"measures.{key} missing: {missing}")
        if m["field"] not in FIELDS:
            raise ValueError(f"measures.{key}.field must be one of {sorted(FIELDS)}")
        if len(cfg["map"]["colors"]) != len(m["breaks"]) + 1:
            raise ValueError(f"measures.{key}.breaks needs exactly one entry fewer than map.colors")
        if list(m["breaks"]) != sorted(m["breaks"]):
            raise ValueError(f"measures.{key}.breaks must be in ascending order")
    if cfg["map"]["default_measure"] not in measures:
        raise ValueError("map.default_measure must be one of measures")
    if cfg["map"]["default_spotlight"] not in cfg["spotlights"]:
        raise ValueError("map.default_spotlight must be one of spotlights")
    cfg["_path"] = str(path.resolve())
    return cfg
