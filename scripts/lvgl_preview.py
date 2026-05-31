#!/usr/bin/env python3
# LVGL UI → PNG 一键预览 (host 端编排)。LVGL 8.x / 9.x 自适配。
#
#   python3 lvgl_preview.py <ui_module.py> [--out preview.png] [--size 480x800]
#                           [--state '{"k":v}'] [--fn build]
#
# ui_module.py 须定义 build(scr, **state): 用 LVGL API 在 scr 上搭 UI。
# 本脚本用本地 lv_micropython 二进制 headless 渲染, 转 PNG, 打印结果路径。
import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def find_binary():
    """优先 $LVMP_BIN, 否则在常见位置找 lv_micropython unix 二进制。"""
    env = os.environ.get("LVMP_BIN")
    cands = [env] if env else []
    cands += [
        os.path.expanduser("~/lv_micropython/ports/unix/micropython"),
        os.path.expanduser("~/github/lv_micropython/ports/unix/micropython"),
        os.path.expanduser("~/src/lv_micropython/ports/unix/micropython"),
        "/opt/lv_micropython/ports/unix/micropython",
    ]
    for c in cands:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def main():
    ap = argparse.ArgumentParser(description="Render an LVGL MicroPython UI module to PNG (v8/v9 auto)")
    ap.add_argument("ui", help="path to UI module defining build(scr, **state)")
    ap.add_argument("--out", default=None, help="output PNG (default: <ui>.png next to ui)")
    ap.add_argument("--size", default="480x800", help="WxH, default 480x800")
    ap.add_argument("--state", default="", help="JSON kwargs passed to build()")
    ap.add_argument("--fn", default="build", help="build function name (default build)")
    args = ap.parse_args()

    binary = find_binary()
    if not binary:
        sys.exit("❌ no lv_micropython binary found. Run scripts/build_runtime.sh, "
                 "or set LVMP_BIN to point at ports/unix/micropython.")

    ui = os.path.abspath(args.ui)
    if not os.path.isfile(ui):
        sys.exit("❌ UI module not found: " + ui)
    w, h = args.size.lower().split("x")
    out = os.path.abspath(args.out) if args.out else os.path.splitext(ui)[0] + ".png"

    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tf:
        raw = tf.name
    try:
        # -X heapsize: 全屏 800x480 帧缓冲 1.5MB + FreeType 缓存 + 控件树, 默认堆不够
        r = subprocess.run([binary, "-X", "heapsize=64m",
                            os.path.join(HERE, "render.py"), ui, raw, w, h, args.state, args.fn])
        if r.returncode != 0:
            sys.exit("❌ render failed (see lv_micropython error above)")
        subprocess.run([sys.executable, os.path.join(HERE, "raw2png.py"), raw, out], check=True)
        print("✅ preview -> " + out)
    finally:
        try:
            os.remove(raw)
        except OSError:
            pass


if __name__ == "__main__":
    main()
