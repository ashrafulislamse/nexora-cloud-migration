// NEXORA workload simulation - campaign peak (11.11 / Black Friday ramp)
// Gradually increasing load to test whether autoscaling keeps up with a
// seasonal campaign. Simulation evidence only, not production measurements.
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    campaign_ramp: {
      executor: 'ramping-vus',
      startVUs: 20,
      stages: [
        { duration: '2m', target: 60 },
        { duration: '3m', target: 120 },
        { duration: '5m', target: 200 },
        { duration: '3m', target: 200 },
        { duration: '2m', target: 20 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<800', 'p(99)<1500'],
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const catalogue = http.get(`${BASE}/api/catalogue?page=1`);
  check(catalogue, { 'catalogue 200': (r) => r.status === 200 });

  const sku = `SKU-${Math.ceil(Math.random() * 500)}`;
  const product = http.get(`${BASE}/api/products/${sku}`);
  check(product, { 'product 200': (r) => r.status === 200 });

  const order = http.post(
    `${BASE}/api/orders`,
    JSON.stringify({ sku: sku, qty: 1 }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': `peak-${__VU}-${__ITER}-${Date.now()}`,
      },
    }
  );
  check(order, { 'order accepted': (r) => r.status === 200 || r.status === 201 });

  sleep(Math.random() * 2);
}
