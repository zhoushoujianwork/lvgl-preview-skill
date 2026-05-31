#!/bin/bash
# install.sh — 把本仓库作为 Claude Code skill 安装到本机, 以便"只开发这个仓库"。
#
# 原理: 用软链接把本 repo 指到 Claude Code 的 skills 目录, 编辑 repo 即时生效, 无需复制。
#
#   ./install.sh                      # 装到用户级 ~/.claude/skills/lvgl-preview (所有项目可用)
#   ./install.sh --project /path/app  # 装到某项目 <app>/.claude/skills/lvgl-preview
#   ./install.sh --copy [...]         # 复制而非软链 (给不跟随 symlink 的环境)
#   ./install.sh --uninstall [...]    # 移除链接/副本
#
# ⚠️ 注意: `mpremote mount` 不跟随 symlink。若你的设备开发把本 repo 的 lib/lvkit.py
#    通过 mount 喂给设备, 不能软链, 要在挂载前 copy 进被挂载的目录 (见 README / 设备脚本)。
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
NAME="lvgl-preview"
MODE="symlink"
DEST_BASE="$HOME/.claude/skills"
ACTION="install"

while [ $# -gt 0 ]; do
  case "$1" in
    --project) DEST_BASE="$2/.claude/skills"; shift 2 ;;
    --copy) MODE="copy"; shift ;;
    --uninstall) ACTION="uninstall"; shift ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1"; exit 2 ;;
  esac
done

TARGET="$DEST_BASE/$NAME"

if [ "$ACTION" = "uninstall" ]; then
  if [ -L "$TARGET" ] || [ -e "$TARGET" ]; then
    rm -rf "$TARGET"; echo "✓ removed $TARGET"
  else
    echo "· nothing at $TARGET"
  fi
  exit 0
fi

mkdir -p "$DEST_BASE"

# 已存在: 若是指向本 repo 的软链则幂等跳过; 是别的东西就备份
if [ -L "$TARGET" ]; then
  cur="$(readlink "$TARGET")"
  if [ "$cur" = "$REPO" ]; then echo "✓ already linked: $TARGET -> $REPO"; exit 0; fi
  rm -f "$TARGET"
elif [ -e "$TARGET" ]; then
  bak="$TARGET.bak.$(date +%s 2>/dev/null || echo old)"
  mv "$TARGET" "$bak"; echo "· existing dir backed up -> $bak"
fi

if [ "$MODE" = "symlink" ]; then
  ln -s "$REPO" "$TARGET"
  echo "✓ linked  $TARGET -> $REPO"
else
  cp -RL "$REPO" "$TARGET"; rm -rf "$TARGET/.git"
  echo "✓ copied  $REPO -> $TARGET"
fi

echo
echo "Claude Code 现在会从这里加载 skill。编辑 $REPO 即时生效。"
echo "桌面渲染前确保: export LVMP_BIN=<lv_micropython>/ports/unix/micropython"
