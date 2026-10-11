// Run requests through the Worker locally in Node (no wrangler, no network):
//   node mock/try.mjs GET /ping
//   node mock/try.mjs GET '/accounts/C001?x=1'
//   node mock/try.mjs POST /promises '{"customer_id":"C001","amount":10}'
//   node mock/try.mjs --routes   (health + spec errors)
import worker from './src/index.js';

const args = process.argv.slice(2);
const base = 'http://mock.local';
const reqs = args[0] === '--routes' || args.length === 0 ? [['GET', '/']] : [[args[0], args[1], args[2]]];
for (const [method, path, body] of reqs) {
  const init = { method: method.toUpperCase(), headers: {} };
  if (body !== undefined) {
    init.body = body;
    init.headers['content-type'] = 'application/json';
  }
  const res = await worker.fetch(new Request(base + path, init));
  console.log(`${init.method} ${path} -> ${res.status}`);
  console.log(await res.text());
}
