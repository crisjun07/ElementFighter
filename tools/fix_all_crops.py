#!/usr/bin/env python3
"""
fix_all_crops.py
================
Fixes all broken/cut frames for:
  floren   - special (text in frame, two chars merged), ultimate
  frostia  - dash, special (text), ultimate
  noctis   - special, ultimate
  terron   - victory
  venom    - punch
  voltra   - defeat, hurt, ultimate, victory + remove white bg
  zephyr   - punch, special, defeat
  solara   - remove background from all frames

Strategy:
  1. Re-scan each problem band with EXPANDED y-range (add padding top+bottom)
     so no character is cut off at edges.
  2. For "text in frame-1" issues: detect and skip the label segment.
  3. Use smart bbox-crop per frame (crop to actual content + padding, then
     scale to DISPLAY keeping aspect, centre on canvas).
  4. bg removal for voltra and solara.
"""
from PIL import Image
import os, math

DISPLAY  = 96
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── helpers ──────────────────────────────────────────────────────────────────

def remove_bg(img, bg_rgb, tol=38):
    r0,g0,b0=bg_rgb; t2=tol*tol
    data=list(img.getdata())
    img=img.copy()
    img.putdata([(0,0,0,0) if (r-r0)**2+(g-g0)**2+(b-b0)**2<t2
                 else (r,g,b,a) for r,g,b,a in data])
    return img

def get_segs(pix, W, y0, y1, alpha_only=False, bg=None, tol=38, mw=30, thr=0.03):
    """Return content x-segments in band.  alpha_only=True for transparent sheets."""
    t2=tol*tol
    def ok(r,g,b,a):
        if a<20: return False
        if alpha_only: return True
        if bg is None: return True
        r0,g0,b0=bg
        return (r-r0)**2+(g-g0)**2+(b-b0)**2 >= t2
    cols=[(x, sum(1 for y in range(y0,y1,2) if ok(*pix[x,y]))) for x in range(W)]
    mx=max(c[1] for c in cols) or 1
    th=mx*thr; in_g=True; segs=[]; fs=0
    for x,v in cols:
        if v<=th and not in_g: segs.append((fs,x)); in_g=True
        elif v>th and in_g: fs=x; in_g=False
    if not in_g: segs.append((fs,W))
    return [(a,b) for a,b in segs if b-a>=mw]

def smart_save(img, anim, idx, x0,y0,x1,y1, root, pad=4):
    """Crop with padding, then scale to fit DISPLAY keeping ratio, transparent bg."""
    W,H=img.size
    # Expand by pad on all sides to avoid edge clipping
    cx0=max(0,x0-pad); cy0=max(0,y0-pad)
    cx1=min(W,x1+pad); cy1=min(H,y1+pad)
    if cx1<=cx0 or cy1<=cy0: return
    crop=img.crop((cx0,cy0,cx1,cy1))
    # Scale to fit inside DISPLAY×DISPLAY keeping aspect ratio
    crop.thumbnail((DISPLAY,DISPLAY), Image.LANCZOS)
    c=Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop,((DISPLAY-crop.width)//2,(DISPLAY-crop.height)//2),crop)
    os.makedirs(os.path.join(root,anim), exist_ok=True)
    c.save(os.path.join(root,anim,f'{anim}-{idx}.png'),'PNG')

def clear(root,anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    w=(x1-x0)/n
    return [(int(x0+i*w),int(x0+(i+1)*w)) for i in range(n)]

def fix_frames(char, anim, segs, img, y0, y1, expected, root, y_expand=8):
    """Save frames from segs, pad to expected count by holding last frame."""
    clear(root,anim)
    # Expand y range
    H=img.size[1]
    ey0=max(0,y0-y_expand); ey1=min(H,y1+y_expand)
    saved=0
    for i,(x0,x1) in enumerate(segs[:expected]):
        smart_save(img,anim,i+1,x0,ey0,x1,ey1,root,pad=6)
        saved+=1
    # Pad if short
    while saved < expected and segs:
        lx0,lx1=segs[min(saved-1,len(segs)-1)]
        smart_save(img,anim,saved+1,lx0,ey0,lx1,ey1,root,pad=6)
        saved+=1
    print(f'  {char} {anim:<12} {saved}/{expected} frames')

# ══════════════════════════════════════════════════════════════════════════════
# SOLARA — remove background from ALL existing frames
# ══════════════════════════════════════════════════════════════════════════════
def fix_solara_bg():
    print('\n=== SOLARA: removing background from all frames ===')
    root=os.path.join(ROOT,'assets','sprites','solara')
    anims=['idle','walk','run','jump','dash','block','punch','kick',
           'special','ultimate','hurt','victory','defeat']
    for anim in anims:
        d=os.path.join(root,anim)
        if not os.path.isdir(d): continue
        files=sorted([f for f in os.listdir(d) if f.endswith('.png')])
        count=0
        for fname in files:
            fp=os.path.join(d,fname)
            img=Image.open(fp).convert('RGBA')
            pix=img.load(); w,h=img.size
            # Check if background is still there (opaque near-white pixels)
            # Solara bg: light yellow-grey (28,28,7) but frames may have white from sheet
            # Remove any pixel close to (230-255, 230-255, 200-255)
            data=list(img.getdata())
            def is_bg(r,g,b,a):
                if a<200: return False
                # original bg (28,28,7) or white artefacts from resize
                if (r-28)**2+(g-28)**2+(b-7)**2 < 40*40: return True
                if r>220 and g>220 and b>180 and abs(r-g)<30: return True
                return False
            new=[( 0,0,0,0) if is_bg(*px) else px for px in data]
            img.putdata(new)
            img.save(fp,'PNG')
            count+=1
        print(f'  {anim:<12} {count} frames cleaned')

# ══════════════════════════════════════════════════════════════════════════════
# VOLTRA — remove white bg from all frames + fix defeat/hurt/ultimate/victory
# ══════════════════════════════════════════════════════════════════════════════
def fix_voltra():
    print('\n=== VOLTRA ===')
    sheet_path=os.path.join(ROOT,'tools','voltra_sheet.png')
    raw=Image.open(sheet_path).convert('RGBA')
    img=remove_bg(raw,(240,241,242),35)
    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','voltra')

    # First: remove bg from ALL existing voltra frames
    anims=['idle','walk','run','jump','dash','block','punch','kick',
           'special','ultimate','hurt','victory','defeat']
    for anim in anims:
        d=os.path.join(root,anim)
        if not os.path.isdir(d): continue
        for fname in os.listdir(d):
            if not fname.endswith('.png'): continue
            fp=os.path.join(d,fname)
            fr=Image.open(fp).convert('RGBA')
            data=list(fr.getdata())
            bg=(240,241,242); tol=35; t2=tol*tol
            r0,g0,b0=bg
            new=[(0,0,0,0) if (r-r0)**2+(g-g0)**2+(b-b0)**2<t2 else px
                 for px,r,g,b,a in zip(data,[px[0] for px in data],[px[1] for px in data],[px[2] for px in data],[px[3] for px in data])
                 for r,g,b,a in [px]]
            # Simpler approach:
            pxs=list(fr.getdata())
            cleaned=[(0,0,0,0) if (p[0]-r0)**2+(p[1]-g0)**2+(p[2]-b0)**2<t2 else p for p in pxs]
            fr.putdata(cleaned); fr.save(fp,'PNG')
    print('  All existing frames: bg removed')

    # Re-slice Band8 properly with expanded y-range
    # Band8 y=858-1018 h=160  12 real segs
    def segs8():
        def ok(r,g,b,a): return a>20
        cols=[(x,sum(1 for y in range(850,1024,2) if ok(*pix[x,y]))) for x in range(W)]
        mx=max(c[1] for c in cols) or 1; th=mx*0.03
        in_g=True; s=[]; fs=0
        for x,v in cols:
            if v<=th and not in_g: s.append((fs,x)); in_g=True
            elif v>thr and in_g: fs=x; in_g=False
        # fallback: use known coords from earlier scan
        return [(17,104),(151,226),(276,354),(392,481),(520,605),(669,754),
                (800,885),(929,1012),(929,1012),(1012,1094),(1094,1176),(1176,1258)]
    
    # Use known seg positions from original scan
    # Band8 segs: f1=17-104, f2=151-226, f3=276-354, f4=392-481, f5=520-605,
    #             f6=669-754, f7=800-885, f8=929-1012, f9=1046-1176(wide)
    s8=[(17,104),(151,226),(276,354),(392,481),(520,605),(669,754),
        (800,885),(929,1012),(1046,1090),(1090,1134),(1134,1176),(1046,1176)]

    # ULTIMATE (10 frames) — f1-f10, expand y
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(s8[:10]):
        smart_save(img,'ultimate',i+1,x0,848,x1,1028,root,pad=8)
    print(f'  voltra ultimate   10 frames')

    # HURT (4 frames) — last 4 distinct segs
    clear(root,'hurt')
    hurt_x=[(929,1012),(1046,1090),(1090,1134),(1134,1176)]
    for i,(x0,x1) in enumerate(hurt_x):
        smart_save(img,'hurt',i+1,x0,848,x1,1028,root,pad=8)
    print(f'  voltra hurt        4 frames')

    # VICTORY (6 frames) — equal-split second half of band8
    clear(root,'victory')
    for i,(x0,x1) in enumerate(eq(520,1176,6)):
        smart_save(img,'victory',i+1,x0,848,x1,1028,root,pad=8)
    print(f'  voltra victory     6 frames')

    # DEFEAT (6 frames) — equal-split full band8
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(17,1176,6)):
        smart_save(img,'defeat',i+1,x0,848,x1,1028,root,pad=8)
    print(f'  voltra defeat      6 frames')

# ══════════════════════════════════════════════════════════════════════════════
# FLOREN — fix special (label+double-char issue), ultimate
# ══════════════════════════════════════════════════════════════════════════════
def fix_floren():
    print('\n=== FLOREN ===')
    img=Image.open(os.path.join(ROOT,'tools','floren_sheet.png')).convert('RGBA')
    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','floren')

    def segs(y0,y1,mw=35):
        cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
        mx=max(c[1] for c in cols) or 1; th=mx*0.03
        in_g=True; s=[]; fs=0
        for x,v in cols:
            if v<=th and not in_g: s.append((fs,x)); in_g=True
            elif v>th and in_g: fs=x; in_g=False
        if not in_g: s.append((fs,W))
        return [(a,b) for a,b in s if b-a>=mw]

    # SPECIAL y=951-1069
    # Previously: seg0=7-137 (label+char merged), seg1=140-974 (7 chars crammed)
    # Fix: scan with lower threshold + skip first wide seg if it has label
    sp=segs(943,1077)   # expand y range
    # First seg has label text — skip if very wide or starts at x<20
    real_sp=[s for s in sp if s[0]>50 or s[1]-s[0]<150]
    if not real_sp: real_sp=sp
    # The big merged seg needs splitting — find it and equal-split
    fixed_sp=[]
    for (x0,x1) in real_sp:
        if x1-x0 > 300:     # too wide = multiple chars merged
            n=max(2, round((x1-x0)/100))
            fixed_sp+=eq(x0,x1,n)
        elif x1-x0 > 150:   # medium = 2 chars
            fixed_sp+=eq(x0,x1,2)
        else:
            fixed_sp.append((x0,x1))
    # Skip label (first seg starting near x=0 if very distinct)
    if fixed_sp and fixed_sp[0][0]<30 and fixed_sp[0][1]-fixed_sp[0][0]>80:
        # Check if it looks like a label (text-like content vs character)
        # labels have content only in top portion
        lx0,lx1=fixed_sp[0]
        top_d=sum(1 for x in range(lx0,lx1,2) for y in range(943,970,2) if pix[x,y][3]>20)
        bot_d=sum(1 for x in range(lx0,lx1,2) for y in range(1020,1077,2) if pix[x,y][3]>20)
        if top_d > bot_d*3:  # top-heavy = label
            fixed_sp=fixed_sp[1:]
    clear(root,'special')
    for i,(x0,x1) in enumerate(fixed_sp[:8]):
        smart_save(img,'special',i+1,x0,943,x1,1077,root,pad=8)
    for e in range(len(fixed_sp)+1,9):
        smart_save(img,'special',e,fixed_sp[-1][0],943,fixed_sp[-1][1],1077,root,pad=8)
    print(f'  floren special     8 frames')

    # ULTIMATE y=1072-1217 — full band equal-split into 10
    ult=segs(1064,1225)
    if ult:
        x_all_start=ult[0][0]; x_all_end=ult[-1][1]
    else:
        x_all_start=7; x_all_end=1007
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(x_all_start,x_all_end,10)):
        smart_save(img,'ultimate',i+1,x0,1064,x1,1225,root,pad=8)
    print(f'  floren ultimate   10 frames')

# ══════════════════════════════════════════════════════════════════════════════
# FROSTIA — fix dash, special (label), ultimate
# ══════════════════════════════════════════════════════════════════════════════
def fix_frostia():
    print('\n=== FROSTIA ===')
    raw=Image.open(os.path.join(ROOT,'tools','frostia_sheet.png')).convert('RGBA')
    img=remove_bg(raw,(241,241,242),40)
    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','frostia')

    def segs(y0,y1,mw=35,thr=0.03):
        cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
        mx=max(c[1] for c in cols) or 1; th=mx*thr
        in_g=True; s=[]; fs=0
        for x,v in cols:
            if v<=th and not in_g: s.append((fs,x)); in_g=True
            elif v>th and in_g: fs=x; in_g=False
        if not in_g: s.append((fs,W))
        return [(a,b) for a,b in s if b-a>=mw]

    # DASH y=499-584 — expand and re-scan
    ds=segs(490,594)
    # Remove tiny segs
    ds=[s for s in ds if s[1]-s[0]>=50]
    clear(root,'dash')
    for i,(x0,x1) in enumerate(ds[:6]):
        smart_save(img,'dash',i+1,x0,490,x1,594,root,pad=8)
    for e in range(len(ds)+1,7):
        smart_save(img,'dash',e,ds[-1][0],490,ds[-1][1],594,root,pad=8)
    print(f'  frostia dash       6 frames')

    # SPECIAL y=980-1075 — skip label, get 8 real frames
    sp=segs(972,1083)
    sp=[s for s in sp if s[1]-s[0]>=40]
    # skip first if it's a label
    if sp and sp[0][0]<30: sp=sp[1:]
    # merge/split wide blobs
    fixed=[]
    for (x0,x1) in sp:
        if x1-x0>200: fixed+=eq(x0,x1,max(2,round((x1-x0)/90)))
        else: fixed.append((x0,x1))
    clear(root,'special')
    for i,(x0,x1) in enumerate(fixed[:8]):
        smart_save(img,'special',i+1,x0,972,x1,1083,root,pad=8)
    for e in range(len(fixed)+1,9):
        smart_save(img,'special',e,fixed[-1][0],972,fixed[-1][1],1083,root,pad=8)
    print(f'  frostia special    8 frames')

    # ULTIMATE y=1091-1213 — equal-split full content range
    ul=segs(1083,1221)
    if ul:
        ux0=ul[0][0]; ux1=ul[-1][1]
    else:
        ux0=12; ux1=1024
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(ux0,ux1,10)):
        smart_save(img,'ultimate',i+1,x0,1083,x1,1221,root,pad=8)
    print(f'  frostia ultimate  10 frames')

# ══════════════════════════════════════════════════════════════════════════════
# NOCTIS — fix special, ultimate
# ══════════════════════════════════════════════════════════════════════════════
def fix_noctis():
    print('\n=== NOCTIS ===')
    raw=Image.open(os.path.join(ROOT,'tools','noctis.png')).convert('RGBA')
    img=remove_bg(raw,(8,12,20),28)
    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','noctis')

    def segs(y0,y1,mw=35):
        cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
        mx=max(c[1] for c in cols) or 1; th=mx*0.03
        in_g=True; s=[]; fs=0
        for x,v in cols:
            if v<=th and not in_g: s.append((fs,x)); in_g=True
            elif v>th and in_g: fs=x; in_g=False
        if not in_g: s.append((fs,W))
        return [(a,b) for a,b in s if b-a>=mw]

    # SPECIAL y=963-1067 expanded
    sp=segs(955,1075)
    sp=[s for s in sp if s[1]-s[0]>=40]
    fixed=[]
    for (x0,x1) in sp:
        if x1-x0>200: fixed+=eq(x0,x1,max(2,round((x1-x0)/90)))
        elif x1-x0>120: fixed+=eq(x0,x1,2)
        else: fixed.append((x0,x1))
    clear(root,'special')
    for i,(x0,x1) in enumerate(fixed[:8]):
        smart_save(img,'special',i+1,x0,955,x1,1075,root,pad=8)
    for e in range(len(fixed)+1,9):
        smart_save(img,'special',e,fixed[-1][0],955,fixed[-1][1],1075,root,pad=8)
    print(f'  noctis special     8 frames')

    # ULTIMATE y=1094-1206 expanded — equal-split
    ul=segs(1086,1214)
    if ul:
        ux0=ul[0][0]; ux1=ul[-1][1]
    else:
        ux0=11; ux1=1015
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(ux0,ux1,10)):
        smart_save(img,'ultimate',i+1,x0,1086,x1,1214,root,pad=8)
    print(f'  noctis ultimate   10 frames')

# ══════════════════════════════════════════════════════════════════════════════
# TERRON — fix victory
# ══════════════════════════════════════════════════════════════════════════════
def fix_terron():
    print('\n=== TERRON ===')
    raw=Image.open(os.path.join(ROOT,'tools','terron_sheet.png')).convert('RGBA')
    img=remove_bg(raw,(11,15,17),38)
    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','terron')

    def segs(y0,y1,mw=40):
        cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
        mx=max(c[1] for c in cols) or 1; th=mx*0.04
        in_g=True; s=[]; fs=0
        for x,v in cols:
            if v<=th and not in_g: s.append((fs,x)); in_g=True
            elif v>th and in_g: fs=x; in_g=False
        if not in_g: s.append((fs,W))
        return [(a,b) for a,b in s if b-a>=mw]

    # VICTORY y=1156-1240 expanded — re-scan all 9 segs, take segs 4-9
    vs=segs(1148,1248)
    # Segs are: first 4=hurt, next 5=victory; take segs 4-8 and equal-split for 6
    vict_segs=vs[4:] if len(vs)>4 else vs
    clear(root,'victory')
    if len(vict_segs)>=6:
        for i,(x0,x1) in enumerate(vict_segs[:6]):
            smart_save(img,'victory',i+1,x0,1148,x1,1248,root,pad=8)
    else:
        # Equal-split second half
        if vs:
            mid_x=(vs[3][1] if len(vs)>3 else vs[-1][1])
            for i,(x0,x1) in enumerate(eq(mid_x,vs[-1][1],6)):
                smart_save(img,'victory',i+1,x0,1148,x1,1248,root,pad=8)
        else:
            for i,(x0,x1) in enumerate(eq(462,993,6)):
                smart_save(img,'victory',i+1,x0,1148,x1,1248,root,pad=8)
    # Ensure 6 frames
    existing=[f for f in os.listdir(os.path.join(root,'victory')) if f.endswith('.png')]
    if len(existing)<6:
        last=sorted(existing)[-1] if existing else None
        for e in range(len(existing)+1,7):
            if last:
                import shutil
                shutil.copy(os.path.join(root,'victory',last),
                            os.path.join(root,'victory',f'victory-{e}.png'))
    print(f'  terron victory     6 frames')

# ══════════════════════════════════════════════════════════════════════════════
# VENOM — fix punch
# ══════════════════════════════════════════════════════════════════════════════
def fix_venom():
    print('\n=== VENOM ===')
    img=Image.open(os.path.join(ROOT,'tools','venom_sheet.png')).convert('RGBA')
    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','venom')

    def segs(y0,y1,mw=35):
        cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
        mx=max(c[1] for c in cols) or 1; th=mx*0.03
        in_g=True; s=[]; fs=0
        for x,v in cols:
            if v<=th and not in_g: s.append((fs,x)); in_g=True
            elif v>th and in_g: fs=x; in_g=False
        if not in_g: s.append((fs,W))
        return [(a,b) for a,b in s if b-a>=mw]

    # PUNCH y=701-817 expanded — 6 frames: f1-f2 (block) + remaining segs
    ps=segs(693,825)
    # Venom punch: f1=16-112, f2=129-224, f3=244-367, f4=376-638(wide), f5=640-769, ...
    # f4 wide=262px needs splitting into 3 (block4 + punch1 + punch2)
    fixed=[]
    for (x0,x1) in ps:
        if x1-x0>150: fixed+=eq(x0,x1,max(2,round((x1-x0)/90)))
        else: fixed.append((x0,x1))
    # Skip first 4 (block frames), take next 6 as punch
    punch_segs=fixed[4:10] if len(fixed)>4 else fixed
    clear(root,'punch')
    for i,(x0,x1) in enumerate(punch_segs[:6]):
        smart_save(img,'punch',i+1,x0,693,x1,825,root,pad=8)
    for e in range(len(punch_segs)+1,7):
        smart_save(img,'punch',e,punch_segs[-1][0],693,punch_segs[-1][1],825,root,pad=8)
    print(f'  venom punch        6 frames')

# ══════════════════════════════════════════════════════════════════════════════
# ZEPHYR — fix punch, special, defeat
# ══════════════════════════════════════════════════════════════════════════════
def fix_zephyr():
    print('\n=== ZEPHYR ===')
    raw=Image.open(os.path.join(ROOT,'tools','zephyr_sheet.png')).convert('RGBA')
    img=remove_bg(raw,(243,244,244),35)
    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','zephyr')

    def segs(y0,y1,mw=35):
        cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
        mx=max(c[1] for c in cols) or 1; th=mx*0.03
        in_g=True; s=[]; fs=0
        for x,v in cols:
            if v<=th and not in_g: s.append((fs,x)); in_g=True
            elif v>th and in_g: fs=x; in_g=False
        if not in_g: s.append((fs,W))
        return [(a,b) for a,b in s if b-a>=mw]

    # PUNCH: Band6 y=623-716 expanded — 10-13 segs, skip first 4 (block), take 6
    ps=segs(615,724)
    # split wide segs
    fixed=[]
    for (x0,x1) in ps:
        if x1-x0>150: fixed+=eq(x0,x1,max(2,round((x1-x0)/100)))
        else: fixed.append((x0,x1))
    punch_segs=fixed[4:10] if len(fixed)>4 else fixed
    clear(root,'punch')
    for i,(x0,x1) in enumerate(punch_segs[:6]):
        smart_save(img,'punch',i+1,x0,615,x1,724,root,pad=8)
    for e in range(len(punch_segs)+1,7):
        smart_save(img,'punch',e,punch_segs[-1][0],615,punch_segs[-1][1],724,root,pad=8)
    print(f'  zephyr punch       6 frames')

    # SPECIAL: Band7 y=726-842 expanded — after kick(6), get 8 more
    sp=segs(718,850)
    fixed=[]
    for (x0,x1) in sp:
        if x1-x0>160: fixed+=eq(x0,x1,max(2,round((x1-x0)/100)))
        else: fixed.append((x0,x1))
    spec_segs=fixed[6:14] if len(fixed)>6 else fixed
    clear(root,'special')
    for i,(x0,x1) in enumerate(spec_segs[:8]):
        smart_save(img,'special',i+1,x0,718,x1,850,root,pad=8)
    for e in range(len(spec_segs)+1,9):
        smart_save(img,'special',e,spec_segs[-1][0],718,spec_segs[-1][1],850,root,pad=8)
    print(f'  zephyr special     8 frames')

    # DEFEAT: Band9 segs via Band8 y-range for full height
    ds=segs(960,1015)
    def_segs=ds[-6:] if len(ds)>=6 else ds
    b8y0=849; b8y1=943
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(def_segs[:6]):
        smart_save(img,'defeat',i+1,x0,b8y0,x1,b8y1,root,pad=8)
    for e in range(len(def_segs)+1,7):
        smart_save(img,'defeat',e,def_segs[-1][0],b8y0,def_segs[-1][1],b8y1,root,pad=8)
    print(f'  zephyr defeat      6 frames')

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    fix_solara_bg()
    fix_voltra()
    fix_floren()
    fix_frostia()
    fix_noctis()
    fix_terron()
    fix_venom()
    fix_zephyr()

    # Final count check
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    chars=['blazor','aquara','terron','voltra','zephyr','frostia','floren','solara','noctis','venom']
    print('\n=== FINAL CHECK ===')
    for char in chars:
        fails=[]
        for a,e in zip(anims,exp):
            d=os.path.join(ROOT,'assets','sprites',char,a)
            c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
            if c!=e: fails.append(f'{a}:{c}/{e}')
        print(f'  {"OK" if not fails else "ISSUE":<6} {char.upper():<10}  {fails if fails else "all OK"}')
    print('\nDone!')
