#!/usr/bin/env python3
"""
fix_crops.py — Re-slice only the broken frames for all 5 characters.
Scans each problem region precisely and regenerates correct PNGs.
"""
from PIL import Image
import os, math

DISPLAY = 96
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── helpers ──────────────────────────────────────────────────────
def load(path):
    return Image.open(os.path.join(ROOT, path)).convert('RGBA')

def remove_bg(img, bg_rgb, tol=38):
    r0,g0,b0 = bg_rgb; t2=tol*tol
    data = list(img.getdata())
    out  = [(0,0,0,0) if (r-r0)**2+(g-g0)**2+(b-b0)**2 < t2 else (r,g,b,a) for r,g,b,a in data]
    img  = img.copy(); img.putdata(out); return img

def save(img_sheet, anim, frame_num, x0,y0,x1,y1, char_id):
    W,H = img_sheet.size
    x0=max(0,min(x0,W)); x1=max(0,min(x1,W))
    y0=max(0,min(y0,H)); y1=max(0,min(y1,H))
    if x1<=x0 or y1<=y0: print(f'  SKIP {anim}-{frame_num}: bad coords'); return
    crop = img_sheet.crop((x0,y0,x1,y1))
    crop.thumbnail((DISPLAY,DISPLAY), Image.LANCZOS)
    canvas = Image.new('RGBA',(DISPLAY,DISPLAY),(0,0,0,0))
    canvas.paste(crop,((DISPLAY-crop.width)//2,(DISPLAY-crop.height)//2),crop)
    path = os.path.join(ROOT,'assets','sprites',char_id,anim,f'{anim}-{frame_num}.png')
    canvas.save(path,'PNG')
    print(f'  saved {char_id}/{anim}-{frame_num}.png')

def save_range(img_sheet, char_id, anim, y0, y1, x_ranges):
    """x_ranges = list of (x0,x1) per frame in order starting from frame_start"""
    pass

def equal_split(total_x0, total_x1, n):
    """Split [total_x0, total_x1] into n equal segments."""
    w = (total_x1 - total_x0) / n
    return [(int(total_x0+i*w), int(total_x0+(i+1)*w)) for i in range(n)]

# ════════════════════════════════════════════════════════════════
# BLAZOR
# ════════════════════════════════════════════════════════════════
def fix_blazor():
    img = load('tools/blazor-sheet.png')
    print('\n=== BLAZOR fixes ===')

    # DASH: frames 4,5,6 — scan found x=487-594, 609-713, 719-809
    save(img,'dash',4, 487,503,594,608,'blazor')
    save(img,'dash',5, 609,503,713,608,'blazor')
    save(img,'dash',6, 719,503,809,608,'blazor')

    # KICK: frames 5,6 — wide 639-750 (111px) split equal
    for i,(x0,x1) in enumerate(equal_split(639,750,2)):
        save(img,'kick',i+5, x0,863,x1,981,'blazor')

    # SPECIAL: frames 5,6,7,8
    # seg found: 437-469(32px noise/label), 482-558(76px)=frame5, 568-987(419px)=frames6,7,8
    save(img,'special',5, 482,999,558,1115,'blazor')
    for i,(x0,x1) in enumerate(equal_split(568,987,3)):
        save(img,'special',i+6, x0,999,x1,1115,'blazor')

    # ULTIMATE: frames 8,9,10
    # scan found: 585-650,671-740,752-819,826-895,899-1010 = frames 6,7,8,9,10 — map to 8,9,10
    save(img,'ultimate',8,  752,1122,819,1234,'blazor')
    save(img,'ultimate',9,  826,1122,895,1234,'blazor')
    save(img,'ultimate',10, 899,1122,1012,1234,'blazor')

    # DEFEAT: frames 2,3 — band found x=354-450 (only 1 seg = both frames together)
    for i,(x0,x1) in enumerate(equal_split(237,795,6)):
        save(img,'defeat',i+1, x0,1460,x1,1514,'blazor')

# ════════════════════════════════════════════════════════════════
# AQUARA
# ════════════════════════════════════════════════════════════════
def fix_aquara():
    img = load('tools/aquara_sheet.png')
    print('\n=== AQUARA fixes ===')

    # DASH: frames 4,5,6 — scan found x=405-563(158), 599-765(166), 808-998(190)
    save(img,'dash',4, 405,500,563,589,'aquara')
    save(img,'dash',5, 599,500,765,589,'aquara')
    save(img,'dash',6, 808,500,998,589,'aquara')

    # SPECIAL: frames 6,7 — segs 555-662(107), 665-772(105), 779-959(180px)=needs split
    save(img,'special',6, 555,954,662,1046,'aquara')
    save(img,'special',7, 665,954,772,1046,'aquara')
    # frame 8 = 779-959 split into 1 (keep as is — large water wave)
    save(img,'special',8, 779,954,959,1046,'aquara')

    # ULTIMATE: frames 4-10
    # segs: 397-495(98)=f4, 517-652(135)=2frames(f5,f6), 668-1005(337)=4frames(f7-f10)
    save(img,'ultimate',4, 397,1065,495,1169,'aquara')
    for i,(x0,x1) in enumerate(equal_split(517,652,2)):
        save(img,'ultimate',i+5, x0,1065,x1,1169,'aquara')
    for i,(x0,x1) in enumerate(equal_split(668,1005,4)):
        save(img,'ultimate',i+7, x0,1065,x1,1169,'aquara')

# ════════════════════════════════════════════════════════════════
# FLOREN
# ════════════════════════════════════════════════════════════════
def fix_floren():
    img = load('tools/floren_sheet.png')
    print('\n=== FLOREN fixes ===')

    # SPECIAL: frame 1 = 7-137(130px), frames 2-8 inside 140-974(834px) split 7
    save(img,'special',1, 7,951,137,1069,'floren')
    # frames 2-5 already scanned: 140-227, 231-324, 331-436, 437-544
    save(img,'special',2, 140,951,227,1069,'floren')
    save(img,'special',3, 231,951,324,1069,'floren')
    save(img,'special',4, 331,951,436,1069,'floren')
    save(img,'special',5, 437,951,544,1069,'floren')
    # frames 6,7,8 = 545-974 split 3
    for i,(x0,x1) in enumerate(equal_split(545,974,3)):
        save(img,'special',i+6, x0,951,x1,1069,'floren')

    # ULTIMATE: entire band 1000px = split 10 equal
    uw = (1007-7)//10
    for i in range(10):
        x0=7+i*uw; x1=7+(i+1)*uw if i<9 else 1007
        save(img,'ultimate',i+1, x0,1072,x1,1217,'floren')

# ════════════════════════════════════════════════════════════════
# FROSTIA — also fix transparency (bg removal + all broken frames)
# ════════════════════════════════════════════════════════════════
def fix_frostia():
    raw = load('tools/frostia_sheet.png')
    img = remove_bg(raw,(241,241,241),38)
    print('\n=== FROSTIA fixes ===')

    # Re-scan with bg removed
    pix = img.load(); w,h=img.size
    def segs(x0,x1,y0,y1,thr=0.03):
        cols=[(x,sum(pix[x,y][3] for y in range(y0,min(y1,h),2))) for x in range(x0,min(x1,w))]
        maxv=max(c[1] for c in cols) or 1; t=maxv*thr
        in_g=True; ss=[]; fs=x0
        for(x,v) in cols:
            if v<=t and not in_g: ss.append((fs,x)); in_g=True
            elif v>t and in_g: fs=x; in_g=False
        if not in_g: ss.append((fs,x1))
        return ss

    print('  Scanning FROSTIA regions...')
    d=segs(263,968,499,584); print(f'  DASH: {[(a,b,b-a) for a,b in d]}')
    p=segs(388,1024,730,830); print(f'  PUNCH: {[(a,b,b-a) for a,b in p]}')
    sp=segs(12,1024,980,1075,0.01); print(f'  SPECIAL: {[(a,b,b-a) for a,b in sp]}')
    ul=segs(12,1024,1091,1213,0.01); print(f'  ULTIMATE: {[(a,b,b-a) for a,b in ul]}')

    # DASH frames 4,5,6 — re-slice with bg removed sheet
    # band4 y=499-584 segs from earlier: s1=263-408, s2=418-573, s3=586-749, s4=789-879, s5=879-968
    dash_segs=segs(263,968,499,584)
    # skip first seg if it's the label (>150px wide usually)
    frame_segs=[s for s in dash_segs if (s[1]-s[0])<200]
    for i in range(min(6,len(frame_segs))):
        x0,x1=frame_segs[i]
        save(img,'dash',i+1,x0,499,x1,584,'frostia')

    # PUNCH frames 1-6
    punch_segs=segs(388,1024,730,830)
    for i,(_,_) in enumerate(punch_segs[:6]):
        x0,x1=punch_segs[i]
        save(img,'punch',i+1,x0,730,x1,830,'frostia')

    # SPECIAL frames 1-8 — equal split entire band content
    sp_all=segs(12,1024,980,1075,0.005)
    # merge into total range then split 8 equal
    if sp_all:
        total_x0=sp_all[0][0]; total_x1=sp_all[-1][1]
        for i,(x0,x1) in enumerate(equal_split(total_x0,total_x1,8)):
            save(img,'special',i+1,x0,980,x1,1075,'frostia')

    # ULTIMATE frames 1-10 — equal split
    ul_all=segs(12,1024,1091,1213,0.005)
    if ul_all:
        total_x0=ul_all[0][0]; total_x1=ul_all[-1][1]
        for i,(x0,x1) in enumerate(equal_split(total_x0,total_x1,10)):
            save(img,'ultimate',i+1,x0,1091,x1,1213,'frostia')

    # Re-save ALL frames with bg removed (fixes transparency issue)
    print('  Re-saving all frames with transparency...')
    all_anims = {
      'idle':  [(157,11,224,114),(244,11,310,114),(331,11,398,114),(425,11,491,114),(506,11,581,114),(603,11,673,114),(702,11,769,114),(792,11,862,114)],
      'walk':  [(238,130,312,237),(327,130,401,237),(424,130,498,237),(512,130,580,237),(601,130,679,237),(679,130,758,237),(770,130,852,237),(878,130,948,237)],
      'run':   [(236,251,309,356),(330,251,408,356),(424,251,506,356),(517,251,613,356),(632,251,722,356),(733,251,816,356),(840,251,919,356),(840,251,919,356)],
      'jump':  [(160,365,230,480),(278,365,359,480),(413,365,486,480),(524,365,610,480),(635,365,726,480),(762,365,844,480)],
      'block': [(156,611,244,708),(287,611,373,708),(422,611,509,708),(547,611,625,708)],
      'kick':  [(272,850,373,955),(389,850,497,955),(541,850,642,955),(676,850,777,955),(800,850,901,955),(800,850,901,955)],
      'hurt':  [(156,1235,225,1320),(242,1235,320,1320),(341,1235,421,1320),(444,1235,517,1320)],
      'victory':[(259,1332,334,1429),(355,1332,417,1429),(440,1332,507,1429),(523,1332,603,1429),(624,1332,692,1429),(727,1332,785,1429)],
      'defeat': [(355,1445,449,1514),(460,1445,555,1514),(566,1445,669,1514),(684,1445,795,1514),(566,1445,669,1514),(460,1445,555,1514)],
    }
    for anim, coords in all_anims.items():
        for i,(x0,y0,x1,y1) in enumerate(coords):
            save(img,anim,i+1,x0,y0,x1,y1,'frostia')
    print('  Frostia full re-slice with transparency done!')

# ════════════════════════════════════════════════════════════════
# NOCTIS — fix punch 3-6, special 1-8, ultimate 1-10
# ════════════════════════════════════════════════════════════════
def fix_noctis():
    raw = load('tools/noctis.png')
    img = remove_bg(raw,(8,12,20),25)
    print('\n=== NOCTIS fixes ===')

    pix=img.load(); w,h=img.size
    def segs(x0,x1,y0,y1,thr=0.03):
        cols=[(x,sum(pix[x,y][3] for y in range(y0,min(y1,h),2))) for x in range(x0,min(x1,w))]
        maxv=max(c[1] for c in cols) or 1; t=maxv*thr
        in_g=True; ss=[]; fs=x0
        for(x,v) in cols:
            if v<=t and not in_g: ss.append((fs,x)); in_g=True
            elif v>t and in_g: fs=x; in_g=False
        if not in_g: ss.append((fs,x1))
        return ss

    print('  Scanning NOCTIS regions...')
    p=segs(265,935,711,810); print(f'  PUNCH: {[(a,b,b-a) for a,b in p]}')
    sp=segs(262,1009,963,1067,0.01); print(f'  SPECIAL: {[(a,b,b-a) for a,b in sp]}')
    ul=segs(11,1015,1094,1206,0.01); print(f'  ULTIMATE: {[(a,b,b-a) for a,b in ul]}')

    # PUNCH frames 3-6
    punch_segs=segs(265,935,711,810)
    for i,s in enumerate(punch_segs[:6]):
        save(img,'punch',i+1,s[0],711,s[1],810,'noctis')

    # SPECIAL 1-8 — equal split total content range
    sp_all=segs(262,1009,963,1067,0.005)
    if sp_all:
        x0=sp_all[0][0]; x1=sp_all[-1][1]
        for i,(sx0,sx1) in enumerate(equal_split(x0,x1,8)):
            save(img,'special',i+1,sx0,963,sx1,1067,'noctis')

    # ULTIMATE 1-10 — equal split
    ul_all=segs(11,1015,1094,1206,0.005)
    if ul_all:
        x0=ul_all[0][0]; x1=ul_all[-1][1]
        for i,(sx0,sx1) in enumerate(equal_split(x0,x1,10)):
            save(img,'ultimate',i+1,sx0,1094,sx1,1206,'noctis')

# ════════════════════════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    fix_blazor()
    fix_aquara()
    fix_floren()
    fix_frostia()
    fix_noctis()

    # Final frame count check
    print('\n=== FRAME COUNT CHECK ===')
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    for char in ['blazor','aquara','floren','frostia','noctis']:
        fails=[]
        for a,e in zip(anims,exp):
            d=os.path.join(ROOT,'assets','sprites',char,a)
            c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
            if c!=e: fails.append(f'{a}:{c}/{e}')
        status='ALL OK' if not fails else f'ISSUES: {fails}'
        print(f'  {char.upper():<10} {status}')
    print('\nDone! Refresh index.html in Chrome.')
