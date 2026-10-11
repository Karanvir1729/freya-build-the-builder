# Bank services mock (Cloudflare Worker)

A generic, data-driven mock of a bank's services. The Worker (`src/index.js`) has no bank-specific code:
every endpoint, fixture and error comes from `src/routes.js`. Plain JS module Worker, no npm dependencies.

- Deployed: https://freya-bank-mock-kk.mehar-144.workers.dev (Cloudflare account mehar@daybot.ca)
- `GET /` health: `{ok: true, routes: ["GET /ping", ...]}` (plus `spec_errors` if routes.js has mistakes)
- `GET /openapi.json` the `openapi` export, with `servers[0].url` set to the request's origin
- `GET /__log?limit=n` the last 200 requests (method, path, query, body, status, route, key, time, ms);
  `DELETE /__log` clears it. Best effort only: it is in-memory per isolate, isolates are not shared
  and are recycled, so it may miss requests. For a complete log use `npx wrangler tail freya-bank-mock-kk`.
- Unknown path: 404 `{error: 'not_found'}`; known path, wrong method: 405 `{error: 'method_not_allowed'}`.

## Filling routes.js from an integration document

For each endpoint in the document, add one entry to `routes`, and describe it in `openapi.paths`
(copy the document's schemas; the tool API file the phone agent uses can be this document,
fetched from `/openapi.json`). Route spec (all keys optional except `method` and `path`):

```js
{
  method: 'GET',                         // or 'POST', 'PUT', ..., '*' for any
  path: '/accounts/{customer_id}',       // {param} placeholders
  key: 'path.customer_id',               // where the fixture key is read:
                                         //   'path.<param>' | 'query.<name>' | 'body.<a.b.c>' | 'header.<name>'
                                         //   or {in: 'path'|'query'|'body'|'header', name: '...'}
                                         //   or an array of them (values joined with '|': 'C001|2026-10-12')
  normalize: 'upper',                    // 'trim' (default) | 'upper' | 'lower' | 'digits' | 'alnum' | 'none'
                                         //   applied to the request value AND the fixture keys
  validate: [                            // checked in order; first failure answers `error`
    { in: 'body', name: 'amount', required: true, type: 'number', min: 0.01, max: 10000 },
    { in: 'body', name: 'channel', enum: ['card', 'bank_transfer'] },  // only checked when present
    // also: equals, not_equals, pattern (regex), min_length, max_length, exists: false,
    //       error: {status, body} per rule
  ],
  error: { status: 400, body: { error: 'invalid_request', field: '{{error.field}}', reason: '{{error.reason}}' } },
  fixtures: {                            // key -> response, exactly as returned (status + body)
    'C001': { status: 200, body: { ... } },
    'C002': [                            // or a list: first entry whose `when` rules all pass
      { when: [{ in: 'body', name: 'amount', max: 120.5 }], status: 201, body: { ok: true } },
      { status: 422, body: { ok: false, error: 'amount_exceeds_balance' } },
    ],
    'C009': { status: 503, body: { error: 'unavailable' }, delay_ms: 8000, headers: { 'retry-after': '5' } },
  },
  default: { status: 404, body: { error: 'customer_not_found' } },   // unknown or missing key (alias: response)
  invalid_json: { status: 400, body: { error: 'invalid_json' } },     // body is not JSON
}
```

- `type`: `string`, `number`, `integer`, `boolean`, `object`, `array`. Body values are checked strictly
  (`"50"` is not a number); path/query/header values are strings, so `number` accepts `"50"` there.
- `error.reason` is one of `missing`, `wrong_type`, `not_allowed`, `not_equal`, `bad_format`,
  `too_small`, `too_large`, `too_short`, `too_long`.
- Templates in response bodies: `{{path.x}}`, `{{query.x}}`, `{{body.a.b}}`, `{{headers.x}}`, `{{key}}`,
  `{{now}}` (ISO time), `{{today}}` (YYYY-MM-DD), `{{error.field}}`, `{{error.reason}}`, `{{error.in}}`.
  A string that is only a placeholder keeps the value's type (`'{{body.amount}}'` gives `50`, not `"50"`).
- `when` rules use the same fields as `validate`; an absent value fails a `when` rule unless `exists: false`.
- `delay_ms` (max 30000) simulates a slow service or a timeout.
- `export const config = { validate: [...], validation_error, not_found, invalid_json }` applies to every
  route (e.g. an API key: `{ in: 'header', name: 'x-api-key', required: true, equals: '...', error: { status: 401, body: {...} } }`).
- If `openapi.paths` is empty, `/openapi.json` is generated from the routes (paths and path params only).

### Example: GET with a path param

```js
{
  method: 'GET', path: '/accounts/{customer_id}', key: 'path.customer_id', normalize: 'upper',
  fixtures: {
    'C001': { status: 200, body: { customer_id: 'C001', name: 'Ada Lovelace', balance: 120.5 } },
    'C002': { status: 423, body: { error: 'account_locked' } },
  },
  default: { status: 404, body: { error: 'customer_not_found', customer_id: '{{path.customer_id}}' } },
}
```

### Example: POST with a JSON body lookup

```js
{
  method: 'POST', path: '/promises', key: 'body.customer_id',
  validate: [
    { in: 'body', name: 'customer_id', required: true, type: 'string' },
    { in: 'body', name: 'amount', required: true, type: 'number', min: 0.01 },
  ],
  error: { status: 400, body: { ok: false, error: 'invalid_request', field: '{{error.field}}' } },
  fixtures: {
    'C001': { status: 201, body: { ok: true, promise_id: 'PR-{{key}}-1', amount: '{{body.amount}}', created_at: '{{now}}' } },
  },
  default: { status: 404, body: { ok: false, error: 'customer_not_found' } },
}
```

## Test locally (no network)

```bash
node mock/try.mjs                     # health + spec errors
node mock/try.mjs GET /ping
node mock/try.mjs GET '/accounts/C001?x=1'
node mock/try.mjs POST /promises '{"customer_id":"C001","amount":10}'
cd mock && npx --yes wrangler dev     # local server on http://localhost:8787
```

## Deploy

```bash
cd mock && npx --yes wrangler deploy  # wrangler is logged in to mehar@daybot.ca
```

Right after the first deploy some edges answered `error code: 1042` (HTTP 404, text/plain) for about
half a minute while the workers.dev route propagated; it went away on its own.

## Test the deployed Worker

```bash
U=https://freya-bank-mock-kk.mehar-144.workers.dev
curl -s $U/ ; curl -s $U/ping ; curl -s $U/openapi.json
curl -s -X POST $U/promises -H 'content-type: application/json' -d '{"customer_id":"C001","amount":10}'
curl -s "$U/__log?limit=20"           # best effort (per isolate)
npx wrangler tail freya-bank-mock-kk --format pretty   # every request, live
```
