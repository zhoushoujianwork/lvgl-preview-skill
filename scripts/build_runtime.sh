#!/bin/bash
# 构建桌面 lv_micropython unix 二进制 (headless 渲染用)。默认 LVGL v8 (release/v8),
# 也可 build v9 (master)。已含 macOS arm64 / clang17 的修复; Linux 一般直接编。
#
#   bash build_runtime.sh [dest_dir] [v8|v9]
#       dest_dir  默认 ~/lv_micropython 的父目录 (~)
#       v8|v9     默认 v8 (与多数嵌入式 LVGL 8.x 一致); v9 用于 LVGL 9.x 设备 (如 K230 CanMV)
#
# 产物: <dest>/lv_micropython/ports/unix/micropython
# 完成后: export LVMP_BIN=<dest>/lv_micropython/ports/unix/micropython
set -e
DEST="${1:-$HOME}"
VER="${2:-v8}"
case "$VER" in
  v8) BRANCH="release/v8" ;;
  v9) BRANCH="master" ;;     # mainline = LVGL 9.x
  *) echo "usage: build_runtime.sh [dest] [v8|v9]"; exit 2 ;;
esac
mkdir -p "$DEST"; cd "$DEST"

if [ ! -d lv_micropython ]; then
  # 别 --recurse-submodules (会拉 pico-sdk/tinyusb 等数 G 无关板级子模块)
  git clone -b "$BRANCH" --depth 1 https://github.com/lvgl/lv_micropython.git
fi
cd lv_micropython
make -C ports/unix submodules     # 只拉 unix + lvgl 需要的子模块

# macOS arm64: imagetools.py 的 @micropython.native/.viper 无原生发射器 → "invalid arch"。
# 注释掉 (PNG 解码 helper, 不影响 UI 渲染)。Linux 上这步是 no-op。
IMG=lib/lv_bindings/lib/imagetools.py
if [ -f "$IMG" ]; then
  sed -i '' 's/^@micropython.native/#&/; s/^@micropython.viper/#&/' "$IMG" 2>/dev/null || \
  sed -i 's/^@micropython.native/#&/; s/^@micropython.viper/#&/' "$IMG" 2>/dev/null || true
fi

# clang17 把 -Wgnu-folding-constant 当 error → -Wno-error (Linux gcc 无害)
make -C mpy-cross -j4 CFLAGS_EXTRA="-Wno-error"

# lv_bindings 的 SDL 驱动 #include <SDL2/SDL.h> → 给 SDL2 的 include/lib。
# macOS: brew install sdl2;  Linux: apt install libsdl2-dev
SDL_INC="$(pkg-config --cflags sdl2 2>/dev/null || echo '-I/opt/homebrew/include -I/opt/homebrew/include/SDL2 -D_THREAD_SAFE')"
SDL_LIB="$(pkg-config --libs sdl2 2>/dev/null || echo '-L/opt/homebrew/lib -lSDL2')"
make -C ports/unix -j4 CFLAGS_EXTRA="-Wno-error $SDL_INC" LDFLAGS_EXTRA="$SDL_LIB"

echo
echo "✅ binary: $DEST/lv_micropython/ports/unix/micropython  (LVGL $VER)"
echo "   usage:  export LVMP_BIN=$DEST/lv_micropython/ports/unix/micropython"
