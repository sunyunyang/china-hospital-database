# 全国医院数据项目

## 最终数据集

**`final_hospitals.csv`** — **514,215 条** (2026-06-13, v6)

| 字段 | 说明 |
|---|---|
| h_code | 国家医保代码（H 前缀） |
| province | 省份 |
| name | 机构正式名称 |
| type | 机构类型（综合医院/村卫生室/诊所...） |
| level | 等级（三级甲等/二级/未定级...） |
| nature | 盈利性质（非盈利性/盈利） |
| address | 完整地址 |
| province_parsed | 地址解析：省 |
| city_parsed | 地址解析：市 |
| district_parsed | 地址解析：区/县 |
| ahosp_name | a-hospital.com 补充名称 |
| ahosp_grade | a-hospital.com 等级 |
| ahosp_city | a-hospital.com 城市 |
| uscc | 统一社会信用代码（1.7% 覆盖率） |
| uscc_source | USCC 来源（浙江/上海） |
| h_code_alt | 去重合并的备用 h_code |

## 数据源

| 数据源 | 方法 | 记录数 |
|---|---|---|
| 国家医保 API (fuwu.nhsa.gov.cn) | SM2/SM4 解密 + 批量爬取 | 514,849 |
| 浙江开放平台 (data.zjzwfw.gov.cn) | 匿名下载，含 USCC | 26,551 (9,931 医疗机构) |
| 信用上海 | API 批量查询 | 432 实体 (含 USCC) |
| a-hospital.com | 爬取医院名称/等级 | 30,556 |

## 数据优化历程

| 优化项 | 优化前 | 优化后 |
|---|---|---|
| 地址解析-省 | 11.6% | 100% |
| 地址解析-市 | 10.6% | 72.2% |
| 地址解析-区/县 | 10.4% | 64.3% |
| nature 空值 | 34.3% | 4.2% |
| a-hospital 匹配 | 6,021 | 6,242 |
| USCC 总量 | 8,784 (1.7%) | 8,996 (1.7%) |
| 去重合并 | — | 634 条合并 |
| 当前版本 | v3 | **v6** (build_final_v6.py) |

## USCC 覆盖率瓶颈

USCC 仅 1.7% (8,996/514,215)：
- 浙江 8,970 (79.6% of 浙江数据)
- 上海 46 (1.5%)
- 其他省 0

**可行途径**：商业采购（无码科技 110 万机构含 USCC，或企查查 API 按次查询）

## 构建脚本

- `build_final_v6.py` — 当前版本（含地址解析、nature 推断、去重、a-hospital 匹配）
- 最新脚本位于 `~/Downloads/documents/06_Others/Input/医疗机构数据/`

## 已知局限

- 90.3% 记录等级为"未定级"
- 村卫生室占 48%，综合医院仅 3.4%
- 无码科技等商业数据源尚未询价
