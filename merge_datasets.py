import csv, re, sys, time
from collections import defaultdict

AHOSP = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/hospitals.csv"
NATL = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/national_hospitals.csv"
ZJ = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/zj_hospital_list.csv"
OUT = "/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode/merged_hospitals.csv"

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
    '上海交通大学医学院附属', '上海交通大学附属', '上海中医药大学附属',
    '复旦大学附属', '同济大学附属', '海军军医大学附属', '第二军医大学附属',
    '北京协和医学院', '北京大学附属', '北京大学', '首都医科大学附属',
    '中山大学附属', '南方医科大学附属', '南方医科大学',
    '广州医科大学附属', '广州中医药大学附属', '广东医科大学附属',
    '华中科技大学同济医学院附属', '武汉大学附属',
    '浙江大学医学院附属', '浙江大学附属', '温州医科大学附属',
    '南京医科大学附属', '南京大学医学院附属', '东南大学附属',
    '中国医科大学附属', '大连医科大学附属', '锦州医科大学附属',
    '山东大学附属', '山东大学齐鲁医学院', '青岛大学附属',
    '天津医科大学附属', '南开大学附属',
    '河北医科大学附属', '河北大学附属',
    '山西医科大学附属', '山西中医药大学附属',
    '内蒙古医科大学附属', '内蒙古民族大学附属',
    '哈尔滨医科大学附属', '黑龙江中医药大学附属',
    '吉林大学附属', '延边大学附属', '长春中医药大学附属',
    '郑州大学附属', '河南大学附属', '新乡医学院附属',
    '安徽医科大学附属', '皖南医学院附属', '蚌埠医学院附属',
    '南昌大学附属', '江西中医药大学附属',
    '福建医科大学附属', '福建中医药大学附属',
    '广西医科大学附属', '广西中医药大学附属',
    '海南医学院附属',
    '重庆医科大学附属',
    '四川大学华西医院', '四川大学华西', '四川大学附属',
    '西南医科大学附属', '成都中医药大学附属', '川北医学院附属',
    '昆明医科大学附属', '云南中医药大学附属',
    '西安交通大学附属', '延安大学附属', '陕西中医药大学附属',
    '兰州大学附属', '甘肃中医药大学附属',
    '宁夏医科大学附属', '青海大学附属',
    '新疆医科大学附属', '石河子大学附属',
    '徐州医科大学附属', '南通大学附属', '扬州大学附属',
    '湖南中医药大学附属', '南华大学附属',
    '贵州医科大学附属', '遵义医科大学附属',
    '西藏大学附属',
    '中国人民解放军', '解放军', '武警部队',
    '中国医学科学院',
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

print("Loading national医保 data...", file=sys.stderr)
natl = defaultdict(dict)
with open(NATL, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        natl[row['province'].strip()][row['name'].strip()] = row

# Build normalized index: {province: {norm: [orig_names]}}
natl_idx = defaultdict(lambda: defaultdict(list))
for prov, names in natl.items():
    for name in names:
        nn = normalize(name)
        if nn:
            natl_idx[prov][nn].append(name)

zj_uscc = {}
with open(ZJ, 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        nm = row.get('定点医药机构名称', '').strip()
        uc = row.get('统一社会信用代码', '').strip()
        mt = row.get('定点医疗服务机构类型', '').strip()
        if nm and uc:
            zj_uscc[nm] = (uc, mt)

# Load a-hospital records
ahosp = []
with open(AHOSP, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        p = fix_prov(row.get('province',''))
        n = row.get('name','').strip()
        if p and n:
            ahosp.append({'prov': p, 'name': n, 'norm': normalize(n), 'row': row})

print(f"a-hospital: {len(ahosp)} records", file=sys.stderr)

fields = ['ahosp_name','ahosp_province','ahosp_city','ahosp_grade','ahosp_address',
          'natl_code','natl_name','natl_type','natl_level','natl_nature','natl_address',
          'uscc','uscc_source','medins_type']

matched = 0
unmatched = 0
uscc_found = 0
methods = {}

t0 = time.time()
with open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for i, rec in enumerate(ahosp):
        if i % 10000 == 0:
            print(f"  {i}/{len(ahosp)}...", file=sys.stderr)
        
        p, n, norm = rec['prov'], rec['name'], rec['norm']
        pn = natl.get(p, {})
        pi = natl_idx.get(p, {})
        nr = None
        
        # 1. Exact
        if n in pn:
            nr = pn[n]
            methods['exact'] = methods.get('exact',0) + 1
        # 2. Normalized match
        elif norm in pi:
            nr = pn[pi[norm][0]]
            methods['norm'] = methods.get('norm',0) + 1
        # 3. Try: ahosp name WITHOUT prefixes matches a医保 name's normalized form
        else:
            # Try stripping additional prefixes from ahosp name
            for prefix in PREFIXES:
                if n.startswith(prefix):
                    stripped = n[len(prefix):].strip()
                    if stripped in pn:
                        nr = pn[stripped]
                        methods['prefix'] = methods.get('prefix',0) + 1
                        break
        
        out = {'ahosp_name':n, 'ahosp_province':p,
            'ahosp_city':rec['row'].get('city',''), 'ahosp_grade':rec['row'].get('grade',''),
            'ahosp_address':rec['row'].get('address',''),
            'natl_code':'','natl_name':'','natl_type':'','natl_level':'','natl_nature':'','natl_address':'',
            'uscc':'','uscc_source':'','medins_type':''}
        
        if nr:
            matched += 1
            out['natl_code'] = nr.get('code','')
            out['natl_name'] = nr.get('name','')
            out['natl_type'] = nr.get('type','')
            out['natl_level'] = nr.get('level','')
            out['natl_nature'] = nr.get('nature','')
            out['natl_address'] = nr.get('address','')
            for c in [nr.get('name',''), n]:
                if c in zj_uscc:
                    out['uscc'], out['medins_type'] = zj_uscc[c]
                    out['uscc_source'] = '浙江开放平台'
                    uscc_found += 1
                    break
        else:
            unmatched += 1
        
        w.writerow(out)

t = time.time() - t0
print(f"\n=== Results ({t:.1f}s) ===")
print(f"Total: {len(ahosp)}")
print(f"Matched: {matched} ({100*matched/len(ahosp):.1f}%)")
for m, c in sorted(methods.items()):
    print(f"  {m}: {c}")
print(f"Unmatched: {unmatched} ({100*unmatched/len(ahosp):.1f}%)")
print(f"浙江 USCC found: {uscc_found}")
print(f"Output: {OUT}")
