# 從交通部觀光署「觀光資訊資料庫」（政府資料開放授權條款第1版）挑出有名的景點，
# 下載第一張照片、縮小後存進網站，讓拍立得可以直接使用（同網域，不會有跨網站限制）。
import json, hashlib, io, os, sys, time, urllib.request
from PIL import Image
SRC='data/tw_attractions.json'; OUT='img/tw'; MAN='data/tw_photos.json'
HI=['國家公園','國家森林遊樂區','國家風景區','夜市','老街','101','故宮','紀念堂','燈塔','日月潭','阿里山','太魯閣','墾丁','九份','十分','淡水','野柳','清境','合歡山','龍山寺','赤崁','安平','西門','大稻埕','鹿港','旗津','駁二','蓮池潭','三仙台','七星潭','龜山島','小琉球','綠島','蘭嶼','澎湖','金門']
MID=['寺','宮','廟','古蹟','車站','博物館','美術館','步道','瀑布','湖','潭','海灘','沙灘','溫泉','公園','碼頭','古道','燈會','花海','山','林場','濕地','教堂','城','砲台','橋','港']
CAP=int(os.environ.get('CAP_PER_CITY','40'))
# 只用政府機關網站上的照片；來源標示看起來是民間（民宿、店家、個人攝影）的一律不用
from urllib.parse import urlparse
OFFICIAL={'newtaipei.travel','www.travel.taipei','khh.travel','hualien.travel','kinmen.travel','www.twtainan.net','www.ali-nsa.net','map.culture.tw'}
GOVWORDS=('政府','市','縣','處','局','署','管理','公所','分署','中心','部','鄉','鎮','區')
def official(url,credit):
    h=urlparse(url).netloc
    if not (h.endswith('.gov.tw') or h in OFFICIAL): return False
    c=(credit or '').strip()
    return c=='' or any(w in c for w in GOVWORDS)
def score(n):
    s=0
    for k in HI:
        if k in n: s+=10
    for k in MID:
        if k in n: s+=2
    return s
d=json.load(open(SRC,encoding='utf-8'))
by={}
for x in d:
    by.setdefault(x[4] or '其他',[]).append(x)
pick=[]
for city,L in by.items():
    L=sorted(L,key=lambda x:-score(x[0]))
    pick+= [x for x in L if score(x[0])>0 and any(official(u,c) for u,c in x[3])][:CAP]
old={}
if os.path.exists(MAN):
    for r in json.load(open(MAN,encoding='utf-8')): old[r[0]+'|'+str(r[1])]=r
os.makedirs(OUT,exist_ok=True)
man=[];ok=fail=0
for x in pick:
    name,lat,lng,imgs,city=x
    key=name+'|'+str(lat)
    if key in old and os.path.exists(old[key][3]) and official(*next(([u,c] for u,c in imgs if u and f"{OUT}/{hashlib.md5(u.encode()).hexdigest()[:12]}.jpg"==old[key][3]),['',''])): man.append(old[key]); continue
    for url,credit in [i for i in imgs if official(i[0],i[1])]:
        fn=f"{OUT}/{hashlib.md5(url.encode()).hexdigest()[:12]}.jpg"
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (cloudwalkies open-data photo cache)'})
            b=urllib.request.urlopen(req,timeout=20).read()
            im=Image.open(io.BytesIO(b)).convert('RGB')
            if min(im.size)<400: continue
            im.thumbnail((1100,1100)); im.save(fn,'JPEG',quality=80,optimize=True,progressive=True)
            man.append([name,lat,lng,fn,credit or '',city]); ok+=1; break
        except Exception as e:
            fail+=1; continue
    time.sleep(.15)
json.dump(man,open(MAN,'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
keep={r[3] for r in man}
for f in os.listdir(OUT):
    if f'{OUT}/{f}' not in keep: os.remove(f'{OUT}/{f}')
print('picked',len(pick),'saved',len(man),'new',ok,'failed tries',fail)
