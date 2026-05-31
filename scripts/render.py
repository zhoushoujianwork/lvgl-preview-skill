# -*- coding: utf-8 -*-
# 通用 headless LVGL 渲染器 (跑在 lv_micropython unix 上)。版本自适配 v8 / v9。
# 注册一块全屏缓冲的虚拟 display, import 目标 UI 模块, 调它的 build(scr, **state),
# 同步渲染, 把 BGRA 帧 dump 到 out_raw (8字节头: W,H uint32 LE)。
#
# argv: <ui_module.py> <out_raw> <W> <H> [state_json] [build_fn=build]
import sys
import lvgl as lv

# 把本 skill 的 lib/ 加入搜索路径, 让任意 UI 模块都能 import lvkit (通用原语 + CJK 字体)。
_scripts = sys.argv[0].rsplit("/", 1)[0] if "/" in sys.argv[0] else "."
sys.path.insert(0, _scripts + "/../lib")

ui_path = sys.argv[1]
out_raw = sys.argv[2]
W = int(sys.argv[3])
H = int(sys.argv[4])
state = {}
if len(sys.argv) > 5 and sys.argv[5]:
    import json
    state = json.loads(sys.argv[5])
fn = sys.argv[6] if len(sys.argv) > 6 else "build"

lv.init()

# ---- v8 / v9 自适配的虚拟 display 注册 ----
# 全屏单缓冲: 渲染后 buf 即整屏画面 (LVGL 32-bit color = BGRA on little-endian)。
buf = bytearray(W * H * 4)          # 必须持有引用, LVGL 内部存的是指针
_V8 = hasattr(lv, "disp_drv_t")     # v8.3: lv.disp_drv_t; v9: lv.disp_create / display_create

if _V8:
    draw_buf = lv.disp_draw_buf_t()
    draw_buf.init(buf, None, W * H)
    disp_drv = lv.disp_drv_t()
    disp_drv.init()
    disp_drv.draw_buf = draw_buf
    disp_drv.hor_res = W
    disp_drv.ver_res = H

    def _flush(drv, area, color_p):
        drv.flush_ready()

    disp_drv.flush_cb = _flush
    disp_drv.register()
else:
    # v9: K230 CanMV 命名 (disp_create/set_draw_buffers) 优先, 回落到 mainline (display_create)。
    create = getattr(lv, "disp_create", None) or getattr(lv, "display_create", None)
    disp = create(W, H)
    cf = getattr(lv, "COLOR_FORMAT", None)
    if cf is not None and hasattr(disp, "set_color_format"):
        disp.set_color_format(cf.ARGB8888)
    rm = getattr(lv, "DISP_RENDER_MODE", None) or getattr(lv, "DISPLAY_RENDER_MODE", None)
    if hasattr(disp, "set_draw_buffers"):
        disp.set_draw_buffers(buf, None, len(buf), rm.FULL)
    elif hasattr(disp, "set_buffers"):
        disp.set_buffers(buf, None, len(buf), rm.FULL)

    def _flush_v9(d, area, px):
        d.flush_ready()

    (getattr(disp, "set_flush_cb", None) or (lambda cb: None))(_flush_v9)

# ---- 按路径 import UI 模块 (把它所在目录放进 sys.path, 让同级 import 也能解析) ----
if "/" in ui_path:
    d, base = ui_path.rsplit("/", 1)
else:
    d, base = ".", ui_path
if base.endswith(".py"):
    base = base[:-3]
sys.path.insert(0, d)
mod = __import__(base)

# scr_act (v8 / K230 v9) 或 screen_active (mainline v9)
_scr_fn = getattr(lv, "scr_act", None) or getattr(lv, "screen_active", None)
scr = _scr_fn()    # 注意: 必须先 register display, 否则返回 None
build = getattr(mod, fn)
if state:
    build(scr, **state)
else:
    build(scr)

# 同步渲染一帧
_def = getattr(lv, "disp_get_default", None) or getattr(lv, "display_get_default", None)
lv.refr_now(_def())

with open(out_raw, "wb") as f:
    f.write(W.to_bytes(4, "little"))
    f.write(H.to_bytes(4, "little"))
    f.write(buf)
print("rendered {} -> {} ({}x{}, LVGL {})".format(
    ui_path, out_raw, W, H, "v8" if _V8 else "v9"))
