#!/usr/bin/env python3
"""構造ファイル1件から対象chain（主にポリメラーゼ）を抽出するコンポーネント。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional

from chain_split_component import chain_profiles, safe_chain_name

#レビュー済み　上野 2026-04-14　オブジェクトとして構造体を定義
@dataclass
class StructureEntry:
    """抽出した構造1件のメタ情報。"""

    label: str
    group: str
    source_path: Path
    source_obj: str
    target_obj: str
    chain_id: str
    protein_len: int
    output_path: Path

#レビュー済み　上野 2026-04-14　PyMOLオブジェクト名を安全な形式へ変換する。
def sanitize_name(text: str) -> str:
    """文字列をPyMOLオブジェクト名として安全な形式へ変換する。"""
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", text)
    if not name:
        name = "obj"
    if name[0].isdigit():
        name = f"o_{name}"
    return name

#レビュー済み　上野 2026-04-14　ポリメラーゼchainを決定する（指定優先、未指定なら最長側）。
def pick_polymerase_chain(cmd, obj_name: str, forced_chain: Optional[str], min_len: int) -> tuple[str, int]:
    """ポリメラーゼchainを決定する（指定優先、未指定なら最長側）。"""
    profiles = chain_profiles(cmd, obj_name)
    proteins = [
        (str(item["chain"]), int(item["protein_len"]))
        for item in profiles
        if int(item["protein_len"]) > 0
    ]

    if not proteins:
        raise ValueError(f"{obj_name}: タンパク質chainが見つかりません。")

    if forced_chain:
        for chain_id, length in proteins:
            if chain_id == forced_chain:
                return chain_id, length
        raise ValueError(f"{obj_name}: 指定chain '{forced_chain}' が見つかりません。")

    long_candidates = [item for item in proteins if item[1] >= min_len]
    if long_candidates:
        long_candidates.sort(key=lambda x: x[1], reverse=True)
        return long_candidates[0]

    proteins.sort(key=lambda x: x[1], reverse=True)
    return proteins[0]


def load_and_extract_polymerase(
    cmd,
    file_path: Path,
    group: str,
    out_dir: Path,
    forced_chain: Optional[str],
    min_polymerase_len: int,
) -> StructureEntry:
    """1ファイル読み込み→ポリメラーゼ抽出→PDB保存を行う。"""
    label = file_path.stem
    source_obj = sanitize_name(f"{group}_{label}_src")
    target_obj = sanitize_name(f"{group}_{label}_pol")

    cmd.load(str(file_path), source_obj)

    chain_id, protein_len = pick_polymerase_chain(
        cmd,
        source_obj,
        forced_chain=forced_chain,
        min_len=min_polymerase_len,
    )

    selection = f"{source_obj} and chain {chain_id} and polymer.protein"
    if int(cmd.count_atoms(selection)) == 0:
        raise ValueError(f"{file_path.name}: chain {chain_id} 抽出結果が空です。")

    cmd.create(target_obj, selection)

    output_path = out_dir / f"{group}.{label}.chain_{safe_chain_name(chain_id)}.pdb"
    cmd.save(str(output_path), target_obj)

    return StructureEntry(
        label=label,
        group=group,
        source_path=file_path,
        source_obj=source_obj,
        target_obj=target_obj,
        chain_id=chain_id,
        protein_len=protein_len,
        output_path=output_path,
    )
