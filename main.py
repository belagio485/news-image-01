#!/usr/bin/env python3
"""news-image-01: sum up the world's news of Friday 13 November 2026 in one image.

Draws a 1024x1024 editorial broadsheet, deterministically, with stdlib only:
own framebuffer, own 5x7 bitmap font, own PNG encoder (zlib/struct).
No network, no randomness, no wall clock: the same run writes the same bytes.

Stories (all reported on 13 November 2026):
  1. US Senate Banking Committee summons Nvidia CEO Jensen Huang and
     Commerce Secretary Howard Lutnick to testify.
  2. Zelensky meets US envoys; Europe is brought into the Ukraine peace talks.
  3. FBI: North Korean hackers stole $400m in crypto using deepfake video calls.
  4. Strike on Nasser Hospital in Gaza kills six, including a surgeon and a child.
Ticker: Microsoft 365 outage drags into a second day; eight dead in the
Brooklyn building collapse; tankers hit in the Strait of Hormuz.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 231)
NAVY = (16, 41, 75)
NAVY_DK = (10, 28, 52)
INK = (24, 24, 24)
WHITE = (255, 255, 255)
OFFWHITE = (238, 236, 228)
RED = (192, 57, 43)
RED_DK = (139, 26, 26)
GOLD = (212, 175, 55)
GOLD_DK = (176, 141, 38)
SKY = (191, 217, 232)
SKY_LT = (214, 232, 240)
BLUE = (0, 87, 183)
YELLOW = (255, 215, 0)
EU_BLUE = (0, 51, 153)
GREY = (120, 124, 128)
GREY_LT = (200, 204, 208)
GREY_DK = (74, 78, 82)
GREEN = (46, 125, 50)
GREEN_LT = (102, 187, 106)
BROWN = (122, 82, 46)
BROWN_DK = (90, 60, 32)
SKIN = (232, 190, 150)
TEAL = (38, 120, 120)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = ink, '.' = blank.
FONT = {
    'A': ("..#..", ".#.#.", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    '/': ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    '&': (".###.", "#...#", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '•': (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]
                i += 3

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            for t in range(thick):
                self.px(x + t, y, c)
                self.px(x, y + t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.hline(cx - dx, cy + dy, 2 * dx + 1, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for dy in range(-ry, ry + 1):
            dx = int(rx * math.sqrt(max(0.0, 1.0 - (dy * dy) / float(ry * ry))))
            self.hline(cx - dx, cy + dy, 2 * dx + 1, c)

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        for y in range(ay, cy + 1):
            if y < by:
                t1 = (y - ay) / float(by - ay) if by != ay else 0.0
                xa = ax + (bx - ax) * t1
            else:
                t1 = (y - by) / float(cy - by) if cy != by else 0.0
                xa = bx + (cx - bx) * t1
            t2 = (y - ay) / float(cy - ay)
            xb = ax + (cx - ax) * t2
            lo, hi = (xa, xb) if xa < xb else (xb, xa)
            self.hline(int(lo), y, int(hi) - int(lo) + 1, c)

    def poly(self, points, c):
        # Fan triangulation; all polygons used here are convex.
        for i in range(1, len(points) - 1):
            self.tri(points[0][0], points[0][1],
                     points[i][0], points[i][1],
                     points[i + 1][0], points[i + 1][1], c)

    def text(self, x, y, s, scale, c, center=False):
        s = s.upper()
        if center:
            x -= text_width(s, scale) // 2
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '#':
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale

    def frame(self, x, y, w, h, c, t=3):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)


# ---------------------------------------------------------------- panels
PX = [16, 520]          # panel left edges
PY = [134, 540]         # panel top edges
PW = 488
PH = 390
ART_H = 296             # illustration height inside a panel
CAP_H = PH - ART_H      # caption band height


def panel_shell(c, col, row, bg):
    x, y = PX[col], PY[row]
    c.rect(x, y, PW, PH, bg)
    c.frame(x, y, PW, PH, NAVY, 3)
    return x, y


def caption(c, col, row, line1, line2):
    x, y = PX[col], PY[row]
    cy = y + ART_H
    c.rect(x + 3, cy, PW - 6, CAP_H - 3, WHITE)
    c.hline(x + 3, cy, PW - 6, NAVY)
    c.text(x + PW // 2, cy + 12, line1, 4, NAVY, center=True)
    c.text(x + PW // 2, cy + 48, line2, 4, NAVY, center=True)


def draw_capitol(c, x, y):
    """US Capitol dome + hearing desk, inside panel 1."""
    # dome
    c.ellipse(x + 150, y + 150, 92, 66, WHITE)
    c.rect(x + 58, y + 148, 184, 16, WHITE)
    # drum + columns
    c.rect(x + 84, y + 164, 132, 46, WHITE)
    for cx in range(92, 208, 16):
        c.vline(x + cx, y + 166, 42, GREY_LT)
    # base + steps
    c.rect(x + 48, y + 210, 204, 12, OFFWHITE)
    c.rect(x + 36, y + 222, 228, 10, GREY_LT)
    # flag on top
    c.vline(x + 150, y + 66, 22, INK)
    c.rect(x + 150, y + 66, 26, 14, RED)
    # hearing desk
    c.rect(x + 20, y + 246, 448, 34, BROWN)
    c.rect(x + 20, y + 246, 448, 6, BROWN_DK)


def draw_chair_jacket(c, x, y):
    """Empty witness chair with a black leather jacket draped over it."""
    # chair back + seat + legs
    c.rect(x + 210, y + 168, 74, 62, BROWN_DK)
    c.rect(x + 206, y + 228, 82, 12, BROWN_DK)
    c.rect(x + 212, y + 240, 8, 34, BROWN_DK)
    c.rect(x + 272, y + 240, 8, 34, BROWN_DK)
    # jacket draped over the back: black shape with collar notch
    c.poly([(x + 208, y + 172), (x + 286, y + 172), (x + 292, y + 236),
            (x + 262, y + 236), (x + 252, y + 206), (x + 242, y + 236),
            (x + 202, y + 236)], (18, 18, 18))
    # jacket sheen + zipper
    c.line(x + 222, y + 180, x + 228, y + 232, (70, 70, 70), 2)
    c.line(x + 247, y + 196, x + 247, y + 234, GOLD_DK, 2)


def draw_falling_arrow(c, x, y):
    """Red falling stock arrow + microchip, panel 1 right side."""
    # small falling chart bars
    for i, bh in enumerate([26, 20, 14, 8]):
        c.rect(x + 330 + i * 16, y + 96 - bh, 10, bh, TEAL)
    # big red down arrow
    c.line(x + 330, y + 40, x + 420, y + 130, RED, 7)
    c.poly([(x + 420, y + 130), (x + 388, y + 118), (x + 402, y + 148)], RED)
    # microchip
    cx, cy = x + 398, y + 196
    c.rect(cx - 34, cy - 34, 68, 68, (32, 38, 48))
    for i in range(4):
        c.rect(cx - 26 + i * 15, cy - 44, 7, 10, GOLD)
        c.rect(cx - 26 + i * 15, cy + 34, 7, 10, GOLD)
        c.rect(cx - 44, cy - 26 + i * 15, 10, 7, GOLD)
        c.rect(cx + 34, cy - 26 + i * 15, 10, 7, GOLD)
    c.rect(cx - 20, cy - 20, 40, 40, (58, 70, 86))
    c.rect(cx - 10, cy - 10, 20, 20, GOLD)


def draw_panel1(c):
    x, y = panel_shell(c, 0, 0, SKY_LT)
    c.rect(x + 3, y + 3, PW - 6, ART_H - 3, SKY)
    draw_capitol(c, x, y)
    draw_chair_jacket(c, x, y)
    draw_falling_arrow(c, x, y)
    caption(c, 0, 0, "SENATE SUMMONS", "EX-NVIDIA CEO")


def draw_flag(c, x, y, w, h, kind):
    c.vline(x - 4, y - 14, h + 28, INK)
    if kind == 'UA':
        c.rect(x, y, w, h // 2, BLUE)
        c.rect(x, y + h // 2, w, h - h // 2, YELLOW)
    elif kind == 'EU':
        c.rect(x, y, w, h, EU_BLUE)
        for k in range(12):
            a = 2 * math.pi * k / 12.0
            sx = x + w // 2 + int(22 * math.cos(a))
            sy = y + h // 2 + int(14 * math.sin(a))
            c.circle(sx, sy, 2, YELLOW)
    else:  # RU
        c.rect(x, y, w, h // 3, WHITE)
        c.rect(x, y + h // 3, w, h // 3, BLUE)
        c.rect(x, y + 2 * h // 3, w, h - 2 * h // 3, RED)


def draw_dove(c, x, y):
    """White dove with an olive sprig, flying below the flags, over the table."""
    c.ellipse(x + 300, y + 126, 46, 23, WHITE)
    c.circle(x + 336, y + 104, 13, WHITE)
    c.tri(x + 347, y + 100, x + 364, y + 106, x + 347, y + 110, GOLD)
    c.circle(x + 340, y + 100, 2, INK)
    # raised wing
    c.poly([(x + 272, y + 122), (x + 292, y + 74), (x + 322, y + 114)], WHITE)
    c.poly([(x + 280, y + 120), (x + 294, y + 86), (x + 312, y + 112)], GREY_LT)
    # tail
    c.poly([(x + 238, y + 122), (x + 216, y + 108), (x + 220, y + 134)], WHITE)
    # olive sprig in beak
    c.line(x + 360, y + 108, x + 390, y + 126, GREEN, 3)
    for ox, oy in [(368, 112), (376, 118), (382, 124)]:
        c.ellipse(x + ox, y + oy, 7, 4, GREEN_LT)


def draw_table(c, x, y):
    c.rect(x + 60, y + 190, 368, 16, BROWN)
    c.rect(x + 76, y + 206, 12, 66, BROWN_DK)
    c.rect(x + 400, y + 206, 12, 66, BROWN_DK)
    # document on the table
    c.rect(x + 190, y + 152, 110, 40, WHITE)
    c.frame(x + 190, y + 152, 110, 40, INK, 2)
    c.hline(x + 200, y + 164, 90, INK)
    c.hline(x + 200, y + 174, 70, INK)
    c.hline(x + 200, y + 184, 80, INK)
    # pen
    c.line(x + 316, y + 186, x + 344, y + 170, RED, 3)


def draw_panel2(c):
    x, y = panel_shell(c, 0, 1, (226, 238, 226))
    c.rect(x + 3, y + 3, PW - 6, ART_H - 3, (226, 238, 226))
    draw_flag(c, x + 60, y + 40, 92, 56, 'UA')
    draw_flag(c, x + 196, y + 40, 92, 56, 'EU')
    draw_flag(c, x + 332, y + 40, 92, 56, 'RU')
    draw_dove(c, x, y)
    draw_table(c, x, y)
    caption(c, 0, 1, "EUROPE JOINS", "UKRAINE PEACE TALKS")


def draw_fbi_shield(c, x, y):
    cx, cy = x + 96, y + 96
    c.poly([(cx - 52, cy - 58), (cx + 52, cy - 58), (cx + 52, cy + 6),
            (cx, cy + 62), (cx - 52, cy + 6)], GOLD)
    c.poly([(cx - 40, cy - 46), (cx + 40, cy - 46), (cx + 40, cy + 2),
            (cx, cy + 48), (cx - 40, cy + 2)], (24, 54, 120))
    c.text(cx, cy - 8, "FBI", 3, WHITE, center=True)
    c.rect(cx - 26, cy + 16, 52, 4, GOLD)


def draw_laptop(c, x, y):
    # screen
    c.rect(x + 210, y + 40, 220, 140, (40, 44, 52))
    c.rect(x + 218, y + 48, 204, 124, (24, 30, 40))
    # deepfake face: skin circle, split by glitch slices
    fx, fy = x + 320, y + 110
    c.circle(fx, fy, 34, SKIN)
    c.circle(fx - 13, fy - 8, 4, INK)
    c.circle(fx + 13, fy - 8, 4, INK)
    c.line(fx - 8, fy + 14, fx + 8, fy + 14, (120, 40, 40), 3)
    # glitch: offset colour slices across the face
    c.rect(fx - 34, fy - 16, 68, 6, (0, 220, 180))
    c.rect(fx - 20, fy + 2, 40, 5, (220, 0, 120))
    c.rect(fx - 34, fy + 18, 68, 4, (0, 180, 255))
    # crack lines
    c.line(fx - 30, fy - 30, fx - 6, fy - 2, WHITE, 2)
    c.line(fx - 6, fy - 2, fx + 18, fy - 22, WHITE, 2)
    c.line(fx + 10, fy + 6, fx + 30, fy + 26, WHITE, 2)
    # base + keyboard
    c.rect(x + 196, y + 180, 248, 12, (90, 94, 100))
    c.rect(x + 186, y + 192, 268, 8, (70, 74, 80))
    # spilling gold coins
    for i, (ox, oy, r) in enumerate([(236, 214, 13), (262, 226, 11),
                                     (292, 216, 12), (322, 230, 11),
                                     (352, 218, 12), (384, 228, 10),
                                     (410, 214, 11)]):
        c.circle(x + ox, y + oy, r, GOLD)
        c.circle(x + ox, y + oy, r - 4, GOLD_DK)
        c.circle(x + ox, y + oy, 3, GOLD)


def draw_panel3(c):
    x, y = panel_shell(c, 1, 0, NAVY_DK)
    c.rect(x + 3, y + 3, PW - 6, ART_H - 3, NAVY_DK)
    draw_fbi_shield(c, x, y)
    draw_laptop(c, x, y)
    caption(c, 1, 0, "FBI: N. KOREA HACK", "$400M VIA DEEPFAKES")


def draw_hospital(c, x, y):
    # main building
    c.rect(x + 60, y + 96, 300, 176, WHITE)
    c.frame(x + 60, y + 96, 300, 176, GREY, 3)
    # red cross sign
    c.rect(x + 186, y + 52, 48, 48, WHITE)
    c.frame(x + 186, y + 52, 48, 48, RED, 2)
    c.rect(x + 204, y + 60, 12, 32, RED)
    c.rect(x + 194, y + 70, 32, 12, RED)
    # windows
    for r in range(3):
        for col in range(5):
            c.rect(x + 82 + col * 56, y + 118 + r * 48, 34, 28, (70, 110, 150))
    # door
    c.rect(x + 196, y + 224, 28, 48, (60, 80, 110))
    # smoke plume
    for (sx, sy, sr, col) in [(x + 92, y + 70, 16, GREY),
                              (x + 78, y + 46, 20, GREY_LT),
                              (x + 96, y + 22, 24, (220, 222, 224)),
                              (x + 118, y + 2, 18, (228, 230, 232))]:
        c.circle(sx, sy, sr, col)
    # rubble at the base
    c.poly([(x + 60, y + 272), (x + 130, y + 252), (x + 190, y + 272)], GREY_LT)
    c.poly([(x + 300, y + 272), (x + 340, y + 256), (x + 380, y + 272)], GREY_LT)


def draw_ambulance(c, x, y):
    ax, ay = x + 330, y + 208
    c.rect(ax, ay, 120, 52, WHITE)
    c.frame(ax, ay, 120, 52, RED, 3)
    c.rect(ax + 88, ay + 12, 32, 52, WHITE)
    c.frame(ax + 88, ay + 12, 32, 52, RED, 2)
    # red cross on the side
    c.rect(ax + 14, ay + 18, 10, 28, RED)
    c.rect(ax + 5, ay + 27, 28, 10, RED)
    # window + light
    c.rect(ax + 94, ay + 18, 20, 16, SKY)
    c.rect(ax + 40, ay - 8, 40, 8, RED)
    # wheels
    for wx in (ax + 24, ax + 96):
        c.circle(wx, ay + 62, 11, INK)
        c.circle(wx, ay + 62, 5, GREY_LT)


def draw_panel4(c):
    x, y = panel_shell(c, 1, 1, (232, 234, 236))
    c.rect(x + 3, y + 3, PW - 6, ART_H - 3, (232, 234, 236))
    draw_hospital(c, x, y)
    draw_ambulance(c, x, y)
    caption(c, 1, 1, "GAZA HOSPITAL", "STRIKE KILLS 6")


# ---------------------------------------------------------------- masthead + ticker
def draw_masthead(c):
    c.rect(8, 8, W - 16, 110, NAVY)
    c.frame(8, 8, W - 16, 110, GOLD, 2)
    c.text(W // 2, 24, "13 NOVEMBER 2026", 6, WHITE, center=True)
    c.hline(220, 84, W - 440, GOLD)
    c.text(W // 2, 92, "THE WORLD'S NEWS IN ONE IMAGE", 3, GOLD, center=True)


def draw_ticker(c):
    c.rect(8, 946, W - 16, 70, RED_DK)
    c.frame(8, 946, W - 16, 70, NAVY, 2)
    c.text(W // 2, 972,
           "MICROSOFT OUTAGE • BROOKLYN: 8 DEAD • HORMUZ TANKERS HIT",
           2, WHITE, center=True)


# ---------------------------------------------------------------- PNG encoder
def png_bytes(c):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += c.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    c = Canvas(W, H, PAPER)
    c.frame(0, 0, W, H, NAVY, 8)
    draw_masthead(c)
    draw_panel1(c)
    draw_panel2(c)
    draw_panel3(c)
    draw_panel4(c)
    draw_ticker(c)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(png_bytes(c))


if __name__ == "__main__":
    main()
