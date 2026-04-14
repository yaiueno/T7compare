#!/usr/bin/env python3
"""PyMOLで重ね合わせプレビュー画像を生成する。"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path


_DLL_HANDLES = []


def configure_windows_dll_dirs() -> None:
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return

    candidates: list[Path] = []
    env_dirs = os.environ.get("PYMOL_DLL_DIR", "").strip()
    if env_dirs:
        for item in env_dirs.split(";"):
            item = item.strip()
            if item:
                candidates.append(Path(item))

    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        candidates.append(Path(local_app_data) / "Schrodinger" / "PyMOL2" / "Library" / "bin")

    for path in candidates:
        if path.is_dir():
            try:
                _DLL_HANDLES.append(os.add_dll_directory(str(path)))
            except OSError:
                pass


configure_windows_dll_dirs()

import pymol2


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render overlay previews via PyMOL")
    p.add_argument("--known", required=True)
    p.add_argument("--set1", required=True, help="glob pattern for set1 pdbs")
    p.add_argument("--set2", required=True, help="glob pattern for set2 pdbs")
    p.add_argument("--out_dir", required=True)
    p.add_argument("--method", choices=["align", "super"], default="super")
    p.add_argument("--width", type=int, default=1600)
    p.add_argument("--height", type=int, default=900)
    return p.parse_args()


def align_to_known(cmd, method: str, mobile_obj: str, known_obj: str) -> None:
    mobile = f"{mobile_obj} and name CA"
    target = f"{known_obj} and name CA"
    if method == "align":
        cmd.align(mobile, target)
    else:
        cmd.super(mobile, target)


def load_and_align_group(cmd, pattern: str, known_obj: str, prefix: str, method: str) -> list[str]:
    objects: list[str] = []
    for i, fp in enumerate(sorted(glob.glob(pattern))):
        obj = f"{prefix}_{i}"
        cmd.load(fp, obj)
        align_to_known(cmd, method, obj, known_obj)
        objects.append(obj)
    return objects


def style_scene(cmd, known_obj: str, set1_objs: list[str], set2_objs: list[str]) -> None:
    cmd.hide("everything", "all")
    cmd.show("cartoon", "all")
    cmd.bg_color("black")
    cmd.set("ray_opaque_background", 1)
    cmd.color("gray70", known_obj)
    for obj in set1_objs:
        cmd.color("cyan", obj)
    for obj in set2_objs:
        cmd.color("magenta", obj)
    cmd.orient("all")


def save_view(cmd, out_png: Path, selection: str, width: int, height: int) -> None:
    cmd.disable("all")
    cmd.enable(f"({selection})")
    cmd.orient(selection)
    cmd.ray(width, height)
    cmd.png(str(out_png))


def object_union(names: list[str]) -> str:
    if not names:
        return "none"
    return " or ".join(names)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.reinitialize()

        known_obj = "known"
        cmd.load(args.known, known_obj)

        set1_objs = load_and_align_group(cmd, args.set1, known_obj, "set1", args.method)
        set2_objs = load_and_align_group(cmd, args.set2, known_obj, "set2", args.method)

        style_scene(cmd, known_obj, set1_objs, set2_objs)

        save_view(
            cmd,
            out_dir / "overlay_all.png",
            object_union([known_obj, *set1_objs, *set2_objs]),
            args.width,
            args.height,
        )
        save_view(
            cmd,
            out_dir / "overlay_set1.png",
            object_union([known_obj, *set1_objs]),
            args.width,
            args.height,
        )
        save_view(
            cmd,
            out_dir / "overlay_set2.png",
            object_union([known_obj, *set2_objs]),
            args.width,
            args.height,
        )

        cmd.enable("all")
        cmd.save(str(out_dir / "overlay_preview_session.pse"))

    print(f"[INFO] wrote: {out_dir / 'overlay_all.png'}")
    print(f"[INFO] wrote: {out_dir / 'overlay_set1.png'}")
    print(f"[INFO] wrote: {out_dir / 'overlay_set2.png'}")
    print(f"[INFO] wrote: {out_dir / 'overlay_preview_session.pse'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
