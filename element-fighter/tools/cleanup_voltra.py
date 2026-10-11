#!/usr/bin/env python3
"""
cleanup_voltra.py
=================
Post-process Voltra frames: remove semi-transparent grey rescaling artefacts
from frame edges, while keeping all character art (yellow/orange lightning).
"""
from PIL import Image
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def is_grey_artefact(r, g, b, a):
    """True if this pixel is a semi-transparent grey rescaling artefact."""
    if a <= 10 or a >= 250:   # skip fully transparent or fully opaque
        return False
    # Is it grey-ish? (low colour saturation, not yellow/warm)
    sat = max(r,g,b) - min(r,g,b)
    # Character colours are warm (yellow/orange): r>g or r>>b
    # Background grey: r≈g≈b
    if sat < 35 and r > 140:   # grey-ish semi-transparent
        return True
    return False

def cleanup_frame_edges(img):
    """Remove grey rescaling artefacts from the outer 2px of a frame."""
    img = img.convert('RGBA')
    p   = img.load()
    w,h = img.size
    changed = 0
    # Process outer 2 pixel border only
    for border in range(2):
        for x in range(w):
            for y in [border, h-1-border]:
                r,g,b,a = p[x,y]
                if is_grey_artefact(r,g,b,a):
                    p[x,y] = (0,0,0,0); changed += 1
        for y in range(h):
            for x in [border, w-1-border]:
                r,g,b,a = p[x,y]
                if is_grey_artefact(r,g,b,a):
                    p[x,y] = (0,0,0,0); changed += 1
    return img, changed

def run():
    root  = os.path.join(ROOT, 'assets', 'sprites', 'voltra')
    anims = ['idle','walk','run','jump','dash','block','punch','kick',
             'special','ultimate','hurt','victory','defeat']
    total = 0
    print('Cleaning Voltra frame edge artefacts...')
    for anim in anims:
        d = os.path.join(root, anim)
        if not os.path.isdir(d): continue
        for fname in sorted(os.listdir(d)):
            if not fname.endswith('.png'): continue
            fp  = os.path.join(d, fname)
            img = Image.open(fp).convert('RGBA')
            img2, n = cleanup_frame_edges(img)
            if n > 0:
                img2.save(fp, 'PNG')
                total += n

    print(f'Removed {total} grey artefact pixels from frame edges.\n')

    # Final verification
    print('=== VOLTRA EDGE CHECK ===')
    for anim in anims:
        fp = os.path.join(root, anim, f'{anim}-1.png')
        if not os.path.exists(fp): continue
        img = Image.open(fp).convert('RGBA'); p = img.load(); W,H = img.size
        edges = ([(0,y) for y in range(H)] + [(W-1,y) for y in range(H)] +
                 [(x,0) for x in range(W)] + [(x,H-1) for x in range(W)])
        # Count grey bg pixels (light grey, fully opaque or nearly so)
        grey = sum(1 for x,y in edges
                   if p[x,y][3]>50
                   and p[x,y][0]>170 and p[x,y][1]>170
                   and (max(p[x,y][:3])-min(p[x,y][:3]))<40)
        # Count character colour pixels at edge (warm/yellow = fine)
        warm = sum(1 for x,y in edges
                   if p[x,y][3]>50
                   and p[x,y][0]>150
                   and (p[x,y][0]-p[x,y][2])>30)  # more red than blue = warm
        status = 'OK  ' if grey == 0 else 'GREY'
        print(f'  {status}  {anim:<12}  grey_edge={grey}  warm_char_edge={warm}')

    print('\nDone! Rebuild index.html to apply.')

if __name__ == '__main__':
    run()
