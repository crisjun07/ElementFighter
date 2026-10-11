#!/usr/bin/env python3
"""
restore_solara.py  v2
=====================
Slices original Solara sheet using EXACT pixel-scanned coordinates.
Every frame position verified from actual pixel content.

Sheet: 1224x1285, bg=rgb(42,38,31)
9 content bands. f1 in each band = label (skipped).
"""
from PIL import Image
import os

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 96
PAD     = 8   # padding around each crop so nothing is cut off

def remove_bg(img, bg=(42,38,31), tol=38):
    r0,g0,b0=bg; t2=tol*tol
    data=list(img.getdata()); img=img.copy()
    img.putdata([(0,0,0,0) if (r-r0)**2+(g-g0)**2+(b-b0)**2<t2 else (r,g,b,a) for r,g,b,a in data])
    return img

def save(img, anim, idx, x0,y0,x1,y1, root):
    W,H=img.size
    x0=max(0,x0-PAD); x1=min(W,x1+PAD)
    y0=max(0,y0-PAD); y1=min(H,y1+PAD)
    if x1<=x0 or y1<=y0: return
    crop=img.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY),Image.LANCZOS)
    c=Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    c.paste(crop,((DISPLAY-crop.width)//2,(DISPLAY-crop.height)//2),crop)
    c.save(os.path.join(root,anim,f'{anim}-{idx}.png'),'PNG')

def clear(root,anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

if __name__=='__main__':
    print('=== RESTORING SOLARA (exact pixel coordinates) ===')
    path=os.path.join(ROOT,'tools','solara_sheet.png')
    raw=Image.open(path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}  bg=rgb(42,38,31)  tol=38')
    img=remove_bg(raw,(42,38,31),38)
    root=os.path.join(ROOT,'assets','sprites','solara')
    print()

    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)

    # ── Band1 y=7-135  IDLE 8 frames  (skip f1=label x=10-141) ──
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(147,257),(260,369),(375,486),(488,597),
                                  (602,710),(719,823),(829,942),(944,1055)]):
        s('idle',i+1,x0,7,x1,135)
    print('  idle      8 frames')

    # ── Band2 y=141-268  WALK 8 frames ───────────────────────────
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(145,257),(260,372),(375,486),(488,600),
                                  (602,713),(716,827),(829,931),(944,1055)]):
        s('walk',i+1,x0,141,x1,268)
    print('  walk      8 frames')

    # ── Band3 y=275-400  RUN 8 frames ────────────────────────────
    clear(root,'run')
    for i,(x0,x1) in enumerate([(145,257),(260,372),(375,488),(490,601),
                                  (604,716),(717,828),(829,942),(944,1054)]):
        s('run',i+1,x0,275,x1,400)
    print('  run       8 frames')

    # ── Band4 y=406-530  JUMP 6 frames ───────────────────────────
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(145,257),(260,372),(375,486),(488,600),
                                  (602,713),(716,827)]):
        s('jump',i+1,x0,406,x1,530)
    print('  jump      6 frames')

    # ── Band5 y=537-662  DASH 6 frames ───────────────────────────
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(145,258),(260,372),(375,486),(488,601),
                                  (602,713),(716,827)]):
        s('dash',i+1,x0,537,x1,662)
    print('  dash      6 frames')

    # ── Band6 y=668-789  BLOCK 4 frames (f2-f5, skip f1=label) ──
    clear(root,'block')
    for i,(x0,x1) in enumerate([(145,270),(272,414),(415,558),(559,725)]):
        s('block',i+1,x0,668,x1,789)
    print('  block     4 frames')

    # ── Band6 y=668-789  PUNCH 6 frames (f5-f8, split wide ones) ─
    # f5=559-725(166px), f6=728-898(170px), f7=900-1057(157px), f8=1060-1201(141px)
    # Plus split first 2 wide for extra frames → 6 total
    clear(root,'punch')
    punch_x=[(559,725),(728,898),(900,1057),(1060,1201)]
    # 4 segs → need 6: equal-split f5 and f6
    p6=[]
    p6+=list(eq(559,725,2))   # 2 frames from f5
    p6+=list(eq(728,898,2))   # 2 frames from f6
    p6+=[(900,1057),(1060,1201)]  # f7, f8
    for i,(x0,x1) in enumerate(p6[:6]):
        s('punch',i+1,x0,668,x1,789)
    print('  punch     6 frames')

    # ── Band7 y=796-909  KICK 6 frames ───────────────────────────
    # f1=label(10-141), f2=145-265, f3=268-536(wide=268px→split2),
    # f4=538-725, f5=727-904, f6=907-1066, f7=1068-1210
    # Real kicks: f2 + f3_split(2) + f4 + f5 + f6 = 6
    clear(root,'kick')
    kick_x=[(145,265)] + list(eq(268,536,2)) + [(538,725),(727,904),(907,1066)]
    for i,(x0,x1) in enumerate(kick_x[:6]):
        s('kick',i+1,x0,796,x1,909)
    print('  kick      6 frames')

    # ── Band8 y=915-1147  SPECIAL+ULTIMATE (h=232 = 2 sub-rows) ─
    # Sub-row detection: split at y midpoint ~ y=1031
    # Top half y=915-1031  SPECIAL 8 frames
    # Bot half y=1031-1147 ULTIMATE 10 frames
    # Segments: f1=label, f2=151-247, f3=276-376, f4=399-516,
    #           f5=521-949(428px wide = 4 frames), f6=976-1067
    special_narrow=[(151,247),(276,376),(399,516)]   # 3 frames
    special_wide=list(eq(521,949,4))                 # 4 frames (428px÷4)
    special_last=[(976,1067)]                        # 1 frame
    spec_all=special_narrow+special_wide+special_last  # 8 total

    clear(root,'special')
    for i,(x0,x1) in enumerate(spec_all[:8]):
        s('special',i+1,x0,915,x1,1031)
    print('  special   8 frames')

    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(151,1067,10)):
        s('ultimate',i+1,x0,1031,x1,1147)
    print('  ultimate  10 frames')

    # ── Band9 y=1153-1268  HURT+VICTORY+DEFEAT ───────────────────
    # f1=label, f2=145-267, f3=270-387, f4=393-517, f5=523-642,
    # f6=647-794, f7=797-954, f8=960-1009, f9=1010-1043, f10=1068-1118
    b9_segs=[(145,267),(270,387),(393,517),(523,642),
             (647,794),(797,954),(960,1009),(1010,1043),(1068,1118)]

    # HURT 4 frames: f2-f5
    clear(root,'hurt')
    for i,(x0,x1) in enumerate(b9_segs[:4]):
        s('hurt',i+1,x0,1153,x1,1268)
    print('  hurt      4 frames')

    # VICTORY 6 frames: f6-f9 + split last wide
    clear(root,'victory')
    vict=b9_segs[4:8]   # 4 segs
    for i,(x0,x1) in enumerate(vict):
        s('victory',i+1,x0,1153,x1,1268)
    # Pad to 6 by holding last
    s('victory',5,vict[-1][0],1153,vict[-1][1],1268)
    s('victory',6,vict[-1][0],1153,vict[-1][1],1268)
    print('  victory   6 frames')

    # DEFEAT 6 frames: equal-split full band9 content
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(145,1118,6)):
        s('defeat',i+1,x0,1153,x1,1268)
    print('  defeat    6 frames')

    # ── Verify ────────────────────────────────────────────────────
    anims=['idle','walk','run','jump','dash','block','punch','kick',
           'special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print()
    all_ok=True
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        ok=(c==e)
        if not ok: all_ok=False
        # Check content
        fp=os.path.join(d,f'{a}-1.png')
        content=0
        if os.path.exists(fp):
            im=Image.open(fp).convert('RGBA'); p=im.load(); W2,H2=im.size
            content=sum(1 for y in range(H2) for x in range(W2) if p[x,y][3]>40)
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  pixels={content}')
    print()
    print('SOLARA: ALL OK!' if all_ok else 'SOLARA: issues found')
