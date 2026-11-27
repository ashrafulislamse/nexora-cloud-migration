# NEXORA Infrastructure-as-Code and Simulation Package

BIT4043 Cloud Architecturing — Final Assessment (40%), group submission.
Prepared by the NEXORA team: Islam, Ashraf, Mahmud, Atif.

## What this package is

A Terraform prototype plus k6 workload profiles for the NEXORA
omnichannel migration described in the presentation deck (Figure 2,
To-Be architecture). It is **supplied as source code for review — it has
not been applied to an AWS account, and no `terraform plan/apply` output
is included.** All traffic, latency and cost figures in the deck come
from the modelled assumptions documented in `tco-analysis.md` and the
deck's assumptions slide, not from executed infrastructure.

## Layout

```
main.tf                  Root wiring: providers for both regions and the
                         module calls (networking, security, compute,
                         data, monitoring for primary and recovery).
variables.tf             Region, CIDR, image, port and scaling inputs.
outputs.tf               ALB DNS names and Aurora endpoints.
modules/networking/      VPC, public/private subnets, IGW, NAT, routes.
modules/security/        Security groups (ALB 80/443 -> app_port) and
                         ECS execution/task IAM roles.
modules/compute/         ALB, target group, ECS Fargate service,
                         CloudWatch log group, target-tracking CPU policy.
modules/data/            Aurora MySQL Global Database: primary writer
                         cluster (2 Serverless v2 instances) plus a
                         secondary cluster in the recovery region attached
                         to the same global cluster.
modules/monitoring/      SNS topic and high-CPU alarm per environment.
normal-load.js           k6 profile: 20 VUs constant, 10 minutes.
peak-load.js             k6 profile: ramp to 200 VUs (campaign night).
spike-load.js            k6 profile: sudden ramp to 400 VUs.
tco-analysis.md          Three-year TCO model and all assumptions.
```

## Region design (matches the deck)

- Primary: `ap-southeast-5` (Malaysia). Storefront runs active; the
  Aurora writer lives here.
- Recovery: `ap-southeast-3` (Jakarta). Warm-standby Fargate service
  (1-4 tasks) and a secondary Aurora cluster receiving asynchronous
  replication. Failover = promote the secondary, repoint Route 53.

This is a single-writer design. The recovery region is not
active-active for transactional writes; Aurora Global Database
replicates asynchronously (typically under 1 second, unmeasured here),
so the deck's 1-minute RPO is a monitored design target.

## Placeholder application

`variables.tf` defaults to the public nginx:alpine image. The compute
module injects a startup command that makes it serve:

- `GET /health` -> 200 "ok" (target-group health check)
- `GET /api/catalogue`, `GET /api/products/{sku}`, `POST /api/orders`
  -> 200 JSON stubs matching the k6 profiles

This is a stub so the load profiles have endpoints to hit. It is not
the NEXORA storefront application; replace `app_image` and remove the
injected command when the real service exists.

## Known prototype gaps (stated honestly)

- No Terraform state backend configured (local state).
- No ACM certificate, Route 53 zone or CloudFront distribution; TLS is
  expected to terminate at CloudFront in the target design, and the ALB
  listener is plain HTTP on 80 pending that wiring.
- The recovery region does not yet get a CloudFront/S3 static-asset
  stack; only compute, data, network, security and monitoring.
- Security groups allow 0.0.0.0/0 on the ALB; production would restrict
  to the CloudFront managed prefix list.
- The k6 profiles assume endpoints the stub serves; they measure the
  stub, not the real application.

## Running it (if the team chooses to)

```
terraform init
terraform validate
terraform plan -var="alarm_email=you@example.com"
```

The plan provisions in both regions; expect Aurora Global Database and
Fargate charges while applied. Destroy promptly: `terraform destroy`.

## Load testing (if executed)

```
k6 run -e BASE_URL=http://<alb-dns> normal-load.js
k6 run -e BASE_URL=http://<alb-dns> peak-load.js
k6 run -e BASE_URL=http://<alb-dns> spike-load.js
```

Record p95/p99, throughput and error rate from the k6 summary output
before quoting any performance number in the report.
