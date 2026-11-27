// NEXORA workload simulation - normal trading baseline (k6)
// Results from this script are lab simulation evidence for the final
// assessment. They are not production measurements and must be labelled
// as simulation results in the report and slides.
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    normal_trading: {
      executor: 'constant-vus',
      vus: 20,
      duration: '10m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
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
        // idempotency key so a retry cannot double-create an order
        'Idempotency-Key': `normal-${__VU}-${__ITER}-${Date.now()}`,
      },
    }
  );
  check(order, { 'order accepted': (r) => r.status === 200 || r.status === 201 });

  sleep(1);
}
