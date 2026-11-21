"""Provenance: run folder, script version, config copy, input hashes and the
pipeline versions recorded inside the input files themselves."""
import csv
import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __project__, __version__


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def input_pipeline_versions(path: str | Path) -> list[str]:
    """Distinct values of a `pipeline_version` column, if the CSV has one."""
    p = Path(path)
    if p.suffix != ".csv":
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        rows = csv.DictReader(f)
        if "pipeline_version" not in (rows.fieldnames or []):
            return []
        return sorted({r["pipeline_version"] for r in rows if r.get("pipeline_version")})


class Run:
    def __init__(self, cfg: dict):
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.dir = Path(cfg["run"]["output_dir"]) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(cfg["_path"], self.dir / "config.yaml")
        self.prov = {
            "run_id": run_id,
            "project": __project__,
            "script_version": __version__,
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "config_sha256": sha256(cfg["_path"]),
            "environment": {"python": sys.version.split()[0], "platform": platform.platform()},
            "inputs": {
                key: {
                    "path": path,
                    "sha256": sha256(path),
                    "pipeline_versions": input_pipeline_versions(path),
                }
                for key, path in cfg["inputs"].items()
            },
            "steps": [],
        }
        self.save()

    def log_step(self, name: str, **info):
        self.prov["steps"].append(
            {"step": name, "finished_utc": datetime.now(timezone.utc).isoformat(), **info})
        self.save()

    def save(self):
        (self.dir / "provenance.json").write_text(json.dumps(self.prov, indent=2, ensure_ascii=False),
                                                  encoding="utf-8")


def publish(run: "Run", page: Path, publish_dir: str | Path) -> Path:
    """Copy the built page and its provenance to the folder GitHub Pages serves (e.g. docs/)."""
    target = Path(publish_dir)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy(page, target / "index.html")
    run.log_step("publish", page=str(target / "index.html"), page_sha256=sha256(target / "index.html"))
    shutil.copy(run.dir / "provenance.json", target / "provenance.json")
    return target / "index.html"
