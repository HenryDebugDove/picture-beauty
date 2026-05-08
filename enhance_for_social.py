#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将截图 / 封面图处理得更清晰，适合小红书、抖音发布。
- 适度放大 + Lanczos 重采样，减轻压缩后文字发糊
- Unsharp Mask 锐化（克制参数，避免描边感）
- 轻微对比度 / 饱和度，偏“高级感”而非滤镜味

用法:
  pip install -r requirements-image.txt
  python enhance_for_social.py
  python enhance_for_social.py -i default.png -o mockup.png --mockup
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


def _ensure_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "P"):
        return img.convert("RGBA") if img.mode == "P" else img
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def upscale_min_width(img: Image.Image, min_short_edge: int) -> Image.Image:
    """短边至少到 min_short_edge，长边同比缩放，利于发布后仍清晰。"""
    w, h = img.size
    short = min(w, h)
    if short >= min_short_edge:
        return img
    scale = min_short_edge / short
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def enhance_clarity(
    img: Image.Image,
    *,
    unsharp_radius: float = 1.2,
    unsharp_percent: int = 130,
    unsharp_threshold: int = 3,
    contrast: float = 1.06,
    color: float = 1.04,
    sharpness: float = 1.08,
) -> Image.Image:
    """核心清晰增强：锐化 + 轻微对比与色彩。"""
    base = _ensure_rgb(img)
    if base.mode == "RGBA":
        base = base.convert("RGB")

    out = base.filter(
        ImageFilter.UnsharpMask(
            radius=unsharp_radius,
            percent=unsharp_percent,
            threshold=unsharp_threshold,
        )
    )
    out = ImageEnhance.Contrast(out).enhance(contrast)
    out = ImageEnhance.Color(out).enhance(color)
    out = ImageEnhance.Sharpness(out).enhance(sharpness)
    return out


def _rounded_rectangle_mask(size: tuple[int, int], radius: int) -> Image.Image:
    w, h = size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    return mask


def gradient_background_vertical(size: tuple[int, int], dark: bool = True) -> Image.Image:
    """竖向柔和渐变（低调暗底 / 浅底）。"""
    w, h = size
    grad = Image.new("RGB", (w, h))
    px = grad.load()
    if dark:
        top = (18, 18, 22)
        bottom = (8, 9, 14)
    else:
        top = (245, 246, 248)
        bottom = (230, 232, 238)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return grad


def gradient_background_diagonal(
    size: tuple[int, int],
    *,
    top_left: tuple[int, int, int] = (255, 106, 71),
    bottom_right: tuple[int, int, int] = (58, 32, 108),
) -> Image.Image:
    """
    对角线性渐变（左上 → 右下），接近 Shots / 常见 mockup 工具的「Magic Gradient」观感。
    参考: https://shots.so/
    """
    w, h = size
    grad = Image.new("RGB", (w, h))
    px = grad.load()
    c0, c1 = top_left, bottom_right
    denom = max(w + h - 2, 1)
    for y in range(h):
        for x in range(w):
            t = (x + y) / denom
            r = int(c0[0] + (c1[0] - c0[0]) * t)
            g = int(c0[1] + (c1[1] - c0[1]) * t)
            b = int(c0[2] + (c1[2] - c0[2]) * t)
            px[x, y] = (r, g, b)
    return grad


def compose_premium_card(
    img: Image.Image,
    *,
    ratio: tuple[int, int],
    style: str = "shots",
    margin_ratio: float | None = None,
    corner_radius: int = 28,
    shadow_offset: tuple[int, int] | None = None,
    shadow_blur: int | None = None,
    shadow_opacity: float | None = None,
    border_width: int = 3,
    border_color: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """
    将截图置于画布：圆角遮罩 + box-shadow + 可选细边框。
    style:
      - \"shots\": 橙红→紫蓝对角渐变（类似 shots.so mockup）
      - \"minimal\": 深色竖渐变（旧版低调底）
    ratio: 画布宽高比，如 (16,9) 横版 mockup、(3,4) 小红书、(9,16) 抖音。
    """
    rw, rh = ratio
    iw, ih = img.size
    target_h = max(ih, 1600)
    target_w = int(round(target_h * rw / rh))

    if style == "shots":
        if margin_ratio is None:
            margin_ratio = 0.09
        if shadow_offset is None:
            shadow_offset = (18, 36)
        if shadow_blur is None:
            shadow_blur = 36
        if shadow_opacity is None:
            shadow_opacity = 0.48
        canvas = gradient_background_diagonal((target_w, target_h))
    else:
        if margin_ratio is None:
            margin_ratio = 0.06
        if shadow_offset is None:
            shadow_offset = (0, 18)
        if shadow_blur is None:
            shadow_blur = 22
        if shadow_opacity is None:
            shadow_opacity = 0.35
        canvas = gradient_background_vertical((target_w, target_h), dark=True)

    margin = int(round(min(target_w, target_h) * margin_ratio))
    inner_w = target_w - 2 * margin
    inner_h = target_h - 2 * margin
    fit = ImageOps.contain(img, (inner_w, inner_h), Image.Resampling.LANCZOS)
    fw, fh = fit.size
    if fit.mode != "RGBA":
        fit = fit.convert("RGBA")

    x0 = (target_w - fw) // 2
    y0 = (target_h - fh) // 2

    r = min(corner_radius, fw // 4, fh // 4)
    mask = _rounded_rectangle_mask((fw, fh), r)

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ox, oy = shadow_offset
    opacity = int(255 * shadow_opacity)
    shadow_alpha = mask.point(lambda p: (p * opacity) // 255)
    black = Image.merge(
        "RGBA",
        (
            Image.new("L", (fw, fh), 0),
            Image.new("L", (fw, fh), 0),
            Image.new("L", (fw, fh), 0),
            shadow_alpha,
        ),
    )
    shadow_layer.paste(black, (x0 + ox, y0 + oy), black)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

    out = canvas.convert("RGBA")
    out = Image.alpha_composite(out, shadow_layer)

    card_rgba = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    card_rgba.paste(fit, (0, 0))
    card_rgba.putalpha(mask)
    out.paste(card_rgba, (x0, y0), card_rgba)

    out_rgb = out.convert("RGB")
    if border_width > 0:
        draw = ImageDraw.Draw(out_rgb)
        inset = border_width // 2
        draw.rounded_rectangle(
            (
                x0 + inset,
                y0 + inset,
                x0 + fw - 1 - inset,
                y0 + fh - 1 - inset,
            ),
            radius=max(r - inset, 1),
            outline=border_color,
            width=border_width,
        )

    return out_rgb


def run(
    input_path: Path,
    output_path: Path,
    *,
    preset: str,
    min_short: int,
    mockup_169: bool,
    xhs_card: bool,
    douyin_card: bool,
    card_style: str,
) -> None:
    img = Image.open(input_path)
    img = ImageOps.exif_transpose(img)

    if preset == "light":
        img = upscale_min_width(img, min_short)
        out = enhance_clarity(
            img,
            unsharp_radius=1.0,
            unsharp_percent=115,
            contrast=1.03,
            color=1.02,
            sharpness=1.05,
        )
    elif preset == "strong":
        img = upscale_min_width(img, max(min_short, 1440))
        out = enhance_clarity(
            img,
            unsharp_radius=1.5,
            unsharp_percent=150,
            contrast=1.12,
            color=1.08,
            sharpness=1.15,
        )
    else:  # premium：默认平衡
        img = upscale_min_width(img, max(min_short, 1280))
        out = enhance_clarity(
            img,
            unsharp_radius=1.2,
            unsharp_percent=130,
            contrast=1.06,
            color=1.04,
            sharpness=1.08,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    style = "shots" if card_style == "shots" else "minimal"

    if mockup_169:
        out = compose_premium_card(out, ratio=(16, 9), style=style)
    elif xhs_card:
        out = compose_premium_card(out, ratio=(3, 4), style=style)
    elif douyin_card:
        out = compose_premium_card(out, ratio=(9, 16), style=style)

    out.save(output_path, quality=95, optimize=True)
    print(f"已保存: {output_path}  尺寸: {out.size}")


def main() -> None:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="社交发布用图片清晰化 / 高级感处理")
    parser.add_argument("-i", "--input", type=Path, default=root / "default.png")
    parser.add_argument("-o", "--output", type=Path, default=root / "default_enhanced.png")
    parser.add_argument(
        "--preset",
        choices=("premium", "light", "strong"),
        default="premium",
        help="premium=平衡推荐；light=轻量；strong=更强锐化对比",
    )
    parser.add_argument(
        "--min-short",
        type=int,
        default=1080,
        metavar="PX",
        help="短边至少放大到该像素（默认 1080，利于平台压图后仍清晰）",
    )
    parser.add_argument(
        "--mockup",
        action="store_true",
        help="16:9 横版画布：对角渐变 + 圆角 + 投影 + 细边框（类似 shots.so mockup）",
    )
    parser.add_argument("--xhs-card", action="store_true", help="3:4 竖版画布（偏小红书）")
    parser.add_argument("--douyin-card", action="store_true", help="9:16 竖版画布（偏抖音）")
    parser.add_argument(
        "--card-style",
        choices=("shots", "minimal"),
        default="shots",
        help="shots=橙红→紫蓝对角渐变+边框+阴影；minimal=深色竖渐变（旧版）",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"找不到输入文件: {args.input}")

    modes = int(args.mockup) + int(args.xhs_card) + int(args.douyin_card)
    if modes > 1:
        raise SystemExit("请只选一种画布：--mockup / --xhs-card / --douyin-card 之一")

    run(
        args.input,
        args.output,
        preset=args.preset,
        min_short=args.min_short,
        mockup_169=args.mockup,
        xhs_card=args.xhs_card,
        douyin_card=args.douyin_card,
        card_style=args.card_style,
    )


if __name__ == "__main__":
    main()
