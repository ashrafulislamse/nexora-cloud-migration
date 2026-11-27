import http from 'k6/http';
import { check } from 'k6';

export const options = { vus: 2, duration: '5s' };

export default function () {
  check(http.get(`${__ENV.BASE_URL}/api/catalogue?page=1`), { 'catalogue ok': (r) => r.status === 200 });
  check(http.post(`${__ENV.BASE_URL}/api/orders`, JSON.stringify({ sku: 'SKU-1', qty: 1 }), { headers: { 'Content-Type': 'application/json' } }), { 'order ok': (r) => r.status === 201 });
}
