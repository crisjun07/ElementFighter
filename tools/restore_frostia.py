#!/usr/bin/env python3
"""
restore_frostia.py
==================
Restores the original Frostia sprites from frostia_sheet.png
using the exact same logic as the original slice_two.py slicer.

Original: bg=rgb(241,241,241), tol=38, DISPLAY=96, output=<anim>-N.png
"""
from PIL import Image
import os

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 96

def remove_bg_sheet(img, bg_rgb, tol=38):
    """Remove background from entire sheet at once."""
    r0,g0,b0 = bg_rgb; t2=tol*tol
    data = list(img.getdata())
    img  = img.copy()
    img.putdata([(0,0,0,0) if (r-r0)**2+(g-g0)**2+(b-b0)**2<t2 else (r,g,b,a)
                 for r,g,b,a in data])
    return img

def save_frame(img, anim, idx, x0,y0,x1,y1, root):
    W,H=img.size
    x0=max(0,min(x0,W)); x1=max(0,min(x1,W))
    y0=max(0,min(y0,H)); y1=max(0,min(y1,H))
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

if __name__=='__main__':
    print('=== RESTORING ORIGINAL FROSTIA ===')
    sheet_path=os.path.join(ROOT,'tools','frostia_sheet.png')
    raw=Image.open(sheet_path).convert('RGBA')
    print(f'Sheet: {raw.width}x{raw.height}  bg=rgb(241,241,241)  tol=38')
    img=remove_bg_sheet(raw,(241,241,241),38)
    print('Background removed.')
    root=os.path.join(ROOT,'assets','sprites','frostia')

    # ── Original frame map from slice_two.py ──────────────────────
    frostia_map = {
     'idle':  [(157,11,224,114),(244,11,310,114),(331,11,398,114),(425,11,491,114),
               (506,11,581,114),(603,11,673,114),(702,11,769,114),(792,11,862,114)],
     'walk':  [(238,130,312,237),(327,130,401,237),(424,130,498,237),(512,130,580,237),
               (601,130,679,237),(679,130,758,237),(770,130,852,237),(878,130,948,237)],
     'run':   [(236,251,309,356),(330,251,408,356),(424,251,506,356),(517,251,613,356),
               (632,251,722,356),(733,251,816,356),(840,251,919,356),(840,251,919,356)],
     'jump':  [(160,365,230,480),(278,365,359,480),(413,365,486,480),
               (524,365,610,480),(635,365,726,480),(762,365,844,480)],
     'dash':  [(263,499,408,584),(418,499,573,584),(586,499,749,584),
               (789,499,879,584),(879,499,968,584),(789,499,879,584)],
     'block': [(156,611,244,708),(287,611,373,708),(422,611,509,708),(547,611,625,708)],
     'punch': [(388,730,511,830),(524,730,625,830),(652,730,729,830),
               (729,730,806,830),(806,730,881,830),(806,730,881,830)],
     'kick':  [(272,850,373,955),(389,850,497,955),(541,850,642,955),
               (676,850,777,955),(800,850,901,955),(800,850,901,955)],
     'special':[(12,980,119,1075),(119,980,226,1075),(226,980,333,1075),(346,980,470,1075),
                (470,980,594,1075),(606,980,683,1075),(693,980,858,1075),(858,980,1024,1075)],
     'ultimate':[(12,1091,130,1213),(130,1091,248,1213),(248,1091,366,1213),(366,1091,484,1213),
                 (484,1091,605,1213),(615,1091,681,1213),(691,1091,774,1213),
                 (774,1091,857,1213),(857,1091,940,1213),(940,1091,1024,1213)],
     'hurt':  [(156,1235,225,1320),(242,1235,320,1320),(341,1235,421,1320),(444,1235,517,1320)],
     'victory':[(259,1332,334,1429),(355,1332,417,1429),(440,1332,507,1429),
                (523,1332,603,1429),(624,1332,692,1429),(727,1332,785,1429)],
     'defeat': [(355,1445,449,1514),(460,1445,555,1514),(566,1445,669,1514),
                (684,1445,795,1514),(566,1445,669,1514),(460,1445,555,1514)],
    }

    # Remove new Frostia folders that don't belong to original
    for extra in ['attack']:
        d=os.path.join(root,extra)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith('.png'): os.remove(os.path.join(d,f))

    # Slice all original animations
    print()
    for anim, coords in frostia_map.items():
        clear(root,anim)
        for i,(x0,y0,x1,y1) in enumerate(coords):
            save_frame(img,anim,i+1,x0,y0,x1,y1,root)
        print(f'  {anim:<12}  {len(coords)} frames')

    # ── Verify ────────────────────────────────────────────────────
    anims=['idle','walk','run','jump','dash','block','punch','kick',
           'special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print()
    all_ok=True
    for a,e in zip(anims,exp):
        d=os.path.join(root,a)
        c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
        # Verify naming format: should be idle-1.png (not idle-01.png)
        files=sorted([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else []
        first=files[0] if files else 'NONE'
        ok=(c==e)
        if not ok: all_ok=False
        print(f'  {"OK  " if ok else "FAIL"}  {a:<12}  {c}/{e}  first={first}')
    print()
    print('FROSTIA ORIGINAL RESTORED!' if all_ok else 'Issues found above.')
