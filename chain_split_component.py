#!/usr/bin/env python3
"""PyMOLオブジェクトを chain 単位で扱う小さなユーティリティ群。

主な用途:
- 各chainがタンパク質か核酸かをざっくり判定する
- DNA2本 + ポリメラーゼ1本を自動選択する
- chainごとにPDB/CIFとして書き出す
"""

from __future__ import annotations

from pathlib import Path


def safe_chain_name(chain_id: str) -> str:
    """chain IDをファイル名安全な文字列へ変換する。"""
    if not chain_id or chain_id.strip() == "":
        return "blank"
    return "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in chain_id)


def chain_profiles(cmd, obj_name: str) -> list[dict[str, int | str]]:
    """各chainの簡易プロファイルを返す。

    返却項目:
    - chain: chain ID
    - protein_len: CA原子数（タンパク質長の近似）
    - nucleic_len: P原子数（核酸長の近似）
    - atom_count: chain全体の原子数
    """
    profiles: list[dict[str, int | str]] = []
    for chain_id in cmd.get_chains(obj_name):
        # chainごとに「タンパク質」「核酸」を原子名ベースで概算する。
        base = f"({obj_name} and chain {chain_id})"
        protein_len = int(cmd.count_atoms(f"{base} and polymer.protein and name CA"))
        nucleic_len = int(cmd.count_atoms(f"{base} and polymer.nucleic and name P"))
        atom_count = int(cmd.count_atoms(base))
        profiles.append(
            {
                "chain": chain_id,
                "protein_len": protein_len,
                "nucleic_len": nucleic_len,
                "atom_count": atom_count,
            }
        )
    return profiles


def select_dna_and_polymerase(cmd, obj_name: str) -> tuple[str, str, str]:
    """DNA2本 + ポリメラーゼ1本を自動選択してchain IDを返す。

    ルール:
    - DNA: nucleic_lenが大きい上位2本
    - polymerase: protein_lenが最大の1本
    """
    profiles = chain_profiles(cmd, obj_name)
    # DNA候補とタンパク質候補を長さ順に並べる。
    dna = sorted(
        [p for p in profiles if int(p["nucleic_len"]) > 0],
        key=lambda x: int(x["nucleic_len"]),
        reverse=True,
    )
    proteins = sorted(
        [p for p in profiles if int(p["protein_len"]) > 0],
        key=lambda x: int(x["protein_len"]),
        reverse=True,
    )

    if len(dna) < 2:
        raise ValueError("DNA鎖を2本検出できませんでした。")
    if not proteins:
        raise ValueError("タンパク質鎖を検出できませんでした。")

    # 上位2本のDNAと最長タンパク質を返す。
    return str(dna[0]["chain"]), str(dna[1]["chain"]), str(proteins[0]["chain"])


def split_chains_to_files(
    cmd,
    obj_name: str,
    out_dir: Path,
    prefix: str,
    polymer: str = "all",
    fmt: str = "pdb",
) -> int:
    """オブジェクトをchainごとに分割してファイル保存する。

    Args:
        polymer: all / protein / nucleic
        fmt: pdb / cif

    Returns:
        保存したchainファイル数
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    # 書き出し対象のポリマータイプを選ぶ。
    if polymer == "protein":
        polymer_filter = "polymer.protein"
    elif polymer == "nucleic":
        polymer_filter = "polymer.nucleic"
    else:
        polymer_filter = "all"

    written = 0
    for chain_id in cmd.get_chains(obj_name):
        # chain単位で選択を作成し、空選択はスキップ。
        sel = f"{obj_name} and chain {chain_id}"
        if polymer_filter != "all":
            sel = f"({sel}) and {polymer_filter}"
        if int(cmd.count_atoms(sel)) == 0:
            continue

        # chainごとの一時オブジェクトを作って保存。
        obj = f"split_{safe_chain_name(chain_id)}"
        cmd.create(obj, sel)
        ext = "cif" if fmt == "cif" else "pdb"
        out_file = out_dir / f"{prefix}.chain_{safe_chain_name(chain_id)}.{ext}"
        cmd.save(str(out_file), obj)
        written += 1

    return written
