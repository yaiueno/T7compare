#!/usr/bin/env python3
"""抽出済み構造の重ね合わせとRMSD計算を担当するコンポーネント。"""

from __future__ import annotations

from extract_component import StructureEntry


def align_rmsd(cmd, mobile_obj: str, target_obj: str, method: str = "super") -> float:
    """指定メソッドで重ね合わせを行いRMSDを返す。"""
    mobile_sel = f"{mobile_obj} and name CA"
    target_sel = f"{target_obj} and name CA"

    if method == "align":
        result = cmd.align(mobile_sel, target_sel)
        return float(result[0])
    if method == "cealign":
        result = cmd.cealign(target_sel, mobile_sel)
        return float(result["RMSD"])

    result = cmd.super(mobile_sel, target_sel)
    return float(result[0])


def compare_to_known(
    cmd,
    known: StructureEntry,
    entries: list[StructureEntry],
    method: str = "super",
) -> list[dict[str, str | float | int]]:
    """known基準で各entryのRMSDを算出し、CSV用の行データを返す。"""
    rows: list[dict[str, str | float | int]] = []
    for entry in entries:
        rmsd = align_rmsd(cmd, entry.target_obj, known.target_obj, method=method)
        rows.append(
            {
                "group": entry.group,
                "label": entry.label,
                "chain": entry.chain_id,
                "protein_len": entry.protein_len,
                "rmsd_to_known": round(rmsd, 4),
                "output_pdb": str(entry.output_path),
            }
        )
    return rows
