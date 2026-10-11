#!/usr/bin/env python3
"""
fix_all_clipping.py
===================
Re-slices ALL characters with:
  1. Larger output canvas (128x128 instead of 96x96)
  2. More crop padding (12px each side instead of 6px)
  3. Flood-fill bg removal per sheet
  4. Characters scale to FIT inside canvas keeping aspect ratio

For Frostia (zero-padded, 71×104 cells):
  Uses 80×112 canvas to give feet room at bottom.
"""
from PIL import Image
import os, shutil
from collections import deque

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISPLAY = 128   # larger output — prevents clipping for big characters
PAD     = 14    # crop padding on all sides

# ── Flood-fill bg removal ─────────────────────────────────────────
def flood_remove_bg(img, bg_rgb, tol=25):
    img  = img.convert('RGBA')
    data = list(img.getdata())
    W,H  = img.size
    r0,g0,b0 = bg_rgb; t2=tol*tol
    def is_bg(i):
        r,g,b,a=data[i]
        if a<15: return True
        return (r-r0)**2+(g-g0)**2+(b-b0)**2<=t2
    visited=bytearray(W*H); q=deque()
    for x in range(W):
        for y in [0,H-1]:
            i=y*W+x
            if not visited[i] and is_bg(i): visited[i]=1; q.append(i)
    for y in range(H):
        for x in [0,W-1]:
            i=y*W+x
            if not visited[i] and is_bg(i): visited[i]=1; q.append(i)
    while q:
        i=q.popleft(); r,g,b,a=data[i]; data[i]=(r,g,b,0); x,y=i%W,i//W
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<W and 0<=ny<H:
                ni=ny*W+nx
                if not visited[ni] and is_bg(ni): visited[ni]=1; q.append(ni)
    img.putdata(data); return img

# ── Save frame ────────────────────────────────────────────────────
def save(img, anim, idx, x0,y0,x1,y1, root, disp=DISPLAY, pad=PAD, zero_pad=False):
    W,H=img.size
    x0=max(0,x0-pad); x1=min(W,x1+pad)
    y0=max(0,y0-pad); y1=min(H,y1+pad)
    if x1<=x0 or y1<=y0: return
    crop=img.crop((x0,y0,x1,y1))
    crop.thumbnail((disp,disp),Image.LANCZOS)
    c=Image.new('RGBA',(disp,disp),(0,0,0,0))
    ox=(disp-crop.width)//2
    # Bottom-align so feet are at bottom of canvas
    oy=disp-crop.height
    c.paste(crop,(ox,oy),crop)
    num = f'{idx:02d}' if zero_pad else str(idx)
    c.save(os.path.join(root,anim,f'{anim}-{num}.png'),'PNG')

def clear(root,anim):
    d=os.path.join(root,anim); os.makedirs(d,exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.png'): os.remove(os.path.join(d,f))

def eq(x0,x1,n):
    fw=(x1-x0)/n
    return [(int(x0+i*fw),int(x0+(i+1)*fw)) for i in range(n)]

# ══════════════════════════════════════════════════════════════════
def do_blazor():
    print('BLAZOR...')
    img=Image.open(os.path.join(ROOT,'tools','blazor-sheet.png')).convert('RGBA')
    # Already transparent
    root=os.path.join(ROOT,'assets','sprites','blazor')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(137,200),(222,283),(304,366),(387,449),(472,536),(560,621),(644,705),(728,792)]):
        s('idle',i+1,x0,7,x1,114)
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(216,280),(303,367),(384,447),(469,531),(553,618),(641,702),(726,791),(814,879)]):
        s('walk',i+1,x0,130,x1,239)
    clear(root,'run')
    for i,(x0,x1) in enumerate([(214,286),(297,372),(381,455),(471,540),(550,627),(636,709),(727,799),(817,891)]):
        s('run',i+1,x0,254,x1,365)
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(135,203),(234,303),(343,413),(447,521),(564,639),(682,751)]):
        s('jump',i+1,x0,376,x1,485)
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(241,343),(357,475),(483,595),(605,707),(707,810),(483,595)]):
        s('dash',i+1,x0,503,x1,608)
    clear(root,'block')
    for i,(x0,x1) in enumerate([(142,219),(279,349),(404,476),(527,603)]):
        s('block',i+1,x0,615,x1,730)
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(238,316),(338,412),(435,525),(547,624),(647,743),(547,624)]):
        s('punch',i+1,x0,741,x1,852)
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(234,318),(338,411),(432,516),(536,623),(638,694),(694,751)]):
        s('kick',i+1,x0,863,x1,981)
    clear(root,'special')
    for i,(x0,x1) in enumerate([(233,304),(317,385),(401,469),(484,557),(570,675),(675,780),(780,883),(883,987)]):
        s('special',i+1,x0,999,x1,1115)
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate([(240,313),(327,398),(404,476),(488,563),(573,650),(670,741),(751,816),(817,882),(883,947),(948,1012)]):
        s('ultimate',i+1,x0,1122,x1,1234)
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(243,310),(359,428),(467,530),(467,530)]):
        s('hurt',i+1,x0,1243,x1,1335)
    clear(root,'victory')
    for i,(x0,x1) in enumerate([(242,299),(336,407),(446,519),(549,611),(654,715),(715,795)]):
        s('victory',i+1,x0,1336,x1,1444)
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(237,795,6)):
        s('defeat',i+1,x0,1460,x1,1514)

def do_aquara():
    print('AQUARA...')
    img=Image.open(os.path.join(ROOT,'tools','aquara_sheet.png')).convert('RGBA')
    root=os.path.join(ROOT,'assets','sprites','aquara')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(139,198),(246,305),(346,402),(439,497),(532,590),(625,685),(721,780),(816,875)]):
        s('idle',i+1,x0,15,x1,115)
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(124,184),(224,287),(323,387),(423,483),(516,570),(604,658),(694,749),(781,835)]):
        s('walk',i+1,x0,135,x1,231)
    clear(root,'run')
    for i,(x0,x1) in enumerate([(122,200),(220,298),(314,396),(416,497),(520,606),(628,709),(729,808),(827,906)]):
        s('run',i+1,x0,254,x1,359)
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(138,196),(237,293),(333,386),(430,485),(527,585),(635,696)]):
        s('jump',i+1,x0,363,x1,481)
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(20,171),(202,380),(402,564),(405,563),(599,765),(808,998)]):
        s('dash',i+1,x0,500,x1,589)
    clear(root,'block')
    for i,(x0,x1) in enumerate([(135,208),(240,306),(335,402),(428,498)]):
        s('block',i+1,x0,611,x1,705)
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(24,112),(143,227),(246,339),(353,440),(456,538),(556,664)]):
        s('punch',i+1,x0,722,x1,811)
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(35,129),(150,245),(265,357),(378,473),(498,616),(640,752)]):
        s('kick',i+1,x0,827,x1,933)
    clear(root,'special')
    for i,(x0,x1) in enumerate([(26,132),(142,265),(273,392),(403,541),(555,662),(674,769),(769,864),(864,959)]):
        s('special',i+1,x0,954,x1,1046)
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate([(22,126),(142,251),(267,380),(397,494),(518,584),(585,650),(668,736),(737,805),(806,873),(874,1005)]):
        s('ultimate',i+1,x0,1065,x1,1169)
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(24,86),(130,206),(243,308),(344,398)]):
        s('hurt',i+1,x0,1187,x1,1281)
    clear(root,'victory')
    for i,(x0,x1) in enumerate([(29,94),(127,204),(233,318),(347,429),(465,540),(570,637)]):
        s('victory',i+1,x0,1298,x1,1407)
    clear(root,'defeat')
    for i,(x0,x1) in enumerate([(237,326),(340,410),(410,469),(478,572),(586,685),(688,795)]):
        s('defeat',i+1,x0,1460,x1,1499)

def do_terron():
    print('TERRON...')
    raw=Image.open(os.path.join(ROOT,'tools','terron_sheet.png')).convert('RGBA')
    img=flood_remove_bg(raw,(11,15,17),30)
    root=os.path.join(ROOT,'assets','sprites','terron')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(16,78),(105,181),(206,280),(305,379),(405,477),(506,577),(607,677),(708,777)]):
        s('idle',i+1,x0,42,x1,168)
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(111,178),(210,275),(314,374),(409,471),(511,573),(609,670),(710,773),(810,869)]):
        s('walk',i+1,x0,174,x1,296)
    clear(root,'run')
    for i,(x0,x1) in enumerate([(105,184),(206,280),(306,384),(403,483),(499,577),(601,681),(702,781),(802,881)]):
        s('run',i+1,x0,306,x1,421)
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(106,181),(206,277),(308,376),(399,468),(506,568),(602,675)]):
        s('jump',i+1,x0,437,x1,539)
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(17,78),(113,179),(208,275),(311,373),(410,472),(508,565)]):
        s('dash',i+1,x0,563,x1,672)
    clear(root,'block')
    for i,(x0,x1) in enumerate([(17,118),(152,224),(248,328),(359,432)]):
        s('block',i+1,x0,698,x1,781)
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(459,542),(568,654),(674,764),(787,869),(896,971),(896,971)]):
        s('punch',i+1,x0,698,x1,781)
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(17,112),(154,216),(246,318),(350,424),(463,550),(561,659)]):
        s('kick',i+1,x0,804,x1,916)
    clear(root,'special')
    for i,(x0,x1) in enumerate([(18,89),(154,219),(248,328),(354,435),(461,544),(567,648),(671,762),(781,868)]):
        s('special',i+1,x0,930,x1,1032)
    clear(root,'ultimate')
    ult8=[(19,118),(156,216),(256,324),(363,430),(463,539),(570,648),(678,754),(780,862)]
    for i,(x0,x1) in enumerate(ult8):
        s('ultimate',i+1,x0,1052,x1,1138)
    for i,(x0,x1) in enumerate(eq(780,995,2)):
        s('ultimate',9+i,x0,1052,x1,1138)
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(21,102),(156,222),(263,323),(362,427)]):
        s('hurt',i+1,x0,1156,x1,1240)
    clear(root,'victory')
    for i,(x0,x1) in enumerate(eq(462,840,6)):
        s('victory',i+1,x0,1156,x1,1240)
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(414,993,6)):
        s('defeat',i+1,x0,1247,x1,1285)

def do_voltra():
    print('VOLTRA...')
    raw=Image.open(os.path.join(ROOT,'tools','voltra_sheet.png')).convert('RGBA')
    img=flood_remove_bg(raw,(241,242,243),42)
    root=os.path.join(ROOT,'assets','sprites','voltra')
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

def do_zephyr():
    print('ZEPHYR...')
    raw=Image.open(os.path.join(ROOT,'tools','zephyr_sheet.png')).convert('RGBA')
    img=flood_remove_bg(raw,(243,244,244),38)
    root=os.path.join(ROOT,'assets','sprites','zephyr')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)
    X8=[(139,198),(246,305),(346,402),(439,497),(532,590),(625,685),(721,780),(816,875)]
    X6=X8[:6]; X4=X8[:4]
    clear(root,'idle')
    for i,(x0,x1) in enumerate(X8): s('idle',i+1,x0,9,x1,116)
    clear(root,'walk')
    for i,(x0,x1) in enumerate(X8): s('walk',i+1,x0,135,x1,240)
    clear(root,'run')
    for i,(x0,x1) in enumerate(X8): s('run',i+1,x0,261,x1,359)
    clear(root,'jump')
    for i,(x0,x1) in enumerate(X6): s('jump',i+1,x0,375,x1,482)
    clear(root,'dash')
    for i,(x0,x1) in enumerate(X6): s('dash',i+1,x0,503,x1,603)
    clear(root,'block')
    for i,(x0,x1) in enumerate(X4): s('block',i+1,x0,623,x1,716)
    clear(root,'punch')
    segs6=get_segs(img,623,716)[4:10]
    for i,(x0,x1) in enumerate(segs6[:6]): s('punch',i+1,x0,623,x1,716)
    for e in range(len(segs6)+1,7):
        shutil.copy(os.path.join(root,'punch',f'punch-{len(segs6)}.png'),
                    os.path.join(root,'punch',f'punch-{e}.png'))
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]): s('kick',i+1,x0,726,x1,842)
    clear(root,'special')
    spec=get_segs(img,726,842)[6:]
    for i,(x0,x1) in enumerate(spec[:8]): s('special',i+1,x0,726,x1,842)
    for e in range(len(spec)+1,9):
        shutil.copy(os.path.join(root,'special',f'special-{min(len(spec),7)}.png'),
                    os.path.join(root,'special',f'special-{e}.png'))
    clear(root,'ultimate')
    ult_s=get_segs(img,849,943)[:10]
    for i,(x0,x1) in enumerate(ult_s): s('ultimate',i+1,x0,849,x1,943)
    for e in range(len(ult_s)+1,11):
        shutil.copy(os.path.join(root,'ultimate',f'ultimate-{len(ult_s)}.png'),
                    os.path.join(root,'ultimate',f'ultimate-{e}.png'))
    clear(root,'hurt')
    b9=get_segs(img,968,1010)
    for i,(x0,x1) in enumerate(b9[:4]): s('hurt',i+1,x0,849,x1,943)
    for e in range(len(b9[:4])+1,5):
        shutil.copy(os.path.join(root,'hurt',f'hurt-{min(len(b9[:4]),3)}.png'),
                    os.path.join(root,'hurt',f'hurt-{e}.png'))
    clear(root,'victory')
    for i,(x0,x1) in enumerate(b9[:6]): s('victory',i+1,x0,849,x1,943)
    for e in range(len(b9[:6])+1,7):
        shutil.copy(os.path.join(root,'victory',f'victory-{min(len(b9[:6]),5)}.png'),
                    os.path.join(root,'victory',f'victory-{e}.png'))
    clear(root,'defeat')
    def_s=b9[-6:] if len(b9)>=6 else b9
    for i,(x0,x1) in enumerate(def_s[:6]): s('defeat',i+1,x0,849,x1,943)
    for e in range(len(def_s)+1,7):
        shutil.copy(os.path.join(root,'defeat',f'defeat-{min(len(def_s),5)}.png'),
                    os.path.join(root,'defeat',f'defeat-{e}.png'))

def do_noctis():
    print('NOCTIS...')
    raw=Image.open(os.path.join(ROOT,'tools','noctis.png')).convert('RGBA')
    img=flood_remove_bg(raw,(10,15,23),30)
    root=os.path.join(ROOT,'assets','sprites','noctis')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(157,209),(245,294),(331,382),(419,469),(509,560),(596,647),(682,733),(768,821)]): s('idle',i+1,x0,13,x1,109)
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(222,297),(315,380),(406,473),(498,560),(587,645),(671,734),(760,822),(849,909)]): s('walk',i+1,x0,135,x1,229)
    clear(root,'run')
    for i,(x0,x1) in enumerate([(402,480),(493,568),(579,663),(663,747),(747,831),(844,917),(844,917),(844,917)]): s('run',i+1,x0,255,x1,348)
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(278,348),(398,474),(519,590),(638,724),(763,839),(763,839)]): s('jump',i+1,x0,364,x1,476)
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(266,380),(395,506),(521,637),(655,788),(819,968),(819,968)]): s('dash',i+1,x0,497,x1,582)
    clear(root,'block')
    for i,(x0,x1) in enumerate([(155,230),(259,338),(373,458),(496,581)]): s('block',i+1,x0,598,x1,696)
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(265,380),(395,492),(511,608),(622,700),(700,778),(778,856)]): s('punch',i+1,x0,711,x1,810)
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(147,255),(274,384),(384,494),(516,609),(620,733),(757,844)]): s('kick',i+1,x0,834,x1,941)
    clear(root,'special')
    for i,(x0,x1) in enumerate(eq(262,1009,8)): s('special',i+1,x0,955,x1,1075)
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(11,1015,10)): s('ultimate',i+1,x0,1086,x1,1214)
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(153,230),(247,313),(345,413),(449,557)]): s('hurt',i+1,x0,1216,x1,1294)
    clear(root,'victory')
    for i,(x0,x1) in enumerate([(173,236),(277,329),(365,425),(468,528),(573,647),(677,729)]): s('victory',i+1,x0,1303,x1,1402)
    clear(root,'defeat')
    for i,(x0,x1) in enumerate([(266,359),(376,468),(491,595),(621,711),(738,855),(738,855)]): s('defeat',i+1,x0,1429,x1,1492)

def do_venom():
    print('VENOM...')
    img=Image.open(os.path.join(ROOT,'tools','venom_sheet.png')).convert('RGBA')
    root=os.path.join(ROOT,'assets','sprites','venom')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(13,86),(126,208),(232,315),(346,425),(458,540),(576,652),(694,773),(809,887)]): s('idle',i+1,x0,6,x1,138)
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(10,95),(120,197),(225,314),(347,423),(451,536),(561,649),(675,756),(783,881)]): s('walk',i+1,x0,154,x1,275)
    clear(root,'run')
    for i,(x0,x1) in enumerate([(12,99),(137,238),(277,385),(416,505),(532,631),(674,789),(811,913),(949,1050)]): s('run',i+1,x0,293,x1,419)
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(14,91),(129,217),(258,349),(409,485),(540,627),(680,753)]): s('jump',i+1,x0,427,x1,549)
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(17,105),(148,222),(258,354),(396,489),(517,621),(653,743)]): s('dash',i+1,x0,554,x1,687)
    clear(root,'block')
    for i,(x0,x1) in enumerate([(16,112),(129,224),(244,367),(376,441)]): s('block',i+1,x0,701,x1,817)
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(441,506),(506,572),(572,638),(640,769),(783,897),(927,1044)]): s('punch',i+1,x0,701,x1,817)
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]): s('kick',i+1,x0,832,x1,933)
    clear(root,'special')
    for i,(x0,x1) in enumerate([(783,915),(927,1062),(13,101),(117,239),(247,363),(367,485),(502,640),(651,783)]): s('special',i+1,x0,832,x1,933)
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(17,1176,10)): s('ultimate',i+1,x0,1047,x1,1157)
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(15,88),(142,211),(257,334),(363,473)]): s('hurt',i+1,x0,1163,x1,1271)
    clear(root,'victory')
    for i,(x0,x1) in enumerate([(494,610),(631,756),(779,880),(909,1014),(1046,1180),(1046,1180)]): s('victory',i+1,x0,1163,x1,1271)
    clear(root,'defeat')
    for i,(x0,x1) in enumerate(eq(15,1180,6)): s('defeat',i+1,x0,1163,x1,1271)

def do_floren():
    print('FLOREN...')
    img=Image.open(os.path.join(ROOT,'tools','floren_sheet.png')).convert('RGBA')
    root=os.path.join(ROOT,'assets','sprites','floren')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)
    clear(root,'idle')
    for i,(x0,x1) in enumerate([(145,209),(235,300),(322,388),(408,475),(496,562),(581,647),(668,739),(759,826)]): s('idle',i+1,x0,20,x1,116)
    clear(root,'walk')
    for i,(x0,x1) in enumerate([(139,207),(225,299),(317,388),(407,476),(492,562),(581,651),(669,737),(756,825)]): s('walk',i+1,x0,135,x1,232)
    clear(root,'run')
    for i,(x0,x1) in enumerate([(137,212),(227,301),(319,392),(405,478),(492,561),(576,649),(661,733),(754,826)]): s('run',i+1,x0,255,x1,351)
    clear(root,'jump')
    for i,(x0,x1) in enumerate([(149,213),(237,303),(331,394),(418,482),(506,584),(611,685)]): s('jump',i+1,x0,357,x1,481)
    clear(root,'dash')
    for i,(x0,x1) in enumerate([(138,254),(268,393),(407,517),(534,647),(664,770),(791,891)]): s('dash',i+1,x0,500,x1,578)
    clear(root,'block')
    for i,(x0,x1) in enumerate([(267,361),(408,488),(521,592),(521,592)]): s('block',i+1,x0,610,x1,704)
    clear(root,'punch')
    for i,(x0,x1) in enumerate([(149,275),(292,399),(419,534),(545,670),(691,818),(818,945)]): s('punch',i+1,x0,722,x1,813)
    clear(root,'kick')
    for i,(x0,x1) in enumerate([(147,273),(286,389),(403,498),(516,627),(653,753),(653,753)]): s('kick',i+1,x0,838,x1,939)
    clear(root,'special')
    for i,(x0,x1) in enumerate([(7,137),(140,227),(231,324),(331,436),(437,544),(545,687),(687,829),(829,973)]): s('special',i+1,x0,943,x1,1077)
    clear(root,'ultimate')
    for i,(x0,x1) in enumerate(eq(7,1007,10)): s('ultimate',i+1,x0,1064,x1,1225)
    clear(root,'hurt')
    for i,(x0,x1) in enumerate([(140,200),(230,294),(326,400),(425,494)]): s('hurt',i+1,x0,1228,x1,1320)
    clear(root,'victory')
    for i,(x0,x1) in enumerate([(144,218),(243,309),(336,404),(431,498),(527,598),(623,673)]): s('victory',i+1,x0,1332,x1,1430)
    clear(root,'defeat')
    for i,(x0,x1) in enumerate([(247,333),(353,442),(464,550),(579,663),(695,796),(695,796)]): s('defeat',i+1,x0,1438,x1,1502)

def do_solara():
    print('SOLARA...')
    raw=Image.open(os.path.join(ROOT,'assets','revise_character','solara_newcharcter.png')).convert('RGBA')
    img=flood_remove_bg(raw,(0,0,0),20)
    root=os.path.join(ROOT,'assets','sprites','solara')
    def s(a,i,x0,y0,x1,y1): save(img,a,i,x0,y0,x1,y1,root)
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
    clear(root,'idle');    [s('idle',i+1,x0,12,x1,98)   for i,(x0,x1) in enumerate(BAND1_X)]
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

def get_segs(img, y0, y1, mw=30):
    W,H=img.size; pix=img.load()
    cols=[(x,sum(1 for y in range(y0,y1,2) if pix[x,y][3]>20)) for x in range(W)]
    mx=max(c[1] for c in cols) or 1; thr=mx*0.03
    in_g=True; segs=[]; fs=0
    for x,v in cols:
        if v<=thr and not in_g: segs.append((fs,x)); in_g=True
        elif v>thr and in_g: fs=x; in_g=False
    if not in_g: segs.append((fs,W))
    return [(a,b) for a,b in segs if b-a>=mw]

# ── Run all ───────────────────────────────────────────────────────
if __name__=='__main__':
    print(f'=== RE-SLICING ALL CHARACTERS (DISPLAY={DISPLAY}px, PAD={PAD}px) ===\n')
    do_blazor()
    do_aquara()
    do_terron()
    do_voltra()
    do_zephyr()
    do_noctis()
    do_venom()
    do_floren()
    do_solara()

    # Verify counts
    chars=['blazor','aquara','terron','voltra','zephyr','frostia','floren','solara','noctis','venom']
    anims=['idle','walk','run','jump','dash','block','punch','kick','special','ultimate','hurt','victory','defeat']
    exp  =[8,8,8,6,6,4,6,6,8,10,4,6,6]
    print('\n=== FRAME COUNT CHECK ===')
    for char in chars:
        fails=[]
        for a,e in zip(anims,exp):
            d=os.path.join(ROOT,'assets','sprites',char,a)
            c=len([f for f in os.listdir(d) if f.endswith('.png')]) if os.path.isdir(d) else 0
            if c!=e: fails.append(f'{a}:{c}/{e}')
        print(f'  {"OK  " if not fails else "FAIL"}  {char.upper():<10}  {fails if fails else "all OK"}')

    print(f'\nAll done! DISPLAY={DISPLAY}px  PAD={PAD}px')
    print('Rebuild index.html to apply.')
