# -*- coding: utf-8 -*-
# LVGL 绘图原语 —— 把命令式画线 (rect/circle/line) 封装成干净的 LVGL obj,
# 屏蔽默认边框/内边距/滚动条。LVGL 8.x / 9.x 通用 (桌面 sim 与设备共用)。
import lvgl as lv

# ---- v8 vs v9 自适配 ----
# 两端 LVGL 大版本不同: 字体 / line / qrcode 的 API 不一样。检测一次, 下面按需分支,
# 这样调用方的公共写法两端通用, UI 代码一字不改。
_V8 = hasattr(lv, "disp_drv_t")     # v8.3: lv.disp_drv_t / ft_info_t
_V9 = not _V8                       # v9(K230 'dev'): lv.disp_create / freetype_font_create

# ---- 中文字体 ----
# 设备 (v9): 推上去的可缩放 ttf; 桌面 (v8): 系统字体。任意字号都走矢量, build(scr) 不用改。
_ft_inited = False
_cjk_cache = {}
CJK_FONT_PATH = ("/sdcard/res/font/SourceHanSansSC-Normal-Min.ttf" if _V9
                 else "/System/Library/Fonts/STHeiti Medium.ttc")


def cjk_font(size, path=None):
    """加载中文字体, 任意字号。v9: freetype_font_create; v8: ft_info_t。失败返回 None。"""
    global _ft_inited
    p = path or CJK_FONT_PATH
    key = (int(size), p)
    if key in _cjk_cache:
        return _cjk_cache[key]
    font = None
    try:
        if _V9:
            font = lv.freetype_font_create(p, int(size), 0)   # (path, size, style=0 normal)
        else:
            if not _ft_inited:
                lv.freetype_init(16, 16, 512 * 1024)
                _ft_inited = True
            info = lv.ft_info_t()
            info.name = p
            info.weight = int(size)
            info.style = lv.FT_FONT_STYLE.NORMAL
            info.mem = None
            if info.font_init():
                font = info.font
    except Exception as e:
        print("cjk_font fail:", e)
    _cjk_cache[key] = font
    return font


def rect(parent, x, y, w, h, color, opa=None):
    o = lv.obj(parent)
    o.set_pos(int(x), int(y))
    o.set_size(int(w), int(h))
    o.set_style_radius(0, 0)
    o.set_style_border_width(0, 0)
    o.set_style_pad_all(0, 0)
    o.clear_flag(lv.obj.FLAG.SCROLLABLE)
    o.set_style_bg_color(lv.color_hex(color), 0)
    o.set_style_bg_opa(lv.OPA.COVER if opa is None else opa, 0)
    return o


def dot(parent, cx, cy, r, color):
    """实心圆 (圆心 cx,cy 半径 r)。"""
    o = lv.obj(parent)
    o.set_pos(int(cx - r), int(cy - r))
    o.set_size(int(2 * r), int(2 * r))
    o.set_style_radius(360, 0)
    o.set_style_border_width(0, 0)
    o.set_style_pad_all(0, 0)
    o.clear_flag(lv.obj.FLAG.SCROLLABLE)
    o.set_style_bg_color(lv.color_hex(color), 0)
    o.set_style_bg_opa(lv.OPA.COVER, 0)
    return o


def ring(parent, cx, cy, r, color, width=2):
    """空心环。"""
    o = lv.obj(parent)
    o.set_pos(int(cx - r), int(cy - r))
    o.set_size(int(2 * r), int(2 * r))
    o.set_style_radius(360, 0)
    o.set_style_pad_all(0, 0)
    o.clear_flag(lv.obj.FLAG.SCROLLABLE)
    o.set_style_bg_opa(lv.OPA.TRANSP, 0)
    o.set_style_border_width(int(width), 0)
    o.set_style_border_color(lv.color_hex(color), 0)
    return o


def label(parent, x, y, text, color, font=None):
    lb = lv.label(parent)
    lb.set_text(str(text))
    lb.set_style_text_color(lv.color_hex(color), 0)
    if font is not None:
        lb.set_style_text_font(font, 0)
    lb.set_pos(int(x), int(y))
    return lb


# v9 的 lv_line 用 point_precise_t; v8 用 point_t。保持引用避免被 GC (LVGL 存指针)。
_PT = getattr(lv, "point_precise_t", None) if _V9 else None
if _PT is None:
    _PT = lv.point_t
_line_pts = []


def vline(parent, x1, y1, x2, y2, color, width=4):
    ln = lv.line(parent)
    ln.set_style_pad_all(0, 0)
    ln.set_pos(0, 0)
    pts = [_PT({"x": int(x1), "y": int(y1)}),
           _PT({"x": int(x2), "y": int(y2)})]
    _line_pts.append(pts)        # keep alive
    ln.set_points(pts, 2)
    ln.set_style_line_width(int(width), 0)
    ln.set_style_line_color(lv.color_hex(color), 0)
    ln.set_style_line_rounded(True, 0)
    return ln


def person(parent, cx, cy, scale, color):
    """头 + 肩 两个实心圆, 对齐 canvas.py Icons.person。"""
    dot(parent, cx, cy - 38 * scale, 40 * scale, color)
    dot(parent, cx, cy + 50 * scale, 72 * scale, color)


# ---- 七段时钟 (复刻 seven_seg.py) ----
_SEG = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd",
    "4": "fbgc", "5": "afgcd", "6": "afgcde", "7": "abc",
    "8": "abcdefg", "9": "abcfgd", " ": "", ":": "colon",
}


def _seg(parent, x, y, w, h, t, color, s):
    if s == "a":
        rect(parent, x + t, y, w - 2 * t, t, color)
    elif s == "b":
        rect(parent, x + w - t, y + t, t, (h - t) // 2 - t, color)
    elif s == "c":
        rect(parent, x + w - t, y + h // 2, t, (h - t) // 2 - t, color)
    elif s == "d":
        rect(parent, x + t, y + h - t, w - 2 * t, t, color)
    elif s == "e":
        rect(parent, x, y + h // 2, t, (h - t) // 2 - t, color)
    elif s == "f":
        rect(parent, x, y + t, t, (h - t) // 2 - t, color)
    elif s == "g":
        rect(parent, x + t, y + h // 2 - t // 2, w - 2 * t, t, color)


def seven_seg_char(parent, x, y, w, h, t, color, ch):
    segs = _SEG.get(ch, "")
    if segs == "colon":
        d = t
        rect(parent, x + w // 2 - d // 2, y + h // 3, d, d, color)
        rect(parent, x + w // 2 - d // 2, y + 2 * h // 3, d, d, color)
        return
    for s in segs:
        _seg(parent, x, y, w, h, t, color, s)


def clock_hhmm(parent, x, y, dw, dh, gap, t, color, hhmm):
    """hhmm: 形如 '08:14' 的字符串 (sim 里固定, 设备上传真实时间)。"""
    hh, mm = hhmm.split(":")
    cur = x
    seven_seg_char(parent, cur, y, dw, dh, t, color, hh[0]); cur += dw + gap
    seven_seg_char(parent, cur, y, dw, dh, t, color, hh[1]); cur += dw + gap
    seven_seg_char(parent, cur, y, dw // 2, dh, t, color, ":"); cur += dw // 2 + gap
    seven_seg_char(parent, cur, y, dw, dh, t, color, mm[0]); cur += dw + gap
    seven_seg_char(parent, cur, y, dw, dh, t, color, mm[1])
