#!/usr/bin/env python3
"""
fix_frame_edges.py
==================
Runs flood-fill background removal on EVERY existing frame PNG
for Terron, Voltra, and Solara.

The previous flood-fill ran on the full sheet, but after cropping+resizing,
neighbouring frame pixels can appear at the frame edge.
Running flood-fill per-frame fixes this completely.

For each frame:
  1. Detect the background colour from the frame's own corners.
  2. Flood-fill from all 4 edges of that frame.
  3. Save back in place.
"""
from PIL import Image
import os
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def flood_frame(img, tol=30):
    """
    Flood-fill background removal on a single frame image.
    Samples background colour from the frame's own corner pixels.
    """
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W, H = img.size

    # Sample corners to get background colour
    corner_indices = [0, W-1, (H-1)*W, (H-1)*W + W-1]
    # Pick the most common corner colour
    corner_rgbs = [(data[i][0], data[i][1], data[i][2]) for i in corner_indices
                   if data[i][3] > 50]  # only count opaque corners
    if not corner_rgbs:
        return img  # all corners transparent = already done

    r0 = int(sum(c[0] for c in corner_rgbs) / len(corner_rgbs))
    g0 = int(sum(c[1] for c in corner_rgbs) / len(corner_rgbs))
    b0 = int(sum(c[2] for c in corner_rgbs) / len(corner_rgbs))
    t2 = tol * tol

    def is_bg(idx):
        r,g,b,a = data[idx]
        if a < 20: return False
        return (r-r0)**2+(g-g0)**2+(b-b0)**2 <= t2

    visited = bytearray(W*H)
    q = deque()

    # Seed all 4 frame edges
    for x in range(W):
        for y in [0, H-1]:
            i=y*W+x
            if not visited[i] and is_bg(i):
                visited[i]=1; q.append(i)
    for y in range(H):
        for x in [0, W-1]:
            i=y*W+x
            if not visited[i] and is_bg(i):
                visited[i]=1; q.append(i)

    while q:
        i = q.popleft()
        r,g,b,a = data[i]
        data[i] = (r,g,b,0)
        x,y = i%W, i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<W and 0<=ny<H:
                ni=ny*W+nx
                if not visited[ni] and is_bg(ni):
                    visited[ni]=1; q.append(ni)

    img.putdata(data)
    return img


def fix_character(char_id, tol=30):
    base = os.path.join(ROOT, 'assets', 'sprites', char_id)
    anims = ['idle','walk','run','jump','dash','block','punch','kick',
             'special','ultimate','hurt','victory','defeat']
    total = 0; fixed = 0
    for anim in anims:
        d = os.path.join(base, anim)
        if not os.path.isdir(d): continue
        files = sorted([f for f in os.listdir(d) if f.endswith('.png')])
        for fname in files:
            fp = os.path.join(d, fname)
            img = Image.open(fp).convert('RGBA')
            p = img.load(); W,H = img.size
            # Check if any corner is opaque (needs fixing)
            corners = [p[0,0],p[W-1,0],p[0,H-1],p[W-1,H-1]]
            has_opaque_corner = any(c[3]>50 for c in corners)
            # Also check edge midpoints
            edge_mids = [p[W//2,0], p[W//2,H-1], p[0,H//2], p[W-1,H//2]]
            has_opaque_edge = any(c[3]>50 for c in edge_mids)
            total += 1
            if has_opaque_corner or has_opaque_edge:
                fixed_img = flood_frame(img, tol)
                fixed_img.save(fp, 'PNG')
                fixed += 1
    print(f'  {char_id.upper():<10}: processed {total} frames, fixed {fixed}')
    return fixed


def verify(char_id):
    """Check how many frames still have opaque edge pixels after fix."""
    base = os.path.join(ROOT, 'assets', 'sprites', char_id)
    anims = ['idle','walk','run','jump','dash','block','punch','kick',
             'special','ultimate','hurt','victory','defeat']
    remaining = 0
    for anim in anims:
        d = os.path.join(base, anim)
        if not os.path.isdir(d): continue
        for fname in sorted(os.listdir(d)):
            if not fname.endswith('.png'): continue
            img = Image.open(os.path.join(d,fname)).convert('RGBA')
            p = img.load(); W,H = img.size
            edges = ([(0,y) for y in range(H)] + [(W-1,y) for y in range(H)] +
                     [(x,0) for x in range(W)] + [(x,H-1) for x in range(W)])
            opaque = sum(1 for (x,y) in edges if p[x,y][3] > 50)
            remaining += opaque
    return remaining


if __name__ == '__main__':
    chars = [
        ('terron', 30),   # dark brown bg
        ('voltra', 28),   # light grey bg
        ('solara', 28),   # yellow-grey bg
    ]

    print('=== PER-FRAME FLOOD-FILL FIX ===\n')
    for char_id, tol in chars:
        print(f'Fixing {char_id.upper()}...')
        fixed = fix_character(char_id, tol)

    print('\n=== VERIFICATION (opaque edge pixels remaining) ===')
    all_clean = True
    for char_id, _ in chars:
        remaining = verify(char_id)
        ok = remaining == 0
        if not ok: all_clean = False
        print(f'  {char_id.upper():<10}: {remaining} opaque edge pixels  {"✔" if ok else "still has some"}')

    # Also apply to any other character that shows edge issues
    print('\n=== FULL CHECK — all 10 characters ===')
    all_chars = ['blazor','aquara','terron','voltra','zephyr','frostia',
                 'floren','solara','noctis','venom']
    for char_id in all_chars:
        rem = verify(char_id)
        print(f'  {char_id.upper():<10}: {rem} opaque edge pixels  {"✔ clean" if rem==0 else f"fixing..."}')
        if rem > 0:
            fix_character(char_id, 28)
            rem2 = verify(char_id)
            print(f'             after fix: {rem2}')

    print('\nDone! Rebuild index.html in Chrome.')
