#!/usr/bin/env python3
# Builds the hero animation inputs from the beach picture:
#   ./hero/make-hero.py hero/beach.jpg hero/beach-mask.png hero/beach-clean.jpg
# The polygons (people, mountains) are hand-traced on a 1195x896 grid of this one picture.

import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
src, outmask, outclean = sys.argv[1:4]
full = Image.open(src).convert('RGB'); full.thumbnail((2048, 2048), Image.LANCZOS)
FW, FH = full.size
W, H = 1195, 896  # grid coords used for polygons
im = np.asarray(full.resize((W, H)), dtype=float)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
yy = np.arange(H)[:, None] * np.ones((1, W))
people=[(285,455),(320,385),(345,368),(395,370),(420,383),(470,385),(500,348),(540,346),(575,380),(590,372),(630,372),(645,392),(660,345),(700,342),(745,405),(750,388),(785,383),(805,418),(825,365),(870,362),(885,420),(918,450),(932,500),(918,540),(912,640),(898,700),(882,722),(872,748),(828,748),(808,705),(790,712),(720,722),(640,718),(560,714),(530,695),(522,742),(482,772),(452,818),(418,818),(408,785),(345,822),(312,812),(258,806),(248,762),(208,742),(212,700),(238,640),(272,560),(280,510)]
mtn=[(0,384),(150,378),(205,366),(245,366),(290,360),(325,363),(365,374),(420,380),(520,392),(520,404),(0,404)]
def poly(pts, blur):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(blur)), dtype=float) / 255
def blur(a, rad):
    return np.asarray(Image.fromarray(np.clip(a * 255, 0, 255).astype('uint8')).filter(ImageFilter.GaussianBlur(rad)), dtype=float) / 255
keep = 1 - np.clip(poly(people, 6) * 1.6, 0, 1)
sky = np.clip((396 - yy) / 4, 0, 1) * (1 - np.clip(poly(mtn, 2) * 1.5, 0, 1))
shore = np.clip((yy - 560) / 50, 0, 1)                  # wash zone: beach below the breakers
watercol = np.clip(((b - r) + 15) / 30, 0, 1)
whiteness = np.clip((np.minimum(np.minimum(r, g), b) - 195) / 30, 0, 1)
water = blur(np.maximum(watercol, whiteness) * np.clip((yy - 402) / 18, 0, 1), 4) * (1 - shore)
foam = np.clip(blur(whiteness, 1.2) * 1.3, 0, 1) * shore
# r: sky above the horizon, shore zone below it (they never overlap); g: sea; b: shore foam
out = np.stack([(sky + shore) * keep, water * keep, foam * keep], -1)
Image.fromarray((out * 255).astype('uint8')).resize((1024, 768), Image.BILINEAR).save(outmask, optimize=True)
# Clean plate: the beach with the shore foam painted out (normalized convolution of the non-foam pixels).
fa = np.asarray(Image.fromarray((foam * 255).astype('uint8')).resize((FW, FH), Image.BILINEAR), dtype=float)[..., None] / 255
fa = np.clip(fa * 1.5, 0, 1)
img = np.asarray(full, dtype=float) / 255
fill = np.zeros_like(img); wsum = np.zeros_like(fa)
known = 1 - fa
for rad in (6, 14, 30):
    def box(a, k, axis):
        pad = [(0, 0)] * a.ndim; pad[axis] = (k + 1, k)
        c = np.cumsum(np.pad(a, pad, mode='edge'), axis=axis)
        n = a.shape[axis]
        return (np.take(c, range(2 * k + 1, 2 * k + 1 + n), axis) - np.take(c, range(0, n), axis)) / (2 * k + 1)
    def gb(a, ch):
        for _ in range(3):  # three box passes approximate a gaussian
            a = box(box(a, rad, 0), rad, 1)
        return a
    num = gb(img * known, 3); den = gb(known, 1)
    est = num / np.maximum(den, 1e-3)
    w = (den > .05) * (1 - wsum)
    fill += est * w; wsum += w
clean = img * known + fill * fa
Image.fromarray((np.clip(clean, 0, 1) * 255).astype('uint8')).save(outclean, quality=80, optimize=True, progressive=True)
