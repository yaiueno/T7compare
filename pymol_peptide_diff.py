#!/usr/bin/env python3
"""known + AF2セットからポリメラーゼを抽出してRMSD比較するCLI。"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

from compare_component import compare_to_known
from extract_component import StructureEntry, load_and_extract_polymerase
from io_component import ensure_dir, resolve_files


_DLL_HANDLES = []


def _configure_windows_pymol_dll_dirs() -> None:
    """WindowsでPyMOL依存DLLの探索先を追加する。"""
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return

    candidate_dirs: list[Path] = []

    env_dirs = os.environ.get("PYMOL_DLL_DIR", "").strip()
    if env_dirs:
        for item in env_dirs.split(";"):
            item = item.strip()
            if item:
                candidate_dirs.append(Path(item))

    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        candidate_dirs.append(Path(local_app_data) / "Schrodinger" / "PyMOL2" / "Library" / "bin")

    for dll_dir in candidate_dirs:
        if dll_dir.is_dir():
            try:
                _DLL_HANDLES.append(os.add_dll_directory(str(dll_dir)))
            except OSError:
                continue


_configure_windows_pymol_dll_dirs()

try:
    import pymol2
except ImportError as exc:
    raise SystemExit(
        f"pymol2 の読み込みに失敗しました: {exc}\n"
        "Python環境に pymol2 が無いか、依存DLLが不足しています。"
    ) from exc

#レビュー済み　上野 2026-04-14　コマンドライン引数解析
def parse_args() -> argparse.Namespace:
    """CLI引数を定義・解析する。"""
    parser = argparse.ArgumentParser(description="T7ポリメラーゼ抽出とRMSD比較")
    parser.add_argument("--known", required=True, help="既知構造 (cif/pdb)")
    parser.add_argument("--set1", nargs="+", required=True, help="AFセット1のglob")
    parser.add_argument("--set2", nargs="+", required=True, help="AFセット2のglob")
    parser.add_argument("--out_dir", required=True, help="出力ディレクトリ")
    parser.add_argument("--known_chain", default=None, help="known側chain固定")
    parser.add_argument("--pred_chain", default=None, help="予測側chain固定")
    parser.add_argument("--min_polymerase_len", type=int, default=400, help="自動判定の最小長")
    parser.add_argument("--align_method", choices=["super", "align", "cealign"], default="super")
    return parser.parse_args()


def write_summary_csv(out_csv: Path, rows: list[dict[str, str | float | int]]) -> None:
    """比較結果をCSVに保存する。"""
    with out_csv.open("w", newline="", encoding="utf-8") as fw:
        writer = csv.DictWriter(
            fw,
            fieldnames=["group", "label", "chain", "protein_len", "rmsd_to_known", "output_pdb"],
        )
        writer.writeheader()
        writer.writerows(rows)


def extract_group_entries(
    cmd,
    files: list[Path],
    group: str,
    output_dir: Path,
    pred_chain: str | None,
    min_polymerase_len: int,
) -> list[StructureEntry]:
    """指定グループのファイル群から抽出結果をまとめて返す。"""
    entries: list[StructureEntry] = []
    for file_path in files:
        entries.append(
            load_and_extract_polymerase(
                cmd,
                file_path,
                group,
                output_dir,
                forced_chain=pred_chain,
                min_polymerase_len=min_polymerase_len,
            )
        )
    return entries


def main() -> int:
    """処理全体を実行する。"""
    args = parse_args()

    known_file = Path(args.known)
    if not known_file.is_file():
        raise SystemExit(f"[ERROR] known が見つかりません: {known_file}")

    set1_files = resolve_files(args.set1)
    set2_files = resolve_files(args.set2)
    if not set1_files:
        raise SystemExit("[ERROR] set1 に入力ファイルがありません。")
    if not set2_files:
        raise SystemExit("[ERROR] set2 に入力ファイルがありません。")

    out_dir = ensure_dir(Path(args.out_dir))
    polymerase_dir = ensure_dir(out_dir / "polymerase")

    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.reinitialize()

        known_entry = load_and_extract_polymerase(
            cmd,
            known_file,
            "known",
            polymerase_dir,
            forced_chain=args.known_chain,
            min_polymerase_len=args.min_polymerase_len,
        )

        entries: list[StructureEntry] = []
        entries.extend(
            extract_group_entries(
                cmd,
                set1_files,
                "set1",
                polymerase_dir,
                pred_chain=args.pred_chain,
                min_polymerase_len=args.min_polymerase_len,
            )
        )
        entries.extend(
            extract_group_entries(
                cmd,
                set2_files,
                "set2",
                polymerase_dir,
                pred_chain=args.pred_chain,
                min_polymerase_len=args.min_polymerase_len,
            )
        )

        rows = compare_to_known(cmd, known_entry, entries, method=args.align_method)
        write_summary_csv(out_dir / "summary_rmsd_to_known.csv", rows)

        cmd.group("polymerase", "*_pol")
        cmd.hide("everything", "all")
        cmd.show("cartoon", "*_pol")
        cmd.color("gray70", known_entry.target_obj)
        cmd.color("cyan", "set1_*_pol")
        cmd.color("magenta", "set2_*_pol")
        cmd.orient("*_pol")
        cmd.save(str(out_dir / "polymerase_compare_session.pse"))

    print("[INFO] 完了")
    print(f"  known: {known_file}")
    print(f"  set1 : {len(set1_files)} files")
    print(f"  set2 : {len(set2_files)} files")
    print(f"  out  : {out_dir}")
    print("  - summary_rmsd_to_known.csv")
    print("  - polymerase_compare_session.pse")
    print("  - polymerase/*.pdb")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
