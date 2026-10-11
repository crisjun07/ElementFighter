#!/usr/bin/env python3
"""
slice_frostia_new.py  v2
========================
Slices the new Frostia sprite sheet using FLOOD-FILL background removal.
Instead of colour-tolerance (which eats skin pixels), we:
  1. Start from every edge pixel of the sheet.
  2. Flood-fill outward through pixels that match the background.
  3. Only those connected-to-edge pixels become transparent.
  4. Interior white/light pixels (face, skin, highlights) are PRESERVED.

Sheet: 1536x1024, bg=rgb(245,246,246)
Grid:  13 columns × 9 rows = 117 frames
Cell:  71×104 px output canvas
"""
from PIL import Image
import os
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Exact grid (pixel-scanned) ────────────────────────────────────
ROW_BANDS = [
    (14,  112),   # idle
    (137, 231),   # walk
    (254, 347),   # run
    (365, 469),   # jump
    (481, 585),   # attack
    (606, 707),   # special
    (720, 818),   # ultimate
    (824, 924),   # hurt
    (947, 1003),  # defeat
]
ANIM_ORDER = ['idle','walk','run','jump','attack','special','ultimate','hurt','defeat']

FRAME_X = [
    (19,  83),
    (124, 190),
    (228, 292),
    (330, 395),
    (436, 501),
    (542, 611),
    (643, 714),
    (758, 824),
    (867, 931),
    (973, 1039),
    (1082, 1140),
    (1185, 1248),
    (1282, 1344),
]

MAX_FW = max(x1-x0 for x0,x1 in FRAME_X)
MAX_FH = max(y1-y0 for y0,y1 in ROW_BANDS)

BG      = (245, 246, 246)
BG_TOL  = 22   # tight tolerance — only clear very close bg colours

# ─────────────────────────────────────────────────────────────────
def flood_remove_bg(img, bg=BG, tol=BG_TOL):
    """
    Flood-fill background removal starting from ALL edge pixels.
    Only pixels CONNECTED to the sheet edge that are within tolerance
    of the bg colour become transparent.
    Interior pixels (face, highlights, ice) are never touched.
    """
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W, H = img.size
    r0,g0,b0 = bg
    t2 = tol * tol

    def matches_bg(idx):
        r,g,b,a = data[idx]
        return (r-r0)**2 + (g-g0)**2 + (b-b0)**2 <= t2

    visited = bytearray(W * H)   # 0=unvisited, 1=visited
    queue   = deque()

    # Seed from all 4 edges
    for x in range(W):
        for y in [0, H-1]:
            idx = y*W + x
            if not visited[idx] and matches_bg(idx):
                visited[idx] = 1
                queue.append(idx)
    for y in range(H):
        for x in [0, W-1]:
            idx = y*W + x
            if not visited[idx] and matches_bg(idx):
                visited[idx] = 1
                queue.append(idx)

    # BFS flood fill
    while queue:
        idx = queue.popleft()
        x   = idx % W
        y   = idx // W
        # Make transparent
        r,g,b,a = data[idx]
        data[idx] = (r, g, b, 0)
        # Check 4 neighbours
        for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < W and 0 <= ny < H:
                nidx = ny*W + nx
                if not visited[nidx] and matches_bg(nidx):
                    visited[nidx] = 1
                    queue.append(nidx)

    img.putdata(data)
    return img

# ─────────────────────────────────────────────────────────────────
def save_frame(img, anim, frame_num, x0, y0, x1, y1, out_dir, cell_w, cell_h):
    W, H = img.size
    x0=max(0,x0); x1=min(W,x1); y0=max(0,y0); y1=min(H,y1)
    if x1<=x0 or y1<=y0: return
    crop   = img.crop((x0, y0, x1, y1))
    canvas = Image.new('RGBA', (cell_w, cell_h), (0,0,0,0))
    paste_x = (cell_w - crop.width)  // 2
    paste_y =  cell_h - crop.height       # bottom-align
    canvas.paste(crop, (paste_x, paste_y), crop)
    canvas.save(os.path.join(out_dir, f'{anim}-{frame_num:02d}.png'), 'PNG')

def clear_dir(d):
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

# ─────────────────────────────────────────────────────────────────
def slice_frostia():
    sheet_path = os.path.join(ROOT, 'assets', 'revise_character', 'frostia_newcharact.png')
    print(f'Loading: {sheet_path}')
    raw = Image.open(sheet_path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}')
    print(f'Flood-fill removing background (edge-connected only)...')
    img = flood_remove_bg(raw, BG, BG_TOL)
    print(f'Background removed — interior pixels preserved.\n')

    out_base = os.path.join(ROOT, 'assets', 'sprites', 'frostia')
    total = 0

    for row_idx, (anim, (ry0, ry1)) in enumerate(zip(ANIM_ORDER, ROW_BANDS)):
        out_dir = os.path.join(out_base, anim)
        clear_dir(out_dir)
        for fi, (fx0, fx1) in enumerate(FRAME_X):
            save_frame(img, anim, fi+1, fx0, ry0, fx1, ry1, out_dir, MAX_FW, MAX_FH)
            total += 1
        print(f'  Row {row_idx+1}  {anim:<12}  13 frames  y={ry0}-{ry1}')

    print(f'\nTotal frames: {total}')
    return total

def quality_check():
    print('\n=== QUALITY CHECK ===')
    out_base = os.path.join(ROOT, 'assets', 'sprites', 'frostia')
    dims = set(); ok_all = True; grand_total = 0
    for anim in ANIM_ORDER:
        d = os.path.join(out_base, anim)
        files = sorted([f for f in os.listdir(d) if f.endswith('.png')])
        grand_total += len(files)
        if len(files) != 13:
            print(f'  FAIL  {anim:<12}  {len(files)}/13'); ok_all=False; continue
        first_file = files[0]
        for fname in files:
            im = Image.open(os.path.join(d,fname))
            dims.add(im.size)
        # spot-check transparency at corners of first frame
        im0 = Image.open(os.path.join(d, files[0])).convert('RGBA')
        p = im0.load(); W,H=im0.size
        corners_transparent = all(p[x,y][3]==0 for x,y in [(0,0),(W-1,0),(0,H-1),(W-1,H-1)])
        mark = 'OK  ' if corners_transparent else 'WARN'
        print(f'  {mark}  {anim:<12}  13 frames  corners_transparent={corners_transparent}')
    print(f'\n  Unique sizes: {dims}')
    print(f'  Total frames: {grand_total} (expected 117)')
    print('\n✔ PASSED' if ok_all and grand_total==117 else '\n✗ Issues found')

if __name__ == '__main__':
    slice_frostia()
    quality_check()

    # Re-run the animation remapping
    print('\nRe-mapping engine animations...')
    import shutil
    base = os.path.join(ROOT, 'assets', 'sprites', 'frostia')
    MAPPINGS = {'punch':'attack','kick':'attack','dash':'run',
                'block':'walk','victory':'idle'}
    for target, source in MAPPINGS.items():
        tgt = os.path.join(base, target); clear_dir(tgt)
        src = os.path.join(base, source)
        for fname in sorted(os.listdir(src)):
            if fname.endswith('.png'):
                shutil.copy(os.path.join(src, fname),
                            os.path.join(tgt, fname.replace(source, target)))
        print(f'  {target:<12} <- {source}')

    print('\nDone! Frostia ready. Refresh index.html in Chrome.')
