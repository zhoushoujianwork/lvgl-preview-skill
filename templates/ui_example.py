# -*- coding: utf-8 -*-
# LVGL UI 模块模板 —— lvgl-preview skill 的入口约定 (LVGL 8.x / 9.x 通用)。
#
# 唯一硬性要求: 定义 build(scr, **state), 在 scr 上搭 UI。
# 渲染器已替你 lv.init() + 注册好虚拟 display, scr 已可用。
# 预览: python3 ../scripts/lvgl_preview.py ui_example.py --out ui_example.png
import lvgl as lv


def build(scr, title="Hello LVGL", accent=0x00C8FF):
    scr.set_style_bg_color(lv.color_hex(0x0C101A), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)

    # 一个圆点 (LVGL 没有原生 circle: 用方 obj + radius 360)
    dot = lv.obj(scr)
    dot.set_size(40, 40)
    dot.set_style_radius(360, 0)
    dot.set_style_pad_all(0, 0)
    dot.clear_flag(lv.obj.FLAG.SCROLLABLE)        # 去掉默认滚动条
    dot.set_style_border_width(0, 0)
    dot.set_style_bg_color(lv.color_hex(accent), 0)
    dot.align(lv.ALIGN.CENTER, 0, -40)

    lbl = lv.label(scr)
    lbl.set_text(title)
    lbl.set_style_text_color(lv.color_hex(0xEBF0F8), 0)
    lbl.align(lv.ALIGN.CENTER, 0, 20)


# 直接 build(scr) 时的默认演示已由上面默认参数覆盖。
# 想试不同状态: lvgl_preview.py ui_example.py --state '{"title":"OPEN","accent":16755260}'
