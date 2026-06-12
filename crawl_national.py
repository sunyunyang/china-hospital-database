import execjs, requests, json, os, time, csv, sys
from urllib3 import disable_warnings
disable_warnings()

BASE = '/var/folders/2q/dqxl1s592zq_3jb1w0dd_2sc0000gn/T/opencode'
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HOSP_URL = "https://fuwu.nhsa.gov.cn/ebus/fuwu/api/nthl/api/fixed/queryFixedHospital"
REG_URL = "https://fuwu.nhsa.gov.cn/ebus/fuwu/api/nthl/api/dic/queryAdmdvsTree"
PAGE_SIZE = 1000
OUTPUT = os.path.join(BASE, 'national_hospitals.csv')

os.chdir(BASE)
print("Compiling JS...", flush=True)
with open('fuwu_nhsa.js', 'r', encoding='utf-8') as f:
    nhsa_js = execjs.compile(f.read())

def get_headers():
    h = nhsa_js.call("getHeaders")
    h["User-Agent"] = UA
    h["Content-Type"] = "application/json"
    for k, v in {"Host": "fuwu.nhsa.gov.cn", "Origin": "https://fuwu.nhsa.gov.cn", "Referer": "https://fuwu.nhsa.gov.cn/nationalHallSt/"}.items():
        h[k] = v
    return h

def query_page(regn_code, page):
    payload = {"addr":"","medinsLvCode":"","medinsName":"","medinsTypeCode":"","pageNum":page,"pageSize":PAGE_SIZE,"regnCode":regn_code,"sprtEcFlag":""}
    for attempt in range(3):
        try:
            encrypted = nhsa_js.call("getEncryptedData", payload)
            resp = requests.post(HOSP_URL, json=encrypted, headers=get_headers(), timeout=60, verify=False)
            return nhsa_js.call("getDecryptedData", resp.json())
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  Retry {attempt+1} for {regn_code} page {page}: {type(e).__name__}", flush=True)
            time.sleep(3)
    return None

def main():
    print("Fetching province list...", flush=True)
    payload = {"data": {"transferFlag": ""}}
    resp = requests.post(REG_URL, json=payload, headers=get_headers(), timeout=30, verify=False)
    provinces = resp.json()['data']
    
    # Filter only province-level codes (ending with 0000), excluding non-mainland
    valid = [p for p in provinces if p['code'].endswith('0000') 
             and p['code'] not in ('710000','810000','820000','910000','920000')]
    
    fields = ['code', 'province', 'name', 'type', 'level', 'nature', 'address']
    total_written = 0
    
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
    
    for prov in valid:
        code = prov['code']
        name = prov['name']
        print(f"\n--- {name} ({code}) ---", flush=True)
        
        try:
            first = query_page(code, 1)
            total = first.get('total', 0)
            pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
            print(f"  Total: {total:,}, Pages: {pages}", flush=True)
            
            count = 0
            all_items = first.get('list', [])
            
            for page in range(2, pages + 1):
                data = query_page(code, page)
                if data and 'list' in data:
                    all_items.extend(data['list'])
                if page % 5 == 0:
                    print(f"  Page {page}/{pages} ({len(all_items)} items so far)", flush=True)
            
            # Write batch
            with open(OUTPUT, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for item in all_items:
                    writer.writerow([
                        item.get('medinsCode', ''),
                        name,
                        item.get('medinsName', ''),
                        item.get('medinsTypeName', ''),
                        item.get('medinsLvName', ''),
                        item.get('medinsNatuName', ''),
                        item.get('addr', ''),
                    ])
            
            total_written += len(all_items)
            print(f"  Done: {len(all_items)} written ({total_written:,} total)", flush=True)
            
        except Exception as e:
            print(f"  ERROR for {name}: {type(e).__name__}: {str(e)[:100]}", flush=True)
            continue
    
    print(f"\n{'='*50}")
    print(f"COMPLETE: {total_written:,} records written to {OUTPUT}")

if __name__ == '__main__':
    main()
