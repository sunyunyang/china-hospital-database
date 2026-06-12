import csv, re, sys, time
from collections import defaultdict

TMP = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode"
BASE = "/Users/williamsun/Downloads/documents/06_Others/Input/医疗机构数据"
NATL = f"{TMP}/national_hospitals.csv"
AHOSP = f"{TMP}/hospitals.csv"
ZJ = f"{TMP}/zj_hospital_list.csv"
SH = f"{TMP}/shanghai_all_health.csv"
SD = f"{TMP}/shandong_hospitals_2025.xlsx"
OUT = f"{TMP}/final_hospitals.csv"

prov_map = {'北京':'北京市','天津':'天津市','上海':'上海市','重庆':'重庆市',
    '内蒙古':'内蒙古自治区','广西':'广西壮族自治区','西藏':'西藏自治区',
    '宁夏':'宁夏回族自治区','新疆':'新疆维吾尔自治区'}
def fix_prov(p):
    if not p: return ''
    p = p.strip()
    if p in prov_map: return prov_map[p]
    if p.endswith('省') or p.endswith('市') or p.endswith('自治区'): return p
    return p + '省'

PREFIXES = [
    '上海交通大学医学院附属','上海交通大学附属','上海中医药大学附属',
    '复旦大学附属','同济大学附属','海军军医大学附属','第二军医大学附属',
    '北京协和医学院','北京大学附属','北京大学','首都医科大学附属',
    '中山大学附属','南方医科大学附属','南方医科大学',
    '广州医科大学附属','广州中医药大学附属','广东医科大学附属',
    '华中科技大学同济医学院附属','武汉大学附属',
    '浙江大学医学院附属','浙江大学附属','温州医科大学附属',
    '南京医科大学附属','南京大学医学院附属','东南大学附属',
    '中国医科大学附属','大连医科大学附属','锦州医科大学附属',
    '山东大学附属','山东大学齐鲁医学院','青岛大学附属',
    '天津医科大学附属','南开大学附属',
    '河北医科大学附属','河北大学附属',
    '山西医科大学附属','山西中医药大学附属',
    '内蒙古医科大学附属','内蒙古民族大学附属',
    '哈尔滨医科大学附属','黑龙江中医药大学附属',
    '吉林大学附属','延边大学附属','长春中医药大学附属',
    '郑州大学附属','河南大学附属','新乡医学院附属',
    '安徽医科大学附属','皖南医学院附属','蚌埠医学院附属',
    '南昌大学附属','江西中医药大学附属',
    '福建医科大学附属','福建中医药大学附属',
    '广西医科大学附属','广西中医药大学附属',
    '海南医学院附属','重庆医科大学附属',
    '四川大学华西医院','四川大学华西','四川大学附属',
    '西南医科大学附属','成都中医药大学附属','川北医学院附属',
    '昆明医科大学附属','云南中医药大学附属',
    '西安交通大学附属','延安大学附属','陕西中医药大学附属',
    '兰州大学附属','甘肃中医药大学附属',
    '宁夏医科大学附属','青海大学附属',
    '新疆医科大学附属','石河子大学附属',
    '徐州医科大学附属','南通大学附属','扬州大学附属',
    '湖南中医药大学附属','南华大学附属',
    '贵州医科大学附属','遵义医科大学附属',
    '中国人民解放军','解放军','武警部队','中国医学科学院',
]

def normalize(s):
    if not s: return ''
    s = re.sub(r'[（(][^）)]*[）)]', '', s)
    for p in sorted(PREFIXES, key=len, reverse=True):
        if s.startswith(p):
            s = s[len(p):]
            break
    s = re.sub(r'^(上海市|北京市|天津市|重庆市)', '', s)
    return s.strip()

def parse_address(addr):
    if not addr: return ('','','','')
    prov, city, district, detail = '', '', '', addr
    for pv in ['内蒙古自治区','广西壮族自治区','西藏自治区','宁夏回族自治区','新疆维吾尔自治区',
               '北京市','天津市','上海市','重庆市']:
        if addr.startswith(pv):
            prov = pv; detail = addr[len(pv):]; break
    if not prov:
        m = re.match(r'(.+?省)', addr)
        if m: prov = m.group(1); detail = addr[len(prov):]
        else:
            m = re.match(r'(.+?自治区)', addr)
            if m: prov = m.group(1); detail = addr[len(prov):]
    if detail:
        m = re.match(r'(.+?市)', detail)
        if m: city = m.group(1); detail = detail[len(city):]
    if detail:
        m = re.match(r'(.+?[区旗县])', detail)
        if m: district = m.group(1); detail = detail[len(district):]
    return (prov, city, district, detail.strip('；;，, '))

t0 = time.time()

natl_rows = []
with open(NATL, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        natl_rows.append(row)
natl_n = len(natl_rows)

zj_uscc = {}
with open(ZJ, 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        nm = row.get('定点医药机构名称','').strip()
        uc = row.get('统一社会信用代码','').strip()
        mt = row.get('定点医疗服务机构类型','').strip()
        if nm and uc:
            zj_uscc[nm] = (uc, mt)

sh_uscc = {}
with open(SH, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        nm = row.get('name','').strip()
        uc = row.get('code','').strip()
        if nm and uc:
            sh_uscc[nm] = uc

sd_uscc = {}
try:
    import openpyxl
    wb = openpyxl.load_workbook(SD)
    ws = wb.active
    for row in ws.iter_rows(min_row=3, values_only=True):
        name = str(row[1]).strip() if row[1] else ''
        uscc = str(row[3]).strip() if row[3] else ''
        if name and uscc:
            for n in name.split('、'):
                n = n.strip()
                if n and '互联网医院' not in n:
                    sd_uscc[n] = uscc
except Exception as e:
    print(f"山东: {e}", file=sys.stderr)

ahosp_idx = defaultdict(list)
with open(AHOSP, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        p = fix_prov(row.get('province',''))
        n = row.get('name','').strip()
        if p and n:
            ahosp_idx[(p, n)].append(row)
            ahosp_idx[(p, normalize(n))].append(row)

print(f"Loaded: {natl_n} natl, {len(zj_uscc)} ZJ, {len(sh_uscc)} SH, {len(sd_uscc)} SD, {time.time()-t0:.0f}s", file=sys.stderr)

# 浙江 USCC (norm match)
zj_norm_idx = defaultdict(list)
for name, (uc, mt) in zj_uscc.items():
    zj_norm_idx[normalize(name)].append((name, uc, mt))

zj_new = 0
for row in natl_rows:
    if row['province'].strip() != '浙江省': continue
    n = row['name'].strip()
    if n in zj_uscc: continue
    nn = normalize(n)
    if nn in zj_norm_idx:
        zj_uscc[n] = zj_norm_idx[nn][0][1:]
        zj_new += 1
print(f"  浙江 +{zj_new} ({time.time()-t0:.0f}s)", file=sys.stderr)

# Output
fields = ['h_code','province','name','type','level','nature','address',
          'province_parsed','city_parsed','district_parsed',
          'ahosp_name','ahosp_grade','ahosp_city',
          'uscc','uscc_source']

uscc_total = 0
ahosp_total = 0

with open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for i, row in enumerate(natl_rows):
        if i % 100000 == 0 and i > 0:
            print(f"  {i}/{natl_n}...", file=sys.stderr)
        p, n = row['province'].strip(), row['name'].strip()
        uc_val, uc_src = '', ''
        if n in zj_uscc: uc_val = zj_uscc[n][0]; uc_src = '浙江'
        elif n in sh_uscc: uc_val = sh_uscc[n]; uc_src = '上海'
        elif n in sd_uscc: uc_val = sd_uscc[n]; uc_src = '山东'
        if uc_val: uscc_total += 1
        ah = (ahosp_idx.get((p, n)) or ahosp_idx.get((p, normalize(n))) or [None])[0]
        if ah: ahosp_total += 1
        grade = re.sub(r'\*\*.*', '', ah.get('grade','')).strip() if ah else ''
        pp, cp, dp, _ = parse_address(row.get('address',''))
        w.writerow({
            'h_code': row['code'], 'province': p, 'name': n,
            'type': row.get('type',''), 'level': row.get('level',''),
            'nature': row.get('nature',''), 'address': row.get('address',''),
            'province_parsed': pp, 'city_parsed': cp, 'district_parsed': dp,
            'ahosp_name': ah.get('name','') if ah else '',
            'ahosp_grade': grade,
            'ahosp_city': ah.get('city','') if ah else '',
            'uscc': uc_val, 'uscc_source': uc_src,
        })

zj_c = sum(1 for r in natl_rows if r['name'].strip() in zj_uscc)
sh_c = sum(1 for r in natl_rows if r['name'].strip() in sh_uscc)
sd_c = sum(1 for r in natl_rows if r['name'].strip() in sd_uscc)
del ahosp_idx
print(f"\nFinal:", file=sys.stderr)
print(f"Total: {natl_n}", file=sys.stderr)
print(f"USCC: {uscc_total} ({100*uscc_total/natl_n:.1f}%)  ZJ:{zj_c} SH:{sh_c} SD:{sd_c}", file=sys.stderr)
print(f"a-hospital: {ahosp_total} ({100*ahosp_total/natl_n:.1f}%)", file=sys.stderr)
print(f"Time: {time.time()-t0:.0f}s", file=sys.stderr)
