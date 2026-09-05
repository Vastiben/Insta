"""
Retouche paramétrée par preset (voir presets/styles.json).
Implémente le plan de docs/research/photo-retouching-methods.md : crop sur point
focal, balance des blancs gray-world atténuée, courbe en S, split-tone,
saturation plafonnée avec garde-fou clipping, unsharp mask deux passes
(netteté fine + clarté grand rayon), vignette recentrée, export Lanczos.

Usage:
    python3 retouch.py <source.jpg> <dest.jpg> <preset_id> [focus_x] [focus_y]

focus_x/focus_y: position relative [0,1] du sujet (visage) dans l'image
SOURCE (avant tout crop) — repérée à l'œil ou par l'agent qui appelle ce
script après avoir regardé la photo. Par défaut (0.5, 0.38) — tiers
supérieur, centre horizontal.
"""
import json
import sys
from pathlib import Path

import numpy as np
import cv2
from PIL import Image

PRESETS_PATH = Path(__file__).resolve().parent.parent / "presets" / "styles.json"


def load_preset(preset_id: str) -> dict:
    data = json.loads(PRESETS_PATH.read_text())
    for style in data["styles"]:
        if style["id"] == preset_id:
            return style
    raise ValueError(f"Preset inconnu: {preset_id}. Disponibles: "
                      f"{[s['id'] for s in data['styles']]}")


def crop_to_ratio(img: Image.Image, target_ratio: float, focus: tuple[float, float]) -> Image.Image:
    w, h = img.size
    src_ratio = w / h
    if src_ratio > target_ratio:
        new_w = int(h * target_ratio)
        cx = int(w * focus[0])
        left = max(0, min(w - new_w, cx - new_w // 2))
        box = (left, 0, left + new_w, h)
    else:
        new_h = int(w / target_ratio)
        cy = int(h * focus[1])
        top = max(0, min(h - new_h, cy - new_h // 2))
        box = (0, top, w, top + new_h)
    return img.crop(box)


def gray_world_wb(arr: np.ndarray, strength: float) -> np.ndarray:
    arr = arr.astype(np.float64)
    means = arr.reshape(-1, 3).mean(axis=0)
    target = means.mean()
    scale = target / np.clip(means, 1, None)
    corrected = arr * scale
    out = arr * (1 - strength) + corrected * strength
    return np.clip(out, 0, 255).astype(np.uint8)


def build_curve_lut(points) -> np.ndarray:
    xs, ys = zip(*points)
    x_full = np.arange(256)
    lut = np.interp(x_full, xs, ys)
    return np.clip(lut, 0, 255).astype(np.uint8)


def apply_curve(arr: np.ndarray, lut: np.ndarray) -> np.ndarray:
    out = arr.copy()
    for c in range(3):
        out[..., c] = lut[arr[..., c]]
    return out


def luminance_masks(arr: np.ndarray):
    lum = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]) / 255.0
    shadow_mask = np.clip(1.0 - lum / 0.5, 0, 1)
    highlight_mask = np.clip((lum - 0.5) / 0.5, 0, 1)
    return shadow_mask, highlight_mask


def split_tone(arr, shadow_rgb, highlight_rgb, shadow_mask, highlight_mask):
    arr = arr.astype(np.float64)
    for c, (so, ho) in enumerate(zip(shadow_rgb, highlight_rgb)):
        arr[..., c] += shadow_mask * so + highlight_mask * ho
    return np.clip(arr, 0, 255).astype(np.uint8)


def capped_saturation(arr: np.ndarray, factor: float, clip_budget: float = 0.02) -> np.ndarray:
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV).astype(np.float32)
    skin_hue = (hsv[..., 0] >= 3) & (hsv[..., 0] <= 20)
    local_factor = np.where(skin_hue, 1 + (factor - 1) * 0.4, factor)
    s = hsv[..., 1] * local_factor
    clipped_ratio = np.mean(np.clip(s, 0, 255) >= 254)
    if clipped_ratio > clip_budget:
        s = hsv[..., 1] * (1 + (factor - 1) * 0.5)
    hsv[..., 1] = np.clip(s, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)


def unsharp_mask(arr, radius, amount, threshold):
    arr_f = arr.astype(np.float32)
    blurred = cv2.GaussianBlur(arr_f, (0, 0), radius)
    diff = arr_f - blurred
    mask = np.abs(diff) >= threshold
    sharpened = arr_f + diff * amount
    out = np.where(mask, sharpened, arr_f)
    return np.clip(out, 0, 255).astype(np.uint8)


def clarity(arr, radius, amount):
    arr_f = arr.astype(np.float32)
    blurred = cv2.GaussianBlur(arr_f, (0, 0), radius)
    diff = arr_f - blurred
    out = arr_f + diff * amount
    return np.clip(out, 0, 255).astype(np.uint8)


def focal_vignette(arr, focus, opacity):
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    fx, fy = focus[0] * w, focus[1] * h
    max_r = np.sqrt(max(fx, w - fx) ** 2 + max(fy, h - fy) ** 2)
    dist = np.sqrt((xx - fx) ** 2 + (yy - fy) ** 2) / max_r
    darken = np.clip((dist - 0.35) / 0.65, 0, 1) * opacity
    out = arr.astype(np.float64) * (1 - darken[..., None])
    return np.clip(out, 0, 255).astype(np.uint8)


def retouch(src: str, dst: str, preset_id: str, focus=(0.5, 0.38), rotate180=False):
    style = load_preset(preset_id)

    pil_img = Image.open(src).convert("RGB")
    if rotate180:
        pil_img = pil_img.rotate(180)

    target_ratio = style["crop_ratio"][0] / style["crop_ratio"][1]
    pil_img = crop_to_ratio(pil_img, target_ratio, focus)
    focus_cropped = (0.5, min(0.45, focus[1]))  # le crop recentre déjà en x

    arr = np.array(pil_img)
    arr = gray_world_wb(arr, style["white_balance_strength"])
    arr = apply_curve(arr, build_curve_lut(style["curve_points"]))

    shadow_mask, highlight_mask = luminance_masks(arr)
    st = style["split_tone"]
    arr = split_tone(arr, st["shadow_rgb"], st["highlight_rgb"], shadow_mask, highlight_mask)

    arr = capped_saturation(arr, style["saturation_factor"])

    sh = style["sharpen"]
    arr = unsharp_mask(arr, sh["radius"], sh["amount"], sh["threshold"])
    cl = style["clarity"]
    arr = clarity(arr, cl["radius"], cl["amount"])

    arr = focal_vignette(arr, focus_cropped, style["vignette_opacity"])

    out_img = Image.fromarray(arr)
    target_w = 1080
    target_h = int(target_w * out_img.height / out_img.width)
    out_img = out_img.resize((target_w, target_h), Image.LANCZOS)
    out_img.save(dst, quality=92, subsampling=0)
    return out_img.size


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    src, dst, preset_id = sys.argv[1], sys.argv[2], sys.argv[3]
    fx = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    fy = float(sys.argv[5]) if len(sys.argv) > 5 else 0.38
    size = retouch(src, dst, preset_id, focus=(fx, fy))
    print(f"OK preset={preset_id} focus=({fx},{fy}) -> {dst} {size}")
