# 上设备: LVGL display 绑定 (v8 / v9) + 中文 + 截图回传

桌面预览跑通后, UI 代码 (`build(scr)`) 一字不改, 只换显示初始化。下面是经真机验证
(K230 CanMV, LVGL v9) 的可复制写法, 以及 v8 的对应版本。

## v9 disp 绑定 (K230 CanMV / LVGL 9.x)

抄设备自带的官方例子 (CanMV: `/sdcard/examples/15-LVGL/lvgl_demo.py`) —— 版本最对得上。

```python
from media.display import *
from media.media import *
import lvgl as lv, image, uctypes, time, os

W = ALIGN_UP(800, 16); H = 480

def lvgl_setup():
    lv.init()
    imgs = [image.Image(W, H, image.BGRA8888) for _ in range(2)]   # 双缓冲, 32-bit
    disp = lv.disp_create(W, H)
    disp.set_color_format(lv.COLOR_FORMAT.ARGB8888)
    disp.set_draw_buffers(imgs[0].bytearray(), imgs[1].bytearray(),
                          imgs[0].size(), lv.DISP_RENDER_MODE.FULL)
    def flush_cb(drv, area, color):
        if drv.flush_is_last():
            ptr = uctypes.addressof(color.__dereference__())
            shown = imgs[0] if imgs[0].virtaddr() == ptr else imgs[1]
            Display.show_image(shown, layer=Display.LAYER_OSD0)
        drv.flush_ready()
    disp.set_flush_cb(flush_cb)
    return imgs

Display.init(Display.ST7701, width=W, height=H, to_ide=True)
MediaManager.init()           # 若同时开摄像头
lvgl_setup()
scr = lv.scr_act()
# ... build(scr) ...
while True:                   # v9 无需手动 tick_inc
    os.exitpoint()
    lv.task_handler()
    time.sleep_ms(10)
```

## v8 disp 绑定 (LVGL 8.x)

```python
import lvgl as lv
buf = bytearray(W * H * 4)
draw_buf = lv.disp_draw_buf_t(); draw_buf.init(buf, None, W * H)
drv = lv.disp_drv_t(); drv.init()
drv.draw_buf = draw_buf; drv.hor_res = W; drv.ver_res = H
def flush_cb(d, area, color_p):
    # 把 buf 推到你的屏 (SPI/RGB), 然后:
    d.flush_ready()
drv.flush_cb = flush_cb; drv.register()
```

## 中文字体

- **矢量 (任意字号, 推荐)**: 推一个 ttf 上设备, `lvkit.cjk_font(size)` 内部:
  - v9: `lv.freetype_font_create("/sdcard/res/font/Xxx.ttf", size, 0)`
  - v8: `lv.ft_info_t()` + `.font_init()`
- **位图 .fnt**: `lv.font_load("A:/path/font.fnt")` —— 注意板载子集字体可能只含 demo 用字,
  常用汉字会缺 (显示成 □), 优先用矢量 ttf。

## 截图回传 (无屏调试 / Agent 读图)

设备的 `image.to_jpeg` / `to_rgb565` / `copy(x_scale=)` 对 BGRA8888 源可能有 stride bug
(出花屏)。**只有全尺寸 raw BGRA 字节可靠**。UI 大片纯色, 用 `deflate` 压一下再传:

```python
import deflate, io
raw = last_shown_img.bytearray()           # 全尺寸 BGRA
b = io.BytesIO(); d = deflate.DeflateIO(b, deflate.GZIP); d.write(raw); d.close()
open("/sdcard/shot.raw.gz", "wb").write(b.getvalue())   # ~18-49x, 1.5MB→几十KB
```

host 端: `gzip.decompress` → `PIL.Image.frombytes("RGBA",(W,H),data,"raw","BGRA")`。

## 干净退出 (避免 mpremote mount 把板子冻住)

在 RT-Smart 上, 渲染脚本跑完应**干净自退** (跳出循环 → `lv.deinit()` / `Display.deinit()`),
否则 `mpremote mount` 拆卸 USB-CDC 时容易 desync, 把板子冻在最后一屏, 只能物理复位。
