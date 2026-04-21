from __future__ import annotations

import csv
from pathlib import Path


def load_imdb_primary_title_map(path: Path | str) -> dict[str, str]:
    caminho = Path(path)
    out: dict[str, str] = {}
    with open(caminho, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames:
            cols = {(x or "").strip() for x in reader.fieldnames if x}
            req = {"tconst", "primaryTitle"}
            if not req <= cols:
                raise ValueError(f"CSV deve conter colunas {req}; tem {cols}")
        for row in reader:
            tc = (row.get("tconst") or "").strip()
            if not tc:
                continue
            titulo = row.get("primaryTitle") or ""
            if titulo.strip() == r"\N":
                titulo = ""
            out[tc] = titulo.strip()
    return out
