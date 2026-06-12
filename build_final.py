import csv, re, sys
from collections import defaultdict

NATL = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/national_hospitals.csv"
AHOSP = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/hospitals.csv"
ZJ = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/zj_hospital_list.csv"
SH = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/shanghai_all_health.csv"
OUT = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/final_hospitals.csv"

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
    '华中科技大学同济医学院附属','武汉大学附属','武汉大学人民医院',
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
    s = re.sub(r'[（(].*?[）)]', '', s)
    for p in sorted(PREFIXES, key=len, reverse=True):
        if s.startswith(p):
            s = s[len(p):]
            break
    s = re.sub(r'^(上海市|北京市|天津市|重庆市)', '', s)
    return s.strip()

print("Step 1: Load national医保 data (514k records)", file=sys.stderr)
natl_rows = []
with open(NATL, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        natl_rows.append(row)
natl_n = len(natl_rows)
print(f"  Loaded {natl_n} records", file=sys.stderr)

print("Step 2: Load浙江 USCC data", file=sys.stderr)
zj_uscc = {}
with open(ZJ, 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        nm = row.get('定点医药机构名称', '').strip()
        uc = row.get('统一社会信用代码', '').strip()
        mt = row.get('定点医疗服务机构类型', '').strip()
        if nm and uc:
            zj_uscc[nm] = (uc, mt)
print(f"  Loaded {len(zj_uscc)} USCC entries", file=sys.stderr)

print("Step 3: Load上海 USCC data", file=sys.stderr)
sh_uscc = {}
try:
    with open(SH, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            nm = row.get('name', '').strip()
            uc = row.get('code', '').strip()
            if nm and uc:
                sh_uscc[nm] = uc
except FileNotFoundError:
    pass
print(f"  Loaded {len(sh_uscc)} entries", file=sys.stderr)

print("Step 4: Load a-hospital data for matching", file=sys.stderr)
# Build index of a-hospital by province+normalized name
ahosp_index = defaultdict(list)
with open(AHOSP, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        p = fix_prov(row.get('province',''))
        n = row.get('name','').strip()
        if p and n:
            ahosp_index[(p, normalize(n))].append(row)
print(f"  Indexed a-hospital records", file=sys.stderr)

print("Step 5: Build output", file=sys.stderr)
fields = [
    'h_code', 'province', 'name', 'type', 'level', 'nature', 'address',
    'ahosp_name', 'ahosp_grade', 'ahosp_city', 'ahosp_phone', 'ahosp_departments',
    'uscc', 'uscc_source',
]

matched = 0
uscc_found = 0

with open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    
    for i, row in enumerate(natl_rows):
        if i % 100000 == 0:
            print(f"  {i}/{natl_n}...", file=sys.stderr)
        
        prov = row['province'].strip()
        name = row['name'].strip()
        code = row['code'].strip()
        norm = normalize(name)
        
        uscc_val = ''
        uscc_src = ''
        
        # Look up USCC from浙江 first, then上海
        if name in zj_uscc:
            uscc_val, _ = zj_uscc[name]
            uscc_src = '浙江'
        elif name in sh_uscc:
            uscc_val = sh_uscc[name]
            uscc_src = '上海'
        
        if uscc_val:
            uscc_found += 1
        
        # Match with a-hospital
        ahosp_info = ahosp_index.get((prov, norm), [])
        if not ahosp_info:
            # Try without normalization
            ahosp_info = ahosp_index.get((prov, name), [])
        
        out = {
            'h_code': code,
            'province': prov,
            'name': name,
            'type': row.get('type', ''),
            'level': row.get('level', ''),
            'nature': row.get('nature', ''),
            'address': row.get('address', ''),
            'ahosp_name': '',
            'ahosp_grade': '',
            'ahosp_city': '',
            'ahosp_phone': '',
            'ahosp_departments': '',
            'uscc': uscc_val,
            'uscc_source': uscc_src,
        }
        
        if ahosp_info:
            matched += 1
            a = ahosp_info[0]
            out['ahosp_name'] = a.get('name', '')
            out['ahosp_grade'] = a.get('grade', '')
            out['ahosp_city'] = a.get('city', '')
            out['ahosp_phone'] = a.get('phone', '')
            out['ahosp_departments'] = a.get('departments', '')
        
        w.writerow(out)

print(f"\n=== Final Results ===", file=sys.stderr)
print(f"Total records: {natl_n}", file=sys.stderr)
print(f"With a-hospital match: {matched} ({100*matched/natl_n:.1f}%)", file=sys.stderr)
print(f"With USCC: {uscc_found} ({100*uscc_found/natl_n:.1f}%)", file=sys.stderr)
print(f"Output: {OUT}", file=sys.stderr)
