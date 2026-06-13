import csv, re, sys, time
from collections import defaultdict

BASE = "/Users/williamsun/Downloads/documents/06_Others/Input/医疗机构数据"
NATL = f"{BASE}/national_hospitals.csv"
AHOSP = f"{BASE}/hospitals.csv"
ZJ = f"{BASE}/zj_hospital_list.csv"
SH = f"{BASE}/shanghai_all_health.csv"
OUT = f"{BASE}/final_hospitals.csv"

prov_map = {'北京':'北京市','天津':'天津市','上海':'上海市','重庆':'重庆市',
    '内蒙古':'内蒙古自治区','广西':'广西壮族自治区','西藏':'西藏自治区',
    '宁夏':'宁夏回族自治区','新疆':'新疆维吾尔自治区'}

MUNICIPALITIES = {'北京市','天津市','上海市','重庆市'}
AUTONOMOUS = {'内蒙古自治区','广西壮族自治区','西藏自治区','宁夏回族自治区','新疆维吾尔自治区'}

def fix_prov(p):
    if not p: return ''
    p = p.strip()
    if p in prov_map: return prov_map[p]
    if p.endswith('省') or p.endswith('市') or p.endswith('自治区'): return p
    for k, v in prov_map.items():
        if p.startswith(k):
            return v
    return p + '省'

DIRECT_DISTRICTS = {
    '东城区','西城区','朝阳区','海淀区','丰台区','石景山区',
    '通州区','顺义区','昌平区','大兴区','怀柔区','平谷区',
    '延庆区','密云区','门头沟区','房山区','崇文区','宣武区',
    '和平区','河东区','河西区','南开区','河北区','红桥区','东丽区','西青区','津南区','北辰区',
    '武清区','宝坻区','滨海新区','宁河区','静海区','蓟州区',
    '黄浦区','徐汇区','长宁区','静安区','普陀区','虹口区','杨浦区','闵行区','宝山区',
    '嘉定区','浦东新区','金山区','松江区','青浦区','奉贤区','崇明区','南汇区','卢湾区','闸北区',
    '万州区','涪陵区','渝中区','大渡口区','江北区','沙坪坝区','九龙坡区','南岸区','北碚区',
    '綦江区','大足区','渝北区','巴南区','黔江区','长寿区','江津区','合川区','永川区','南川区',
    '璧山区','铜梁区','潼南区','荣昌区','开州区','梁平区','武隆区',
}

PREFIXES = [
    '上海交通大学医学院附属','上海交通大学附属','上海中医药大学附属',
    '复旦大学附属','同济大学附属',
    '海军军医大学第一附属','海军军医大学第二附属','海军军医大学第三附属','海军军医大学附属',
    '第二军医大学第一附属','第二军医大学第二附属','第二军医大学第三附属','第二军医大学附属',
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
    s = re.sub(r'^[\u4e00-\u9fff]{2,10}(?:大学|医学院)(?:第[一二三四五六七八九十]+)?附属', '', s)
    for p in sorted(PREFIXES, key=len, reverse=True):
        if s.startswith(p):
            s = s[len(p):]
            break
    s = re.sub(r'^(上海市|北京市|天津市|重庆市)', '', s)
    s = re.sub(r'^(上海|北京|天津|重庆)', '', s)
    return s.strip()

def normalize_loose(s):
    if not s: return ''
    s = normalize(s)
    s = re.sub(r'[（(][^）)]*[）)]', '', s)
    s = re.sub(r'[\s\u3000]', '', s)
    s = s.replace('（','').replace('）','').replace('(', '').replace(')', '')
    s = s.replace('医院', '').replace('中心', '').replace('卫生院', '')
    s = s.replace('卫生室', '').replace('诊所', '').replace('门诊部', '')
    s = s.replace('院', '')
    return s

ABBREV_CITIES = {
    '呼市': '呼和浩特市', '呼和浩市': '呼和浩特市',
    '乌市': '乌鲁木齐市', '乌鲁齐市': '乌鲁木齐市',
}

def parse_address(addr, fallback_province='', district_city_map=None):
    if not addr: return ('', '', '', '')
    orig_addr = addr
    prov, city, district = '', '', ''
    detail = addr

    for pv in sorted(AUTONOMOUS | MUNICIPALITIES, key=len, reverse=True):
        if addr.startswith(pv):
            prov = pv
            detail = addr[len(pv):]
            break
    if not prov:
        m = re.match(r'(.+?省)', addr)
        if m:
            prov = m.group(1)
            detail = addr[len(prov):]

    if not prov and fallback_province:
        prov = fallback_province
        detail = addr

    if not prov:
        return ('', '', '', addr)

    detail = re.sub(r'^[；;，,、\s\u3000]+', '', detail)

    if prov in MUNICIPALITIES:
        city = prov
        for d in sorted(DIRECT_DISTRICTS, key=len, reverse=True):
            if detail.startswith(d):
                district = d
                detail = detail[len(d):]
                break
        detail = re.sub(r'^[；;，,、\s\u3000]+', '', detail)
        return (prov, city, district, detail)

    # Check for abbreviated city names
    for abbr, full in ABBREV_CITIES.items():
        if detail.startswith(abbr):
            city = full
            detail = detail[len(abbr):]
            detail = re.sub(r'^[；;，,、\s\u3000]+', '', detail)
            break

    if not city:
        m = re.match(r'([\u4e00-\u9fff]{2,6}市)', detail)
        if m:
            c = m.group(1)
            detail = detail[len(c):]
            detail = re.sub(r'^[；;，,、\s\u3000]+', '', detail)
            city = c

    if detail:
        m = re.match(r'([\u4e00-\u9fff]{2,6}[区旗县])', detail)
        if m:
            district = m.group(1)
            detail = detail[len(district):]

    # If still no city but district is found, try to look up from district_city_map
    if not city and district and district_city_map and prov:
        candidates = district_city_map.get(prov, {}).get(district, [])
        if len(candidates) == 1:
            city = list(candidates)[0]

    detail = re.sub(r'^[；;，,、\s\u3000]+', '', detail).strip('；;，,、 ')
    return (prov, city if city else '', district, detail if detail else '')


def build_district_city_map(natl_rows):
    dcm = defaultdict(lambda: defaultdict(set))
    MUNI = MUNICIPALITIES
    AUTO = AUTONOMOUS

    for r in natl_rows:
        p = r['province'].strip()
        a = r['address'].strip()
        if not a or not p: continue

        prov, detail = '', a
        for pv in sorted(AUTO | MUNI, key=len, reverse=True):
            if a.startswith(pv):
                prov = pv; detail = a[len(pv):]; break
        if not prov:
            m = re.match(r'(.+?省)', a)
            if m: prov = m.group(1); detail = a[len(prov):]
        if not prov: continue

        detail = re.sub(r'^[；;，,、\s\u3000]+', '', detail)

        if prov in MUNI:
            continue  # municipalities handled separately

        m = re.match(r'([\u4e00-\u9fff]{2,6}市)', detail)
        if not m: continue
        city = m.group(1)
        detail = detail[len(city):]
        detail = re.sub(r'^[；;，,、\s\u3000]+', '', detail)

        m2 = re.match(r'([\u4e00-\u9fff]{2,6}[区旗县])', detail)
        if m2:
            dcm[prov][m2.group(1)].add(city)

    # Simplify: for each (province, district), if only 1 city, store it
    result = {}
    for prov, districts in dcm.items():
        result[prov] = {}
        for dist, cities in districts.items():
            if len(cities) == 1:
                result[prov][dist] = list(cities)
    return result


t0 = time.time()

natl_rows = []
with open(NATL, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        natl_rows.append(row)
natl_n = len(natl_rows)

district_city_map = build_district_city_map(natl_rows)
print(f"Built district→city map: {sum(len(v) for v in district_city_map.values())} mappings across {len(district_city_map)} provinces", file=sys.stderr)

zj_uscc = {}
with open(ZJ, 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        nm = row.get('定点医药机构名称', '').strip()
        uc = row.get('统一社会信用代码', '').strip()
        mt = row.get('定点医疗服务机构类型', '').strip()
        if nm and uc:
            zj_uscc[nm] = (uc, mt)

sh_uscc = {}
with open(SH, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        nm = row.get('name','').strip()
        uc = row.get('code','').strip()
        if nm and uc:
            sh_uscc[nm] = uc

ahosp_idx = defaultdict(list)
ahosp_loose_idx = defaultdict(list)
with open(AHOSP, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        p = fix_prov(row.get('province',''))
        n = row.get('name','').strip()
        if p and n:
            ahosp_idx[(p, n)].append(row)
            ahosp_idx[(p, normalize(n))].append(row)
            ahosp_loose_idx[(p, normalize_loose(n))].append(row)

print(f"Loaded: {natl_n} natl, {len(zj_uscc)} ZJ, {len(sh_uscc)} SH, {time.time()-t0:.0f}s", file=sys.stderr)

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
print(f"  ZJ norm match +{zj_new} ({time.time()-t0:.0f}s)", file=sys.stderr)

fields = ['h_code','province','name','type','level','nature','address',
          'province_parsed','city_parsed','district_parsed',
          'ahosp_name','ahosp_grade','ahosp_city',
          'uscc','uscc_source']

uscc_total = 0
ahosp_total = 0
ahosp_loose_total = 0
nature_filled = 0
dedup_removed = 0

INFERRED_NATURE = {
    '村卫生室':'非盈利性','卫生所（室）':'非盈利性','乡卫生院':'非盈利性',
    '普通诊所':'盈利','口腔诊所':'盈利','口腔门诊部':'盈利',
    '中医诊所':'盈利','中心卫生院':'非盈利性','社区卫生服务中心':'非盈利性',
    '中西医结合诊所':'盈利','中医门诊部':'盈利','妇幼保健院':'非盈利性',
    '眼科医院':'盈利','其他诊所':'盈利','专科门诊部':'盈利',
    '中西医结合门诊部':'盈利','普通专科门诊部':'盈利','中医（综合）门诊部':'盈利',
    '疾病预防控制中心':'非盈利性','民族医诊所':'盈利','妇幼保健所':'非盈利性',
    '传染病医院':'非盈利性','结核病防治所（站、中心）':'非盈利性',
    '眼科门诊部':'盈利','皮肤病防治所（站、中心）':'非盈利性',
    '其他中医专科医院':'盈利','护理站':'盈利','妇幼保健站':'非盈利性',
    '急救中心':'非盈利性','中心血站':'非盈利性','民族医门诊部':'盈利',
    '中小学卫生保健所':'非盈利性','胸科医院':'非盈利性','结核病医院':'非盈利性',
    '结核病防治院':'非盈利性','职业病防治院':'非盈利性','传染病防治院':'非盈利性',
    '预防保健中心':'非盈利性','急救站':'非盈利性','卫生监督所（局）':'盈利',
    '临床检验所（站）':'盈利','计划生育技术服务中心（站）':'非盈利性',
    '卫生人才交流中心':'非盈利性','针炙医院':'盈利','精神病收容所':'盈利',
    '麻风病医院':'非盈利性','生殖保健中心':'非盈利性','卫生防病中心':'非盈利性',
    '乡防保组':'非盈利性','医疗美容门诊部':'盈利','麻风病防治所（站、中心）':'非盈利性',
    '民族医（药）学研究所':'盈利','预防医学研究院（所）':'非盈利性',
    '护理院（站）':'盈利','健康教育所':'盈利','中医医院':'盈利',
    '医师协会':'盈利','药物戒毒所（中心）':'非盈利性','傣医院':'非盈利性',
}

def infer_nature(nature_val, type_val):
    if nature_val.strip():
        return nature_val.strip()
    return INFERRED_NATURE.get(type_val, '')

def clean_grade(g):
    if not g: return ''
    g = re.sub(r'<[^>]+>', '', g)
    g = re.sub(r'\*\*.*', '', g)
    g = re.sub(r'&nbsp;|\s', '', g)
    return g.strip()

# Dedup: same province + name + type + address_prefix(30 chars)
dup_groups = defaultdict(list)
for i, row in enumerate(natl_rows):
    key = (row['province'].strip(), row['name'].strip(), row['type'].strip(), row.get('address','').strip()[:30])
    dup_groups[key].append(i)

keep = set(range(natl_n))
alt_codes = {}
for key, idxs in dup_groups.items():
    if len(idxs) < 2: continue
    scored = []
    for idx in idxs:
        r = natl_rows[idx]
        score = 0
        if r.get('nature','').strip(): score += 1
        if r.get('level','').strip() and r['level'].strip() != '未定级': score += 2
        if r.get('address','').strip(): score += 1
        scored.append((score, idx))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][1]
    alts = [natl_rows[idx]['code'] for _, idx in scored[1:]]
    if alts:
        alt_codes[best] = alts
    for _, idx in scored[1:]:
        keep.discard(idx)
dedup_removed = natl_n - len(keep)
print(f"Dedup: {dedup_removed} duplicate records removed, {len(alt_codes)} groups merged", file=sys.stderr)

fields = ['h_code','province','name','type','level','nature','address',
          'province_parsed','city_parsed','district_parsed',
          'ahosp_name','ahosp_grade','ahosp_city',
          'uscc','uscc_source','h_code_alt']

with open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for i, row in enumerate(natl_rows):
        if i not in keep: continue
        if i % 100000 == 0 and i > 0:
            print(f"  {i}/{natl_n}...", file=sys.stderr)
        p, n = row['province'].strip(), row['name'].strip()
        uc_val, uc_src = '', ''
        if n in zj_uscc:
            uc_val = zj_uscc[n][0]
            uc_src = '浙江'
        elif n in sh_uscc:
            uc_val = sh_uscc[n]
            uc_src = '上海'
        if uc_val:
            uscc_total += 1

        ah = (ahosp_idx.get((p, n)) or ahosp_idx.get((p, normalize(n))) or [None])[0]
        if ah:
            ahosp_total += 1
        else:
            loose_matches = ahosp_loose_idx.get((p, normalize_loose(n)), [])
            if loose_matches:
                ah = loose_matches[0]
                ahosp_loose_total += 1

        grade = clean_grade(ah.get('grade','')) if ah else ''

        addr = row.get('address','')
        pp, cp, dp, _ = parse_address(addr, fallback_province=p, district_city_map=district_city_map)

        nat = infer_nature(row.get('nature',''), row.get('type',''))
        if not row.get('nature','').strip() and nat:
            nature_filled += 1
        w.writerow({
            'h_code': row['code'], 'province': p, 'name': n,
            'type': row.get('type',''), 'level': row.get('level',''),
            'nature': nat, 'address': addr,
            'province_parsed': pp, 'city_parsed': cp, 'district_parsed': dp,
            'ahosp_name': ah.get('name','') if ah else '',
            'ahosp_grade': grade,
            'ahosp_city': ah.get('city','') if ah else '',
            'uscc': uc_val, 'uscc_source': uc_src,
            'h_code_alt': ';'.join(alt_codes.get(i, [])),
        })

zj_c = sum(1 for r in natl_rows if r['name'].strip() in zj_uscc)
sh_c = sum(1 for r in natl_rows if r['name'].strip() in sh_uscc)

print(f"\nFinal:", file=sys.stderr)
print(f"Total: {natl_n}", file=sys.stderr)
print(f"USCC: {uscc_total} ({100*uscc_total/natl_n:.1f}%)  ZJ:{zj_c} SH:{sh_c}", file=sys.stderr)
print(f"a-hospital exact: {ahosp_total} ({100*ahosp_total/natl_n:.1f}%)", file=sys.stderr)
print(f"a-hospital loose: {ahosp_loose_total}", file=sys.stderr)
print(f"Nature filled by inference: {nature_filled}", file=sys.stderr)
print(f"Time: {time.time()-t0:.0f}s", file=sys.stderr)
