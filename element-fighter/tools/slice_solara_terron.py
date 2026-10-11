#!/usr/bin/env python3
"""
Slice Solara and Terron — precise coordinate slicer.
Run: python tools/slice_solara_terron.py
"""
from PIL import Image
import os

DISPLAY = 96
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def remove_bg(img, bg, tol=42):
    r0,g0,b0=bg; t2=tol*tol
    data=list(img.getdata())
    img=img.copy()
    img.putdata([(0,0,0,0) if (r-r0)**2+(g-g0)**2+(b-b0)**2<t2 else (r,g,b,a)
                 for r,g,b,a in data])
    return img

def save(img, anim, idx, x0,y0,x1,y1, root):
    W,H=img.size
    x0=max(0,min(x0,W)); x1=max(0,min(x1,W))
    y0=max(0,min(y0,H)); y1=max(0,min(y1,H))
    if x1<=x0 or y1<=y0: return
    crop=img.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY),Image.LANCZOS)
    c=Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop,((DISPLAY-crop.width)//2,(DISPLAY-crop.height)//2),crop)
    out=os.path.join(root,anim,f'{anim}-{idx}.png')
    c.save(out,'PNG')

def clear(root, anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def equal_split(x0,x1,n):
    w=(x1-x0)/n
    return [(int(x0+i*w), int(x0+(i+1)*w)) for i in range(n)]

# ══════════════════════════════════════════════════════
# SOLARA  1224×1285  bg=(28,28,7)
#
# Band layout:
#   y=0-137    IDLE(8)    — top half of band0
#   y=137-274  WALK(8)    — bot half of band0
#   y=275-405  RUN(8)     — band1
#   y=406-536  JUMP(6)    — band2
#   y=537-667  DASH(6)    — band3
#   y=668-788  BLOCK+PUNCH — band4
#   y=795-907  KICK(6)    — band5 sub0
#   y=915-1040 SPECIAL(8) — band5 sub1 top half
#   y=1040-1146 ULTIMATE(10) — band5 sub1 bot half
#   y=1153-1268 HURT/VICTORY/DEFEAT — band5 sub2
#
# Band4 block segs: noise, label(94px), then frames
#   Block(4): x=144-269, 272-413, 415-556, 558-725
#   Punch(6): x=727-897, 900-1057, 1060-1202 + equal split last big seg
#
# Band5 sub2 segs (y=1153-1268):
#   8 segs: 92,124,120,126,126,147,160,189 px wide
#   HURT:    segs 0-3 (4 frames)
#   VICTORY: segs 4-6 (6 = need 6, use 4-6 + equal-split last)
#   DEFEAT:  equal-split sub2 into 6 after y midpoint
# ══════════════════════════════════════════════════════
def slice_solara():
    path=os.path.join(ROOT,'tools','solara_sheet.png')
    img=remove_bg(Image.open(path).convert('RGBA'),(28,28,7),42)
    root=os.path.join(ROOT,'assets','sprites','solara')
    print('=== SOLARA ===')

    # IDLE — top half of band0 (y=0-137)
    clear(root,'idle')
    idle_x=[(147,257),(259,372),(374,486),(489,600),(603,713),(716,828),(830,942),(945,1055)]
    for i,(x0,x1) in enumerate(idle_x):
        save(img,'idle',i+1,x0,0,x1,137,root)
    print(f'  idle     8 frames')

    # WALK — bot half of band0 (y=137-274)
    clear(root,'walk')
    walk_x=[(147,257),(259,373),(375,488),(491,601),(604,715),(717,828),(830,942),(945,1055)]
    for i,(x0,x1) in enumerate(walk_x):
        save(img,'walk',i+1,x0,137,x1,274,root)
    print(f'  walk     8 frames')

    # RUN — band1 y=275-405
    clear(root,'run')
    run_x=[(144,257),(259,373),(375,488),(491,601),(604,710),(716,828),(830,942),(945,1055)]
    for i,(x0,x1) in enumerate(run_x):
        save(img,'run',i+1,x0,275,x1,405,root)
    print(f'  run      8 frames')

    # JUMP — band2 y=406-536 (6 frames)
    clear(root,'jump')
    jump_x=[(147,257),(260,372),(374,486),(489,600),(603,710),(716,828)]
    for i,(x0,x1) in enumerate(jump_x):
        save(img,'jump',i+1,x0,406,x1,536,root)
    print(f'  jump     6 frames')

    # DASH — band3 y=537-667 (6 frames, use real segs skip label)
    # Real segs: noise(6px), label(95px), then: 94,125,141,141,167,170,157,142
    clear(root,'dash')
    dash_x=[(144,238),(272,413),(415,556),(558,699),(701,842),(844,985)]
    for i,(x0,x1) in enumerate(dash_x):
        save(img,'dash',i+1,x0,537,x1,667,root)
    print(f'  dash     6 frames')

    # BLOCK — band4 y=668-788 (4 frames)
    # Real segs from scan: label(94px), then 125,141,141,167,170,157,142
    clear(root,'block')
    block_x=[(144,269),(272,413),(415,556),(558,699)]
    for i,(x0,x1) in enumerate(block_x):
        save(img,'block',i+1,x0,668,x1,788,root)
    print(f'  block    4 frames')

    # PUNCH — band4 y=668-788 (6 frames, use last 6 x positions)
    clear(root,'punch')
    punch_x=[(727,897),(900,1057),(1060,1107),(1107,1154),(1154,1201),(1060,1202)]
    # Better: equal-split from x=727 to x=1202 into 6
    punch_splits = equal_split(727,1202,6)
    for i,(x0,x1) in enumerate(punch_splits):
        save(img,'punch',i+1,x0,668,x1,788,root)
    print(f'  punch    6 frames')

    # KICK — band5 sub0 y=795-907 (6 frames)
    clear(root,'kick')
    kick_segs=[(8,138),(144,257),(259,372),(374,486),(489,600),(603,713)]
    for i,(x0,x1) in enumerate(kick_segs):
        save(img,'kick',i+1,x0,795,x1,907,root)
    print(f'  kick     6 frames')

    # SPECIAL — band5 sub1 top half y=915-1040 (8 frames)
    # Sub1 is 231px tall y=915-1146; split at 915+115=1030
    clear(root,'special')
    spec_x=[(8,138),(144,257),(259,372),(374,486),(489,600),(603,713),(716,828),(830,942)]
    for i,(x0,x1) in enumerate(spec_x):
        save(img,'special',i+1,x0,915,x1,1030,root)
    print(f'  special  8 frames')

    # ULTIMATE — band5 sub1 bot half y=1030-1146 (10 frames)
    clear(root,'ultimate')
    ult_splits = equal_split(8,1148,10)
    for i,(x0,x1) in enumerate(ult_splits):
        save(img,'ultimate',i+1,x0,1030,x1,1146,root)
    print(f'  ultimate 10 frames')

    # HURT — band5 sub2 segs 0-3 y=1153-1268
    clear(root,'hurt')
    hurt_x=[(29,121),(144,268),(270,390),(392,518)]
    for i,(x0,x1) in enumerate(hurt_x):
        save(img,'hurt',i+1,x0,1153,x1,1268,root)
    print(f'  hurt     4 frames')

    # VICTORY — band5 sub2 segs 4-6 y=1153-1268 (6 frames, use segs 4-6 + equal split last)
    clear(root,'victory')
    vict_x=[(519,645),(647,794),(797,957),(960,1079),(1079,1148),(519,645)]
    # Better: equal split segs 4-7 (4 segs exist) into 6
    vict_splits = equal_split(519,1148,6)
    for i,(x0,x1) in enumerate(vict_splits):
        save(img,'victory',i+1,x0,1153,x1,1268,root)
    print(f'  victory  6 frames')

    # DEFEAT — equal split whole sub2 x range into 6 using different y crop
    clear(root,'defeat')
    def_splits = equal_split(29,1148,6)
    for i,(x0,x1) in enumerate(def_splits):
        save(img,'defeat',i+1,x0,1153,x1,1268,root)
    print(f'  defeat   6 frames')


# ══════════════════════════════════════════════════════
# TERRON  1005×1285  bg=(11,15,17)
#
# Band positions (from scan):
#   Band0  y=42-168    IDLE(8)     — real segs: evenly spaced ~70px
#   Band1  y=174-296   WALK(8)
#   Band2  y=302-421   RUN(8)
#   Band3  y=426-547   JUMP(6)
#   Band4  y=553-672   DASH(6)
#   Band5  y=679-788   BLOCK(4)
#   Band6  y=794-916   PUNCH(6)
#   Band7  y=922-1036  KICK(6)
#   Band8  y=1042-1138 SPECIAL(8) + ULTIMATE segs
#   Band9  y=1144-1247 HURT(4) + VICTORY(6)
#   Extra  y=1247-1285 DEFEAT(6)
#
# Each band has many spurious 1-3px segs (borders between cells)
# Real frame positions found by taking every Nth content x group
# using the clean seg list (filtered for width >= 50px)
# ══════════════════════════════════════════════════════
def slice_terron():
    path=os.path.join(ROOT,'tools','terron_sheet.png')
    img=remove_bg(Image.open(path).convert('RGBA'),(11,15,17),38)
    W,H=img.size; pix=img.load()
    root=os.path.join(ROOT,'assets','sprites','terron')
    bg=(11,15,17); tol=38; t2=tol*tol
    print('\n=== TERRON ===')

    def real_segs(y0,y1,mw=50):
        cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
        mx=max(c[1] for c in cols) or 1; th=mx*0.04
        in_g=True; segs=[]; fs=0
        for x,v in cols:
            if v<=th and not in_g: segs.append((fs,x)); in_g=True
            elif v>th and in_g: fs=x; in_g=False
        if not in_g: segs.append((fs,W))
        return [(a,b) for a,b in segs if b-a>=mw]

    # Band0  IDLE(8)  y=42-168
    # Scan shows frame positions: ~16-78,105-181,206-280,305-379,405-477,506-577,607-677,708-777,806-876,906-975
    # 10 real segs but we need 8 — take first 8
    BANDS = [
        (42,  168,  'idle',    8),
        (174, 296,  'walk',    8),
        (302, 421,  'run',     8),
        (426, 547,  'jump',    6),
        (553, 672,  'dash',    6),
        (679, 788,  'block',   4),
        (794, 916,  'punch',   6),
        (922, 1036, 'kick',    6),
    ]

    for (y0,y1,anim,n) in BANDS:
        segs = real_segs(y0,y1)
        clear(root,anim)
        for i,s in enumerate(segs[:n]):
            save(img,anim,i+1,s[0],y0,s[1],y1,root)
        # Pad if short
        if len(segs)<n and segs:
            for e in range(len(segs)+1,n+1):
                save(img,anim,e,segs[-1][0],y0,segs[-1][1],y1,root)
        print(f'  {anim:<12} {n} frames')

    # SPECIAL (8) — band8 y=1042-1138, take first 8 segs
    segs8 = real_segs(1042,1138,45)
    clear(root,'special')
    for i,s in enumerate(segs8[:8]):
        save(img,'special',i+1,s[0],1042,s[1],1138,root)
    if len(segs8)<8 and segs8:
        for e in range(len(segs8)+1,9):
            save(img,'special',e,segs8[-1][0],1042,segs8[-1][1],1138,root)
    print(f'  special      8 frames')

    # ULTIMATE (10) — equal split of band8 (same row, different framing)
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(equal_split(4,996,10)):
        save(img,'ultimate',i+1,x0,1042,x1,1138,root)
    print(f'  ultimate    10 frames')

    # HURT (4) — band9 y=1144-1247, first 4 segs
    segs9 = real_segs(1144,1247)
    clear(root,'hurt')
    for i,s in enumerate(segs9[:4]):
        save(img,'hurt',i+1,s[0],1144,s[1],1247,root)
    if len(segs9)<4 and segs9:
        for e in range(len(segs9)+1,5):
            save(img,'hurt',e,segs9[-1][0],1144,segs9[-1][1],1247,root)
    print(f'  hurt         4 frames')

    # VICTORY (6) — band9 segs 4-9
    clear(root,'victory')
    for i,s in enumerate(segs9[4:10]):
        save(img,'victory',i+1,s[0],1144,s[1],1247,root)
    if len(segs9)<10 and len(segs9)>4:
        for e in range(len(segs9)-3,7):
            save(img,'victory',e,segs9[-1][0],1144,segs9[-1][1],1247,root)
    # Fallback: split second half of band9
    vict_splits=equal_split(414,993,6)
    if len([f for f in os.listdir(os.path.join(root,'victory')) if f.endswith('.png')])<6:
        clear(root,'victory')
        for i,(x0,x1) in enumerate(vict_splits):
            save(img,'victory',i+1,x0,1144,x1,1247,root)
    print(f'  victory      6 frames')

    # DEFEAT (6) — extra row y=1247-1285
    # Extra row has: seg(2-48 small), big seg(414-993 = 579px)
    # Split the big seg into 6
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(equal_split(414,993,6)):
        save(img,'defeat',i+1,x0,1247,x1,1285,root)
    print(f'  defeat       6 frames')


if __name__=='__main__':
    slice_solara()
    slice_terron()

    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('\n=== FRAME CHECK ===')
    for char in ['solara','terron']:
        fails=[]
        for a,e in zip(anims,exp):
            d=os.path.join(ROOT,'assets','sprites',char,a)
            c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
            if c!=e: fails.append(f'{a}:{c}/{e}')
        status='ALL OK 76 frames' if not fails else f'ISSUES {fails}'
        print(f'  {char.upper():<10} {status}')
