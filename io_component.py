#!/usr/bin/env python3
#レビュー済み　上野 2026-04-14
"""入出力パス解決を担当するコンポーネント。"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import glob

#パターンを実行時に入れたやつを参考にファイルを正規化するueno
def resolve_files(patterns: Iterable[str]) -> list[Path]:
    """globパターンを展開し、重複を除いてファイル一覧を返す。"""
    resolved: list[Path] = []
    for pattern in patterns:
        for match in sorted(glob.glob(pattern)):
            path = Path(match)
            if path.is_file():
                resolved.append(path)

    unique = sorted({p.resolve() for p in resolved})
    return [Path(p) for p in unique]

#受け取ったパスのディレクトリがなければ作成してあればpathを返すだけ、なくても止まらないようにするueno
def ensure_dir(path: Path) -> Path:
    """ディレクトリが無ければ作成し、そのPathを返す。"""
    path.mkdir(parents=True, exist_ok=True)
    return path
