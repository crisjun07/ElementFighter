#!/usr/bin/env python3
"""Check all character frames for content touching frame edges (potential clipping)."""
from PIL import Image
import os

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
chars = ['blazor','aquara','terron','voltra','zephyr','frostia','floren','solara','noctis','venom']
anims = ['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']

print('=== FRAMES WITH CONTENT TOUCHING EDGES (alpha>80) ===\n')

for char in chars:
    issues = []
    for anim in anims:
        d = os.path.join(ROOT,'assets','sprites',char,anim)
        if not os.path.isdir(d): continue
        files = sorted([f for f in os.listdir(d) if f.endswith('.png')])
        for fname in files:
            fp  = os.path.join(d,fname)
            img = Image.open(fp).convert('RGBA')
            p   = img.load(); w,h = img.size
            top   = any(p[x,0][3]>80   for x in range(w))
            bot   = any(p[x,h-1][3]>80 for x in range(w))
            left  = any(p[0,y][3]>80   for y in range(h))
            right = any(p[w-1,y][3]>80 for y in range(h))
            if top or bot or left or right:
                n  = fname.replace('.png','').split('-')[-1]
                e  = ('T' if top else '') + ('B' if bot else '') + ('L' if left else '') + ('R' if right else '')
                issues.append(f'{anim[0]}{n}({e})')

    if issues:
        print(f'{char.upper():<10}: {len(issues):3d} clipped frames')
        # Group by animation
        by_anim = {}
        for issue in issues:
            key = issue[0]  # first letter = anim initial
            by_anim.setdefault(key,[]).append(issue)
        for k,v in by_anim.items():
            print(f'  {k}: {" ".join(v[:15])}')
    else:
        print(f'{char.upper():<10}: OK')
    print()
