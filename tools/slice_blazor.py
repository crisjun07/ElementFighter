#!/usr/bin/env python3
"""
slice_blazor.py  v5  —  Segment-exact slicer for 1024x1536 Blazor sheet
========================================================================
Uses pixel-accurate segment coordinates measured directly from the sheet.
Seg0 in every row = label text (skipped).
Seg1..N = actual character animation frames.

OUTPUT: assets/sprites/blazor/<anim>/<anim>-N.png  (96x96 RGBA, transparent bg)
USAGE : python tools/slice_blazor.py
"""

import sys, os
try:
    from PIL import Image
except ImportError:
    print("Run: pip install Pillow"); sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# EXACT FRAME COORDINATES  (from pixel scan of 1024x1536 sheet)
# Each frame: (x0, y0, x1, y1)
# ═══════════════════════════════════════════════════════════════
FRAMES = {

  # Band 0  y=7-114  IDLE (8 frames) — seg1..seg8
  "idle": [
    (137, 7, 200, 114),
    (222, 7, 283, 114),
    (304, 7, 366, 114),
    (387, 7, 449, 114),
    (472, 7, 536, 114),
    (560, 7, 621, 114),
    (644, 7, 705, 114),
    (728, 7, 792, 114),
  ],

  # Band 1  y=130-239  WALK (8 frames) — seg1..seg8
  "walk": [
    (216, 130, 280, 239),
    (303, 130, 367, 239),
    (384, 130, 447, 239),
    (469, 130, 531, 239),
    (553, 130, 618, 239),
    (641, 130, 702, 239),
    (726, 130, 791, 239),
    (814, 130, 879, 239),
  ],

  # Band 2  y=254-365  RUN (8 frames) — seg1..seg8
  "run": [
    (214, 254, 286, 365),
    (297, 254, 372, 365),
    (381, 254, 455, 365),
    (471, 254, 540, 365),
    (550, 254, 627, 365),
    (636, 254, 709, 365),
    (727, 254, 799, 365),
    (817, 254, 891, 365),
  ],

  # Band 3  y=376-485  JUMP (6 frames) — seg1..seg6
  "jump": [
    (135, 376, 203, 485),
    (234, 376, 303, 485),
    (343, 376, 413, 485),
    (447, 376, 521, 485),
    (564, 376, 639, 485),
    (682, 376, 751, 485),
  ],

  # Band 4  y=503-608  DASH (6 frames)
  # seg0=label(224px), seg1(102px), seg2(118px), seg3(112px), seg4(205px)=2 frames
  "dash": [
    (241, 503, 343, 608),   # frame 1
    (357, 503, 475, 608),   # frame 2
    (483, 503, 595, 608),   # frame 3
    (605, 503, 707, 608),   # frame 4  (seg4 left half)
    (707, 503, 810, 608),   # frame 5  (seg4 right half)
    (483, 503, 595, 608),   # frame 6  (hold frame 3 — fire pose)
  ],

  # Band 5  y=615-730  BLOCK (4 frames)
  "block": [
    (142, 615, 219, 730),
    (279, 615, 349, 730),
    (404, 615, 476, 730),
    (527, 615, 603, 730),
  ],

  # Band 6  y=741-852  PUNCH (6 frames)
  # Only 5 unique segs found — seg5 (x=647-743, w=96) is ONE frame
  # Frame 6 = hold frame 5
  "punch": [
    (238, 741, 316, 852),   # frame 1
    (338, 741, 412, 852),   # frame 2
    (435, 741, 525, 852),   # frame 3
    (547, 741, 624, 852),   # frame 4
    (647, 741, 743, 852),   # frame 5
    (547, 741, 624, 852),   # frame 6 = hold frame 4 (recovery)
  ],

  # Band 7  y=863-981  KICK (6 frames)
  # seg5 (x=638-751, w=113) = 2 kick frames — split at midpoint
  "kick": [
    (234, 863, 318, 981),   # frame 1
    (338, 863, 411, 981),   # frame 2
    (432, 863, 516, 981),   # frame 3
    (536, 863, 623, 981),   # frame 4
    (638, 863, 694, 981),   # frame 5  (seg5 left half)
    (694, 863, 751, 981),   # frame 6  (seg5 right half)
  ],

  # Band 8  y=999-1115  SPECIAL (8 frames)
  # seg1-4 = normal wind-up frames
  # seg5 (x=568-987, w=419) = fire blast — split into 4 equal parts (≈105px each)
  "special": [
    (233,  999, 304, 1115),  # frame 1
    (317,  999, 385, 1115),  # frame 2
    (401,  999, 469, 1115),  # frame 3
    (484,  999, 557, 1115),  # frame 4
    (570,  999, 675, 1115),  # frame 5  blast q1
    (675,  999, 780, 1115),  # frame 6  blast q2
    (780,  999, 883, 1115),  # frame 7  blast q3
    (883,  999, 987, 1115),  # frame 8  blast q4
  ],

  # Band 9  y=1122-1234  ULTIMATE (10 frames)
  # seg1(73), seg2(150)=2frames, seg3(163)=2frames, seg4(71), seg5(261)=4frames
  "ultimate": [
    (240, 1122, 313, 1234),  # frame 1   seg1
    (327, 1122, 398, 1234),  # frame 2   seg2 left
    (404, 1122, 476, 1234),  # frame 3   seg2 right
    (488, 1122, 563, 1234),  # frame 4   seg3 left
    (573, 1122, 650, 1234),  # frame 5   seg3 right
    (670, 1122, 741, 1234),  # frame 6   seg4
    (751, 1122, 816, 1234),  # frame 7   seg5 q1
    (817, 1122, 882, 1234),  # frame 8   seg5 q2
    (883, 1122, 947, 1234),  # frame 9   seg5 q3 (explosion build)
    (948, 1122,1012, 1234),  # frame 10  seg5 q4 (full explosion)
  ],

  # Band 10  y=1243-1335  HURT (4 frames)
  "hurt": [
    (243, 1243, 310, 1335),
    (359, 1243, 428, 1335),
    (467, 1243, 530, 1335),
    (467, 1243, 530, 1335),  # frame 4 = hold frame 3
  ],

  # Band 11  y=1336-1514  VICTORY (top) + DEFEAT (bottom)
  # Vertical gap at y=1444-1460 separates the two animations
  # VICTORY: y=1336-1444  6 frames
  "victory": [
    (242, 1336, 299, 1444),  # frame 1  seg1
    (336, 1336, 407, 1444),  # frame 2  seg2 f1
    (446, 1336, 519, 1444),  # frame 3  seg2 f2
    (549, 1336, 611, 1444),  # frame 4  seg2 f3
    (654, 1336, 715, 1444),  # frame 5  seg2 f4
    (715, 1336, 795, 1444),  # frame 6  seg2 f5
  ],
  # DEFEAT: y=1460-1514  6 frames
  "defeat": [
    (237, 1460, 326, 1514),  # frame 1
    (340, 1460, 410, 1514),  # frame 2  (seg2 left)
    (410, 1460, 469, 1514),  # frame 3  (seg2 mid-left)
    (478, 1460, 572, 1514),  # frame 4
    (586, 1460, 685, 1514),  # frame 5
    (688, 1460, 795, 1514),  # frame 6
  ],
}

DISPLAY = 96   # all output frames scaled to this square size

# ── Dash fix: frame 6 = copy of frame 3 ─────────────────────────
# (handled below by skipping zero-width entries)


def crop_and_scale(sheet, x0, y0, x1, y1):
    """Crop one frame, scale to DISPLAY×DISPLAY, keep transparency."""
    W, H = sheet.size
    x0 = max(0, min(x0, W));  x1 = max(0, min(x1, W))
    y0 = max(0, min(y0, H));  y1 = max(0, min(y1, H))
    if x1 <= x0 or y1 <= y0:
        return Image.new("RGBA", (DISPLAY, DISPLAY), (0,0,0,0))

    frame = sheet.crop((x0, y0, x1, y1))
    frame.thumbnail((DISPLAY, DISPLAY), Image.LANCZOS)

    canvas = Image.new("RGBA", (DISPLAY, DISPLAY), (0,0,0,0))
    ox = (DISPLAY - frame.width)  // 2
    oy = (DISPLAY - frame.height) // 2
    canvas.paste(frame, (ox, oy), frame)
    return canvas


def slice_sheet(sheet_path, out_base):
    sheet = Image.open(sheet_path).convert("RGBA")
    W, H  = sheet.size
    print(f"Sheet: {W}×{H} px\n")

    anim_order = ["idle","walk","run","jump","dash","block",
                  "punch","kick","special","ultimate","hurt","victory","defeat"]

    for anim in anim_order:
        coords = FRAMES[anim]
        out_dir = os.path.join(out_base, anim)
        os.makedirs(out_dir, exist_ok=True)

        # Clear old frames
        for old in os.listdir(out_dir):
            if old.endswith(".png"):
                os.remove(os.path.join(out_dir, old))

        saved = 0
        for i, (x0,y0,x1,y1) in enumerate(coords):
            if x1 <= x0:   # zero-width = skip / duplicate previous
                if saved > 0:
                    prev = os.path.join(out_dir, f"{anim}-{saved}.png")
                    dest = os.path.join(out_dir, f"{anim}-{i+1}.png")
                    import shutil; shutil.copy(prev, dest)
                    saved += 1
                continue

            canvas = crop_and_scale(sheet, x0, y0, x1, y1)
            out_path = os.path.join(out_dir, f"{anim}-{i+1}.png")
            canvas.save(out_path, "PNG")
            saved += 1

        fw = coords[0][2] - coords[0][0]
        fh = coords[0][3] - coords[0][1]
        print(f"  ✔  {anim:<12} {saved:2d} frames  (src ~{fw}×{fh}px → {DISPLAY}×{DISPLAY}px)")

    print(f"\nSaved to: {out_base}")
    print("Refresh index.html to see Blazor with real sprites!")


if __name__ == "__main__":
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sheet_path   = sys.argv[1] if len(sys.argv) > 1 \
                   else os.path.join(script_dir, "blazor-sheet.png")

    if not os.path.exists(sheet_path):
        print(f"Not found: {sheet_path}")
        sys.exit(1)

    out_base = os.path.join(project_root, "assets", "sprites", "blazor")
    slice_sheet(sheet_path, out_base)
