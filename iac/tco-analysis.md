# NEXORA 3-Year TCO and FinOps Analysis

**Date compiled:** 24 Nov 2026
**Status:** working model owned by the team. Every figure is a model estimate built from public list prices, not from a billing account. The model produces its own savings number; no savings percentage is claimed in advance.
**Currency:** USD. Salary inputs converted at RM 4.70 = USD 1 (assumption, [TEAM] verify).

This file answers rubric item "Three-year TCO and FinOps" and feeds slide 16 of the executive deck and page 2 of the executive visual summary.

---

## 1. Honesty rules (apply to every table below)

1. Verified prices carry a source and retrieval date. Everything else is labelled **assumption** and listed in section 9 for the team to verify.
2. Fargate has no Malaysia rates in the AWS Price List bulk API. The model uses US East list prices plus a documented ~10% regional uplift, consistent with the observed uplift on NAT (+11.4%), ALB (+0.9%) and Aurora r7g.large (~+9%) in ap-southeast-5.
3. Results are steady-state estimates. They are not measured from a real deployment and must never be presented as such.
4. All component costs reconcile to the stated totals. Rounding is applied only at line level.

## 2. Workload sizing assumptions

| Assumption | Value | Basis |
|---|---|---|
| Stores / distribution centres | 120 stores, 3 DCs | enterprise profile (SPEC.md) |
| Orders, baseline | 2,000/day across all channels | assumption, mid-size regional retailer |
| Campaign peak | 20,000/day for ~10 days/month (10x) | matches R5 in SPEC.md |
| Storefront requests | 2M/day baseline, 20M/day campaign | ~23 req/s baseline, ~230 req/s campaign average |
| Catalogue and media | 50,000 SKUs, 2 TB images in S3, growing ~500 GB/year | assumption |
| Aurora storage | 300 GB now, ~800 GB by year 3, 550 GB average | assumption |
| Aurora I/O volume | ~40M I/O per month (orders + POS sync + reporting reads) | assumption |
| Egress to internet | ~2 TB/month via CloudFront + ~80 GB direct (payment/API) | assumption |
| App tasks (Fargate) | floor 2 tasks 24/7, evening +4 tasks x 12h, campaign 14 tasks x 14h, staging 1 task x 220 h/month | derived from request rates at ~80 req/s per task |
| Peak capacity check | 14 tasks x 80 req/s = 1,120 req/s vs ~460 req/s campaign peak | headroom ~2.4x, consistent with autoscaling target |

## 3. Verified unit prices (AWS Price List bulk API, ap-southeast-5, retrieved 24 Nov 2026)

| Item | Rate | Source |
|---|---|---|
| Aurora PostgreSQL db.r7g.large (standard storage model) | $0.283/hr per instance | bulk API 2026-11-01 (verified) |
| Aurora db.r7g.large, I/O-Optimized | $0.368/hr per instance | bulk API (verified) |
| Aurora storage, standard | $0.099/GB-month | bulk API (verified) |
| Aurora I/O | $0.198 per 1M requests | bulk API (verified) |
| Aurora backup storage | $0.021/GB-month | bulk API (verified) |
| ALB | $0.0227/hr + $0.008/LCU-hr | bulk API (verified) |
| NAT Gateway | $0.05015/hr + $0.05015/GB processed | bulk API (verified) |
| S3 Standard storage (first 50 TB) | $0.0225/GB-month | bulk API (verified) |
| S3 Standard-IA | $0.01242/GB-month | bulk API (verified) |
| S3 Glacier Instant Retrieval | $0.0045/GB-month | bulk API (verified) |
| S3 PUT (Tier 1) | $0.0045 per 1,000 requests | bulk API (verified) |
| S3 GET (Tier 2) | $0.00036 per 1,000 requests | bulk API (verified) |
| S3 IA transition request | $0.01 per 1,000 requests | bulk API (verified) |
| Internet egress (first 10 TB) | $0.108/GB | AWSDataTransfer bulk API (verified) |
| Inter-region transfer, Malaysia to Jakarta or Singapore | $0.08/GB | AWSDataTransfer bulk API (verified) |
| Fargate vCPU (Graviton, US East list) | $0.03238/hr; +10% uplift = $0.0356/hr | US East page, uplift assumption |
| Fargate memory (US East list) | $0.00356/GB-hr; +10% uplift = $0.003916/hr | US East page, uplift assumption |
| Aurora secondary (Jakarta) | priced at Malaysia rate | assumption, Jakarta parity pending [TEAM] verify |

Pricing basis for Aurora: the model uses the provisioned db.r7g.large rate because Aurora instance rates are engine-independent (MySQL and PostgreSQL cost the same per instance class). The Terraform data module expresses the same capacity as Aurora MySQL Serverless v2 (0.5-16 ACU); the fixed provisioned line is the steady-state basis for a 24/7 writer + reader, and right-sizing the cluster after 90 days of CloudWatch data is FinOps lever 3 in section 7.

## 4. Model A: on-premises, 3-year total cost of ownership

| Cost line | Monthly | Basis |
|---|---|---|
| Server amortization | $1,719 | 7 servers x $7,500 = $52,500 + SAN $20,000 + network gear $10,000, straight-line over 48 months |
| Hardware maintenance contracts | $550 | 8%/year of $82,500 hardware value |
| Power and cooling | $360 | 3.5 kW average load, $0.10/kWh, x1.4 cooling overhead |
| Data centre facilities | $600 | rack space, cabling, physical security (assumption) |
| Internet bandwidth | $350 | 2 TB/month committed (assumption) |
| Backup and offsite DR (tape rotation) | $400 | manual DR per As-Is audit (assumption) |
| Server licensing | $180 | Windows + database licences (assumption) |
| IT operations staff, 1.5 FTE | $2,400 | ~RM 7,500/month per FTE, manual deploy, patch, tape, DR drills |
| **Model A monthly total** | **$6,559** | |
| **Model A 3-year total** | **$236,124** | 36 months, no growth allowance |

Notes: amortization already treats the hardware as if replaced at time zero, which is generous to Model A. If the existing fleet is at end of life today, Model A would carry the full $82,500 as upfront capex instead.

## 5. Model B: cloud (Malaysia primary + Jakarta warm standby), monthly run rate

| Component | Monthly | Calculation |
|---|---|---|
| Fargate compute + memory | $222 | 4,860 task-h/month x ($0.0356 + 2 x $0.003916) + staging ~$11 |
| Aurora (writer + reader) | $413 | 2 x 730 x $0.283 |
| Aurora storage | $54 | 550 GB x $0.099 |
| Aurora I/O | $8 | 40M x $0.198/1M |
| Aurora backup storage | $15 | 700 GB x $0.021 |
| ALB | $52 | $0.0227 x 730 + 6 LCU x 730 x $0.008 |
| NAT Gateway (2 AZs) | $77 | 2 x 730 x $0.05015 + 80 GB x $0.05015 |
| S3 (blended lifecycle) | $98 | 1,200 GB std + 800 GB IA + 500 GB GIR + PUT/GET/transition requests |
| CloudFront (egress + HTTPS requests) | $244 | 2 TB x $0.11 + 20M req x $0.012/10k (**assumption**, APAC tier) |
| Direct internet egress (payment/API) | $9 | 80 GB x $0.108 |
| Jakarta warm standby: Aurora secondary | $207 | 730 x $0.283 (Jakarta parity assumption) |
| Jakarta warm standby: Fargate floor | $63 | 2 x 730 x $0.043432 |
| Jakarta: S3 cross-region replica | $65 | 2.5 TB x ~$0.025 + 30 GB x $0.08 CRR transfer |
| WAF + Secrets Manager + GuardDuty | $40 | 1 web ACL + 4 rules + 20M req; 10 secrets; ~$15 sampling |
| CloudWatch (logs, metrics, dashboards) | $26 | 30 GB ingestion x $0.50 + storage + dashboards |
| AWS Developer support plan | $29 | list price; Business plan during migration window |
| **Infrastructure total** | **$1,622** | |
| Platform operations, 0.5 FTE | $850 | cloud skills premium ~RM 8,000/month; automation reduces headcount share |
| **Model B monthly total** | **$2,472** | |

Observed cost structure: Aurora is ~30% of infrastructure cost, DR replication ~21%, storage/egress ~21%, compute ~14%. This shape is normal for a transactional retail workload and gives the FinOps levers in section 7 a clear target.

## 6. 3-year comparison, break-even and sensitivity

Growth: traffic +20%/year, cloud cost lines scale at ~+12%/year (autoscaling is sublinear). On-premises is capacity-fixed until a refresh, which falls outside the 3-year window.

| Measure | Value |
|---|---|
| Model A, 3-year total | $236,124 |
| Model B run-rate, year 1 ($2,472 x 12) | $29,664 |
| Model B run-rate, year 2 (+12%) | $33,224 |
| Model B run-rate, year 3 (+12%) | $37,211 |
| One-time migration project (assessment, IaC, DMS, testing, training) | $14,000 (assumption) |
| Dual-running, 2 months at Model B rate | $4,944 |
| **Model B, 3-year total incl. migration** | **$119,043** |
| **3-year saving vs Model A** | **$117,081 (~50%)** |
| Net steady-state monthly saving | $4,087 |
| Break-even | month 5 after go-live; ~month 11 counting the 6-month migration programme |

Sensitivity checks (each applied to the base case):

| Scenario | Effect | 3-year saving |
|---|---|---|
| Traffic doubles for the whole window | Model B +~$460/month growing; Model A needs +$28,000 hardware in year 2 | ~$126,500 (~48%) |
| Aurora I/O-Optimized instead of standard | +$192/month (writer+reader $537 vs $413, storage $123 vs $54) | ~$110,200 (~47%) |
| FinOps lever scenario (section 7) applied | -$163/month from month 1 | ~$123,000 (~52%) |

Interpretation for the panel: the saving is driven less by compute price and more by removing fixed facilities, licensing, manual DR and 1.0 FTE of operations capacity that the platform redeploys rather than deletes. If traffic doubles, absolute savings grow even though the percentage shrinks, because on-premises must buy hardware while the cloud autoscales.

## 7. FinOps levers (ranked by modelled impact)

| Lever | Modelled effect | Note |
|---|---|---|
| 1-year Reserved Instances / Aurora reserve on writer + reader | about -$128/month | ~31% Aurora discount, list price |
| Compute Savings Plan on the 24/7 floor + staging | about -$35/month | commit floor usage only |
| Right-size Aurora after 90 days of CloudWatch data | up to -$206/month if db.r7g.medium suffices | gated by R5 acceptance criteria, not assumed |
| S3 lifecycle tiering (IA + Glacier IR) | already in base model ($98 vs $107 all-standard) | keep policy reviewed quarterly |
| VPC gateway endpoints for S3/DynamoDB (free) + interface endpoints | avoids NAT processing on bulk traffic | interface endpoint cost ~$29/month traded against NAT data |
| Graviton (ARM) Fargate tasks | already in base model, ~21% cheaper than x86 | validated by k6 simulation before cutover |
| Spot for batch reporting/analytics | ~65% off interruptible tasks | applies to Athena-prep and reconciliation jobs |
| AWS Budgets alerts + Cost Anomaly Detection + mandatory cost-allocation tags | governance, not savings | monthly cost review is a runbook item |

## 8. What the deck and one-pager should claim

1. Cloud 3-year TCO ≈ $119k vs on-premises ≈ $236k, a modelled saving of ≈ $117k (~50%), break-even month 5 after go-live.
2. State plainly: estimates from list prices, not billing data; Fargate carries a ~10% regional uplift assumption; CloudFront and Jakarta rates pending team verification.
3. Show the sensitivity rows when asked "what if traffic doubles", it is the most likely panel question.

## 9. Open items for the team [TEAM]

1. Cross-check the five largest lines (Aurora, compute, CloudFront, DR, NAT) in the AWS Pricing Calculator and record the comparison.
2. Verify Jakarta Aurora parity and CloudFront APAC rates ($0.11/GB, $0.012/10k HTTPS) against public pages.
3. Confirm salary inputs (RM 7,500 / RM 8,000 per FTE-month) and the RM/USD rate used.
4. Decide the Aurora standard vs I/O-Optimized position for the deck (this model keeps standard and explains when to switch).
5. If a real AWS account is used for the prototype, reconcile a one-month bill against section 5 and label the delta.
