"""fachada de visualizacoes do projeto.

uso:
    python -m src.viz parte2
    python -m src.viz parte2 --out-dir out/parte2
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.parte2.build_visualizations import gerar_figuras_parte2

REPORT_PARTE2 = ROOT / "out" / "parte2_report.json"
EDGES_PARTE2 = ROOT / "data" / "dataset_parte2" / "Imdb_arestas.csv"
OUT_PARTE2 = ROOT / "out" / "parte2"
INTERFACE_ASSETS = ROOT / "interface" / "assets"


def _rodar_parte2(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    gerados = gerar_figuras_parte2(
        report_path=Path(args.report),
        edges_path=Path(args.edges),
        out_dir=out_dir,
        scatter_max=args.scatter_max,
    )

    # espelha em interface/assets para a interface web carregar.
    if args.mirror_interface:
        INTERFACE_ASSETS.mkdir(parents=True, exist_ok=True)
        for nome in gerados:
            shutil.copyfile(out_dir / nome, INTERFACE_ASSETS / nome)
        print(f"[viz] espelhado em {INTERFACE_ASSETS}")


def main() -> None:
    parser = argparse.ArgumentParser(description="gera figuras do projeto.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p2 = sub.add_parser("parte2", help="figuras da parte 2.")
    p2.add_argument("--report", default=str(REPORT_PARTE2))
    p2.add_argument("--edges", default=str(EDGES_PARTE2))
    p2.add_argument("--out-dir", default=str(OUT_PARTE2))
    p2.add_argument("--scatter-max", type=int, default=50000)
    p2.add_argument(
        "--no-mirror",
        dest="mirror_interface",
        action="store_false",
        help="nao copia os pngs pra interface/assets.",
    )
    p2.set_defaults(func=_rodar_parte2, mirror_interface=True)

    # parte1 e all entram aqui depois do merge.

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
