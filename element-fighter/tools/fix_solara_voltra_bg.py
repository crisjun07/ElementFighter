#!/usr/bin/env python3
"""
fix_solara_voltra_bg.py
========================
Re-slices Solara and Voltra with very tight flood-fill tolerances:
  Solara: bg=black (0,0,0), tol=8   — only near-pure-black removed
  Voltra: bg=grey (240,241,242), tol=15 — only near-grey removed

The strict tolerance ensures:
  - Solara's gold armour, white dress, skin, hair = KEPT
  - Voltra's yellow lightning, black outlines, skin = KEPT
  - Only the solid background surrounding the sprites = REMOVED

Method: edge-connected flood-fill (BFS from sheet border only).
Interior pixels are NEVER touched regardless of colour.
"""
from PIL import Image
import os, shutil
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 128
PAD     = 12

# ── Strict flood-fill ─────────────────────────────────────────────
def flood_remove_bg(img, bg_rgb, tol):
    """
    STRICT flood-fill: only removes edge-connected pixels within `tol`
    of the background colour. Lower tol = safer for character art.
    """
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W,H  = img.size
    r0,g0,b0 = bg_rgb
    t2 = tol * tol

    def is_bg(i):
        r,g,b,a = data[i]
        if a < 10: return True   # already transparent
        return (r-r0)**2 + (g-g0)**2 + (b-b0)**2 <= t2

    visited = bytearray(W * H)
    q = deque()

    # Seed all 4 sheet edges
    for x in range(W):
        for y in [0, H-1]:
            i = y*W+x
            if not visited[i] and is_bg(i):
                visited[i]=1; q.append(i)
    for y in range(H):
        for x in [0, W-1]:
            i = y*W+x
            if not visited[i] and is_bg(i):
                visited[i]=1; q.append(i)

    # BFS — only removes connected-to-edge bg pixels
    while q:
        i  = q.popleft()
        r,g,b,a = data[i]
        data[i] = (r, g, b, 0)
        x,y = i%W, i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < W and 0 <= ny < H:
                ni = ny*W+nx
                if not visited[ni] and is_bg(ni):
                    visited[ni]=1; q.append(ni)

    img.putdata(data)
    return img

# ── Frame save ────────────────────────────────────────────────────
def save(img, anim, idx, x0,y0,x1,y1, root, pad=PAD, disp=DISPLAY):
    W,H = img.size
    x0=max(0,x0-pad); x1=min(W,x1+pad)
    y0=max(0,y0-pad); y1=min(H,y1+pad)
    if x1<=x0 or y1<=y0: return
    crop = img.crop((x0,y0,x1,y1))
    crop.thumbnail((disp,disp), Image.LANCZOS)
    c = Image.new('RGBA',(disp,disp),(0,0,0,0))
    ox = (disp - crop.width) // 2
    oy =  disp - crop.height   # bottom-align
    c.paste(crop,(ox,oy),crop)
    c.save(os.path.join(root, anim, f'{anim}-{idx}.png'), 'PNG')

def clear(root, anim):
    d = os.path.join(root, anim)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw), int(x0+(i+1)*fw)) for i in range(n)]


# ══════════════════════════════════════════════════════════════════
# SOLARA  —  bg=(0,0,0)  tol=8
# Only pure black pixels reachable from sheet edge are removed.
# Gold, white, skin, orange, grey = all preserved.
# ══════════════════════════════════════════════════════════════════
def fix_solara():
    print('=== SOLARA (tol=8, pure black bg only) ===')
    path = os.path.join(ROOT,'assets','revise_character','solara_newcharcter.png')
    raw  = Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}  bg=(0,0,0)  tol=8')
    img  = flood_remove_bg(raw, (0,0,0), tol=8)
    print('Background removed.\n')

    root = os.path.join(ROOT,'assets','sprites','solara')

    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)

    # Exact frame coordinates from original pixel scan (unchanged)
    BAND1_X=[(0,72),(105,177),(219,284),(320,388),(422,489),(524,590),(622,689),(720,786)]
    BAND2_X=[(0,75),(118,189),(225,296),(335,405),(441,510),(549,617),(651,721),(755,824)]
    BAND3_X=[(0,87),(141,223),(265,345),(393,473),(512,593),(640,723),(759,840),(878,952)]
    BAND4_X=[(0,64),(124,188),(230,293),(340,404),(447,508),(547,608)]
    BAND5_X=[(0,62),(120,181),(224,281),(320,377),(421,479),(519,583)]
    B6_BLK=[(0,72),(121,190),(237,311),(352,429)]
    B6_PCH=[(452,547),(567,665),(680,778),(791,883),(895,989),(1007,1079)]
    B7_KCK=[(19,78),(122,212),(240,335),(353,445),(462,565),(578,685)]
    B7_SPC=[(697,800),(808,909),(921,1017),(1027,1123),(1132,1243),(1248,1366),(1373,1521),(1373,1521)]
    B8T_ULT=[(12,79),(121,187),(236,304),(345,417),(460,527),(565,636),(688,762),(773,886),(773,886),(773,886)]
    B8B_HRT=[(0,64),(121,181),(235,295),(350,415)]
    B8B_VCT=[(449,512),(549,618),(655,714),(753,812),(856,946),(1004,1117)]
    B9_DFT=[(0,66),(148,229),(281,361),(412,493),(560,649),(705,796)]

    clear(root,'idle');    [s('idle',i+1,x0,12,x1,98)    for i,(x0,x1) in enumerate(BAND1_X)]
    clear(root,'walk');    [s('walk',i+1,x0,125,x1,208)  for i,(x0,x1) in enumerate(BAND2_X)]
    clear(root,'run');     [s('run',i+1,x0,234,x1,322)   for i,(x0,x1) in enumerate(BAND3_X)]
    clear(root,'jump');    [s('jump',i+1,x0,343,x1,434)  for i,(x0,x1) in enumerate(BAND4_X)]
    clear(root,'dash');    [s('dash',i+1,x0,456,x1,543)  for i,(x0,x1) in enumerate(BAND5_X)]
    clear(root,'block');   [s('block',i+1,x0,553,x1,629) for i,(x0,x1) in enumerate(B6_BLK)]
    clear(root,'punch');   [s('punch',i+1,x0,553,x1,629) for i,(x0,x1) in enumerate(B6_PCH)]
    clear(root,'kick');    [s('kick',i+1,x0,648,x1,729)  for i,(x0,x1) in enumerate(B7_KCK)]
    clear(root,'special'); [s('special',i+1,x0,648,x1,729) for i,(x0,x1) in enumerate(B7_SPC)]
    clear(root,'ultimate');[s('ultimate',i+1,x0,734,x1,824) for i,(x0,x1) in enumerate(B8T_ULT)]
    clear(root,'hurt');    [s('hurt',i+1,x0,824,x1,915)  for i,(x0,x1) in enumerate(B8B_HRT)]
    clear(root,'victory'); [s('victory',i+1,x0,824,x1,915) for i,(x0,x1) in enumerate(B8B_VCT)]
    clear(root,'defeat');  [s('defeat',i+1,x0,941,x1,979) for i,(x0,x1) in enumerate(B9_DFT)]

    # Verify
    _verify('solara', ['idle','walk','run','jump','dash','block','punch','kick',
                       'special','ultimate','hurt','victory','defeat'],
            [8,8,8,6,6,4,6,6,8,10,4,6,6], root)


# ══════════════════════════════════════════════════════════════════
# VOLTRA  —  bg=(241,242,243)  tol=15
# Only light-grey pixels reachable from sheet edge removed.
# Yellow lightning, black outlines, white highlights = all preserved.
# ══════════════════════════════════════════════════════════════════
def fix_voltra():
    print('\n=== VOLTRA (tol=15, light grey bg only) ===')
    path = os.path.join(ROOT,'tools','voltra_sheet.png')
    raw  = Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}  bg=(241,242,243)  tol=15')
    img  = flood_remove_bg(raw, (241,242,243), tol=15)
    print('Background removed.\n')

    root = os.path.join(ROOT,'assets','sprites','voltra')

    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)

    clear(root,'idle')
    for i,(x0,x1) in enumerate([(13,86),(126,208),(232,315),(346,425),(458,540),(576,652),(694,773),(809,887)]):
        s('idle',i+1,x0,7,x1,117)

    clear(root,'walk')
    for i,(x0,x1) in enumerate([(10,95),(120,197),(225,314),(347,423),(451,536),(561,649),(675,756),(783,881)]):
        s('walk',i+1,x0,134,x1,248)

    clear(root,'run')
    for i,(x0,x1) in enumerate([(12,99),(137,238),(277,385),(416,505),(532,631),(674,789),(811,913),(949,1050)]):
        s('run',i+1,x0,263,x1,365)

    clear(root,'jump')
    for i,(x0,x1) in enumerate([(14,91),(129,217),(258,349),(409,485),(540,627),(680,753)]):
        s('jump',i+1,x0,372,x1,490)

    clear(root,'dash')
    for i,(x0,x1) in enumerate([(17,105),(148,222),(258,354),(396,489),(517,621),(653,743)]):
        s('dash',i+1,x0,503,x1,613)

    clear(root,'block')
    for i,(x0,x1) in enumerate([(16,112),(129,224),(244,367),(376,441)]):
        s('block',i+1,x0,630,x1,730)

    clear(root,'punch')
    for i,(x0,x1) in enumerate([(441,506),(506,572),(572,638),(640,769),(783,897),(927,1044)]):
        s('punch',i+1,x0,630,x1,730)

    clear(root,'kick')
    for i,(x0,x1) in enumerate([(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]):
        s('kick',i+1,x0,736,x1,852)

    clear(root,'special')
    for i,(x0,x1) in enumerate([(783,915),(927,1062),(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]):
        s('special',i+1,x0,736,x1,852)

    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(17,1176,10)):
        s('ultimate',i+1,x0,848,x1,1028)

    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(929,1012),(1046,1090),(1090,1134),(1134,1176)]):
        s('hurt',i+1,x0,848,x1,1028)

    clear(root,'victory')
    for i,(x0,x1) in enumerate(eq(520,1176,6)):
        s('victory',i+1,x0,848,x1,1028)

    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(17,1176,6)):
        s('defeat',i+1,x0,848,x1,1028)

    _verify('voltra', ['idle','walk','run','jump','dash','block','punch','kick',
                       'special','ultimate','hurt','victory','defeat'],
            [8,8,8,6,6,4,6,6,8,10,4,6,6], root)


# ── Verify helper ─────────────────────────────────────────────────
def _verify(char, anims, exp_list, root):
    print(f'Quality check — {char.upper()}:')
    all_ok = True
    for anim, e in zip(anims, exp_list):
        d = os.path.join(root, anim)
        files = sorted([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else []
        c = len(files)
        ok = (c == e)
        if not ok: all_ok = False

        # Check first frame: corners transparent, interior has content
        if files:
            im  = Image.open(os.path.join(d,files[0])).convert('RGBA')
            p   = im.load(); W2,H2 = im.size
            corners_ok = p[0,0][3]==0 and p[W2-1,0][3]==0 and p[0,H2-1][3]==0 and p[W2-1,H2-1][3]==0
            # Interior content — check centre pixels
            content = sum(1 for y in range(H2//4,3*H2//4)
                          for x in range(W2//4,3*W2//4) if p[x,y][3]>40)
        else:
            corners_ok = False; content = 0

        print(f'  {"OK  " if ok else "FAIL"}  {anim:<12}  {c}/{e}  '
              f'transparent_corners={corners_ok}  interior_content={content}')

    print(f'  {"ALL OK" if all_ok else "ISSUES"}')


# ── Run ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    fix_solara()
    fix_voltra()
    print('\nDone! Rebuild index.html to apply.')
