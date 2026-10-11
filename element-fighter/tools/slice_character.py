#!/usr/bin/env python3
"""
slice_character.py  —  Universal sprite sheet slicer for Element Fighter
=========================================================================
Works for ANY character sheet that follows the same vertical layout:
  - One animation per row
  - Text label on the LEFT of each row (auto-skipped)
  - Transparent or solid background (auto-removed)
  - Portrait orientation (taller than wide)

USAGE:
  python tools/slice_character.py <character_id> <sheet_path>

  Examples:
    python tools/slice_character.py aquara  tools/aquara-sheet.png
    python tools/slice_character.py terron  tools/terron-sheet.png
    python tools/slice_character.py blazor  tools/blazor-sheet.png

OUTPUT:
  assets/sprites/<character_id>/<anim>/<anim>-N.png  (96x96 transparent PNG)

ANIMATION ROW ORDER (must match top-to-bottom order in the sheet):
  idle(8) walk(8) run(8) jump(6) dash(6) block(4)
  punch(6) kick(6) special(8) ultimate(10) hurt(4) victory(6) defeat(6)

If your sheet has a different row order, edit ANIM_ORDER below.
"""

import sys, os, shutil
try:
    from PIL import Image
except ImportError:
    print("Run: pip install Pillow"); sys.exit(1)

# ── Animation row order + frame counts ───────────────────────────
ANIM_ORDER = [
    ("idle",      8),
    ("walk",      8),
    ("run",       8),
    ("jump",      6),
    ("dash",      6),
    ("block",     4),
    ("punch",     6),
    ("kick",      6),
    ("special",   8),
    ("ultimate", 10),
    ("hurt",      4),
    ("victory",   6),
    ("defeat",    6),
]

DISPLAY = 96   # output frame size (square)


# ── Step 1: Find row bands ────────────────────────────────────────
def find_row_bands(img):
    """Returns list of (y_start, y_end) for each content row."""
    w, h   = img.size
    pix    = img.load()
    bands  = []
    in_row = False
    y0     = 0
    for y in range(h):
        has = any(pix[x, y][3] > 20 for x in range(0, w, 3))
        if has and not in_row:
            y0 = y; in_row = True
        elif not has and in_row:
            if y - y0 > 10:   # ignore thin noise bands
                bands.append((y0, y))
            in_row = False
    if in_row and h - y0 > 10:
        bands.append((y0, h))
    return bands


# ── Step 2: Find frame x-positions within a row ───────────────────
def find_frames_in_row(img, y0, y1, n_frames):
    """
    Finds n_frames equally-meaningful x-ranges within the row,
    automatically skipping the left label area.
    Returns list of (x0, x1) tuples.
    """
    w   = img.size[0]
    pix = img.load()

    # Content columns (any non-transparent pixel in this row)
    content_cols = [x for x in range(w)
                    if any(pix[x, y][3] > 20 for y in range(y0, y1, 2))]
    if not content_cols:
        return []

    # Find gaps between content columns
    gaps = []
    for j in range(1, len(content_cols)):
        g = content_cols[j] - content_cols[j-1]
        if g > 8:
            gaps.append((g, content_cols[j-1], content_cols[j]))

    # The biggest gap separates the text label from the character frames
    if gaps:
        gaps.sort(reverse=True)
        frames_x_start = gaps[0][2]   # first column after the biggest gap
    else:
        frames_x_start = content_cols[0]

    frames_x_end = content_cols[-1] + 1
    total_w      = frames_x_end - frames_x_start

    if total_w <= 0 or n_frames <= 0:
        return []

    # Divide the frame region equally
    fw = total_w / n_frames
    result = []
    for i in range(n_frames):
        fx0 = int(frames_x_start + i * fw)
        fx1 = int(frames_x_start + (i + 1) * fw)
        result.append((fx0, fx1))

    return result


# ── Step 3: Crop + scale one frame ───────────────────────────────
def crop_frame(img, x0, y0, x1, y1):
    """Crop region, scale to DISPLAY×DISPLAY keeping transparency."""
    W, H = img.size
    x0 = max(0, min(x0, W));  x1 = max(0, min(x1, W))
    y0 = max(0, min(y0, H));  y1 = max(0, min(y1, H))
    if x1 <= x0 or y1 <= y0:
        return Image.new("RGBA", (DISPLAY, DISPLAY), (0,0,0,0))

    frame = img.crop((x0, y0, x1, y1))
    frame.thumbnail((DISPLAY, DISPLAY), Image.LANCZOS)

    canvas = Image.new("RGBA", (DISPLAY, DISPLAY), (0,0,0,0))
    ox = (DISPLAY - frame.width)  // 2
    oy = (DISPLAY - frame.height) // 2
    canvas.paste(frame, (ox, oy), frame)
    return canvas


# ── Step 4: Remove background if sheet is not already transparent ─
def make_transparent(img, tolerance=40):
    """
    If sheet corners are opaque, flood-fill replace the background colour
    with full transparency.
    """
    img = img.convert("RGBA")
    w, h = img.size
    pix  = img.load()

    # Check if already transparent (corners have alpha=0)
    corners = [pix[0,0], pix[w-1,0], pix[0,h-1], pix[w-1,h-1]]
    if all(c[3] == 0 for c in corners):
        return img   # already transparent — nothing to do

    # Compute average background colour from corners
    bg_r = int(sum(c[0] for c in corners) / 4)
    bg_g = int(sum(c[1] for c in corners) / 4)
    bg_b = int(sum(c[2] for c in corners) / 4)

    # Replace matching pixels
    import math
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            d = math.sqrt((r-bg_r)**2 + (g-bg_g)**2 + (b-bg_b)**2)
            if d < tolerance:
                pix[x, y] = (0, 0, 0, 0)
    return img


# ── Main ─────────────────────────────────────────────────────────
def slice_character(char_id, sheet_path, out_base):
    print(f"\nCharacter : {char_id.upper()}")
    print(f"Sheet     : {sheet_path}")

    raw   = Image.open(sheet_path).convert("RGBA")
    sheet = make_transparent(raw)
    W, H  = sheet.size
    print(f"Size      : {W}×{H} px\n")

    bands = find_row_bands(sheet)
    print(f"Detected {len(bands)} content rows  (need {len(ANIM_ORDER)})\n")

    if len(bands) < len(ANIM_ORDER):
        print("WARNING: fewer rows than expected. Some animations may be missing.")

    for idx, (anim_name, n_frames) in enumerate(ANIM_ORDER):
        out_dir = os.path.join(out_base, char_id, anim_name)
        os.makedirs(out_dir, exist_ok=True)

        # Clear old frames
        for old in os.listdir(out_dir):
            if old.endswith(".png"):
                os.remove(os.path.join(out_dir, old))

        if idx >= len(bands):
            print(f"  SKIP  {anim_name:<12} (no row band)")
            continue

        y0, y1 = bands[idx]
        frame_coords = find_frames_in_row(sheet, y0, y1, n_frames)

        if not frame_coords:
            print(f"  SKIP  {anim_name:<12} (no content found in row)")
            continue

        for i, (fx0, fx1) in enumerate(frame_coords):
            canvas   = crop_frame(sheet, fx0, y0, fx1, y1)
            out_path = os.path.join(out_dir, f"{anim_name}-{i+1}.png")
            canvas.save(out_path, "PNG")

        src_w = frame_coords[0][1] - frame_coords[0][0]
        print(f"  ✔  {anim_name:<12} {n_frames:2d} frames  "
              f"(row y={y0}–{y1} h={y1-y0}px  frame ~{src_w}×{y1-y0}px)")

    # Generate preview contact sheet
    preview_path = os.path.join(
        os.path.dirname(os.path.dirname(out_base)), "tools", f"{char_id}_preview.png"
    )
    _make_preview(out_base, char_id, preview_path)

    print(f"\nAll frames saved!")
    print(f"Preview   : {preview_path}")
    print(f"Next step : refresh index.html in Chrome\n")


def _make_preview(out_base, char_id, preview_path):
    """Generate a contact sheet of all saved frames."""
    try:
        from PIL import ImageDraw
        cell = DISPLAY; pad = 4; lw = 90; max_f = 10
        anims = [a for a, _ in ANIM_ORDER]
        out_w = lw + max_f * (cell + pad) + pad
        out_h = len(anims) * (cell + pad + 2) + pad
        canvas = Image.new("RGBA", (out_w, out_h), (15, 15, 25, 255))
        draw   = ImageDraw.Draw(canvas)

        for r, anim in enumerate(anims):
            y    = pad + r * (cell + pad + 2)
            adir = os.path.join(out_base, char_id, anim)
            draw.text((2, y + 38), anim[:8], fill=(180, 200, 255, 255))
            if not os.path.isdir(adir):
                continue
            files = sorted([f for f in os.listdir(adir) if f.endswith(".png")])
            for c, fname in enumerate(files):
                img = Image.open(os.path.join(adir, fname)).convert("RGBA")
                x   = lw + c * (cell + pad)
                draw.rectangle([x, y, x+cell, y+cell], (35, 35, 50, 255))
                canvas.paste(img, (x, y), img)
                draw.text((x+2, y+cell-12), str(c+1), fill=(255, 220, 50, 255))

        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        canvas.save(preview_path, "PNG")
    except Exception as e:
        print(f"  (Preview skipped: {e})")


# ── Entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        print("USAGE: python tools/slice_character.py <char_id> <sheet.png>")
        sys.exit(1)

    char_id    = sys.argv[1].lower().strip()
    sheet_path = sys.argv[2]

    if not os.path.exists(sheet_path):
        print(f"File not found: {sheet_path}")
        sys.exit(1)

    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    out_base     = os.path.join(project_root, "assets", "sprites")

    slice_character(char_id, sheet_path, out_base)
