// NEXORA workload simulation - flash-sale spike
// Sudden surge in traffic to test resilience and failover behaviour.
// Simulation evidence only, not production measurements.
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    flash_spike: {
      executor: 'ramping-vus',
      startVUs: 20,
      stages: [
        { duration: '1m', target: 20 },
        { duration: '10s', target: 400 }, // near-instant jump, like a push notification
        { duration: '3m', target: 400 },
        { duration: '2m', target: 20 },
      ],
    },
  },
  thresholds: {
    // relaxed targets: the point is to observe degradation behaviour,
    // not to pass. Record where the error rate actually crosses these.
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<2000'],
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
        'Idempotency-Key': `spike-${__VU}-${__ITER}-${Date.now()}`,
      },
    }
  );
  check(order, { 'order accepted': (r) => r.status === 200 || r.status === 201 });

  sleep(Math.random() * 3);
}
