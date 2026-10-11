// Generic, data-driven mock of a bank's services (Cloudflare Worker, plain JS module, no dependencies).
// Everything bank-specific lives in ./routes.js (see ../README.md for the spec format).
//
// Built-in endpoints:
//   GET  /              health: {ok: true, routes: ["GET /ping", ...]}
//   GET  /openapi.json  the `openapi` export of routes.js, servers[0].url = this request's origin
//   GET  /__log         the last 200 requests (?limit=n); DELETE /__log clears it
import * as data from './routes.js';

const ROUTES = Array.isArray(data.routes) ? data.routes : [];
const CONFIG = data.config || {};
const LOG_MAX = 200;
const MAX_DELAY_MS = 30000;

// Request log. BEST EFFORT ONLY: it lives in this isolate's memory. Cloudflare runs many isolates
// (per colo, and they are recycled at any time), isolates do not share memory, so /__log shows only
// what reached the isolate that answers the /__log request, and it can be empty after an eviction.
const LOG = [];

function logRequest(entry) {
  LOG.push(entry);
  if (LOG.length > LOG_MAX) LOG.splice(0, LOG.length - LOG_MAX);
}

// ---------- spec compilation ----------

const NORMALIZERS = {
  none: (s) => s,
  trim: (s) => s.trim(),
  upper: (s) => s.trim().toUpperCase(),
  lower: (s) => s.trim().toLowerCase(),
  digits: (s) => s.replace(/\D+/g, ''),
  alnum: (s) => s.replace(/[^0-9a-z]+/gi, '').toUpperCase(),
};

function normalizer(name) {
  return NORMALIZERS[name || 'trim'] || NORMALIZERS.trim;
}

function compilePath(path) {
  const names = [];
  let p = String(path || '/');
  if (p.length > 1) p = p.replace(/\/+$/, '');
  const pattern = p
    .replace(/[.*+?^$()|[\]\\]/g, '\\$&')
    .replace(/\{([^}/]+)\}/g, (_, n) => {
      names.push(n);
      return '([^/]+)';
    });
  return { re: new RegExp('^' + pattern + '/?$'), names };
}

const SPEC_ERRORS = [];
const COMPILED = ROUTES.map((r, i) => {
  const where = `routes[${i}] ${r && r.method} ${r && r.path}`;
  if (!r || typeof r !== 'object') {
    SPEC_ERRORS.push(`routes[${i}] is not an object`);
    return null;
  }
  if (!r.path || !String(r.path).startsWith('/')) SPEC_ERRORS.push(`${where}: path must start with /`);
  if (!r.method) SPEC_ERRORS.push(`${where}: method missing`);
  if (r.fixtures && !r.key) SPEC_ERRORS.push(`${where}: fixtures without key`);
  if (!r.fixtures && !r.default && !r.response) SPEC_ERRORS.push(`${where}: no fixtures and no default/response`);
  const norm = normalizer(r.normalize);
  const fixtures = {};
  for (const [k, v] of Object.entries(r.fixtures || {})) fixtures[norm(String(k))] = v;
  return { ...r, method: String(r.method || 'GET').toUpperCase(), ...compilePath(r.path), norm, fixtures };
}).filter(Boolean);

// ---------- request reading ----------

function getIn(obj, dotted) {
  if (obj === undefined || obj === null) return undefined;
  if (dotted === undefined || dotted === null || dotted === '') return obj;
  let cur = obj;
  for (const part of String(dotted).split('.')) {
    if (cur === undefined || cur === null || typeof cur !== 'object') return undefined;
    cur = cur[part];
  }
  return cur;
}

// A source spec is {in: 'path'|'query'|'body'|'header', name: 'a.b'} or the shorthand 'body.a.b'.
function parseSource(spec) {
  if (typeof spec === 'string') {
    const i = spec.indexOf('.');
    return i < 0 ? { in: spec, name: '' } : { in: spec.slice(0, i), name: spec.slice(i + 1) };
  }
  return spec || {};
}

function readSource(ctx, spec) {
  const s = parseSource(spec);
  const where = String(s.in || '').toLowerCase();
  if (where === 'path' || where === 'params') return getIn(ctx.path, s.name);
  if (where === 'query') return getIn(ctx.query, s.name);
  if (where === 'body') return getIn(ctx.body, s.name);
  if (where === 'header' || where === 'headers') return ctx.headers[String(s.name).toLowerCase()];
  return undefined;
}

function sourceLabel(spec) {
  const s = parseSource(spec);
  return { in: s.in, field: s.name };
}

async function readBody(request) {
  if (request.method === 'GET' || request.method === 'HEAD') return { body: undefined, raw: '' };
  let raw = '';
  try {
    raw = await request.text();
  } catch (_) {
    raw = '';
  }
  if (!raw) return { body: undefined, raw };
  const ct = (request.headers.get('content-type') || '').toLowerCase();
  if (ct.includes('application/x-www-form-urlencoded')) {
    return { body: Object.fromEntries(new URLSearchParams(raw)), raw };
  }
  try {
    let body = JSON.parse(raw);
    // config.envelope = 'data': a request whose fields are not wrapped in {data: ...} is read as if they were
    const env = CONFIG.envelope;
    if (env && body && typeof body === 'object' && !Array.isArray(body) && !(env in body)) body = { [env]: body };
    return { body, raw };
  } catch (_) {
    if (ct.includes('json')) return { body: undefined, raw, invalid: true };
    return { body: raw, raw };
  }
}

// ---------- rules (validation and fixture conditions) ----------

function present(v) {
  return v !== undefined && v !== null && v !== '';
}

function typeOk(type, v, fromBody) {
  const s = String(v);
  switch (type) {
    case 'string':
      return typeof v === 'string';
    case 'number':
      return fromBody ? typeof v === 'number' && isFinite(v) : s.trim() !== '' && isFinite(Number(s));
    case 'integer':
      return fromBody ? Number.isInteger(v) : /^-?\d+$/.test(s.trim());
    case 'boolean':
      return fromBody ? typeof v === 'boolean' : /^(true|false)$/i.test(s.trim());
    case 'object':
      return v !== null && typeof v === 'object' && !Array.isArray(v);
    case 'array':
      return Array.isArray(v);
    default:
      return true;
  }
}

// Returns null when the rule passes, else {in, field, reason}.
// mode 'validate': an absent value fails only when rule.required. mode 'when': an absent value fails
// unless rule.exists === false (and a present one fails when rule.exists === false).
function checkRule(rule, ctx, mode) {
  const src = parseSource(rule);
  const v = readSource(ctx, src);
  const fail = (reason) => ({ ...sourceLabel(src), reason });
  const has = present(v);
  if (rule.exists === false) return has ? fail('not_allowed') : null;
  if (!has) {
    if (mode === 'when') return fail('missing');
    return rule.required ? fail('missing') : null;
  }
  const fromBody = String(src.in).toLowerCase() === 'body';
  if (rule.type && !typeOk(rule.type, v, fromBody)) return fail('wrong_type');
  if (Array.isArray(rule.enum) && !rule.enum.map(String).includes(String(v))) return fail('not_allowed');
  if ('equals' in rule && String(v) !== String(rule.equals)) return fail('not_equal');
  if ('not_equals' in rule && String(v) === String(rule.not_equals)) return fail('not_allowed');
  if (rule.pattern && !new RegExp(rule.pattern).test(String(v))) return fail('bad_format');
  if (rule.min !== undefined && !(Number(v) >= rule.min)) return fail('too_small');
  if (rule.max !== undefined && !(Number(v) <= rule.max)) return fail('too_large');
  if (rule.min_length !== undefined && !(String(v).length >= rule.min_length)) return fail('too_short');
  if (rule.max_length !== undefined && !(String(v).length <= rule.max_length)) return fail('too_long');
  return null;
}

// ---------- templating ----------
// Strings in a response body may use {{path.x}}, {{query.x}}, {{body.a.b}}, {{headers.x}}, {{key}},
// {{now}}, {{today}}, {{error.field}}, {{error.reason}}, {{error.in}}. A string that is exactly one
// placeholder keeps the value's type (number, object, ...); inside longer text it is stringified.

function render(value, ctx) {
  if (typeof value === 'string') {
    const whole = value.match(/^\{\{\s*([\w.-]+)\s*\}\}$/);
    if (whole) {
      const v = getIn(ctx, whole[1]);
      return v === undefined ? null : v;
    }
    return value.replace(/\{\{\s*([\w.-]+)\s*\}\}/g, (_, p) => {
      const v = getIn(ctx, p);
      if (v === undefined || v === null) return '';
      return typeof v === 'object' ? JSON.stringify(v) : String(v);
    });
  }
  if (Array.isArray(value)) return value.map((x) => render(x, ctx));
  if (value && typeof value === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(value)) out[k] = render(v, ctx);
    return out;
  }
  return value;
}

// ---------- responses ----------

function jsonResponse(status, body, headers) {
  const s = Number(status) || 200;
  const noBody = s === 204 || s === 205 || s === 304;
  return new Response(noBody ? null : JSON.stringify(body === undefined ? null : body, null, 2), {
    status: s,
    headers: { 'content-type': 'application/json; charset=utf-8', ...(headers || {}) },
  });
}

// A response spec is {status, body, headers?, delay_ms?, when?} or an array of them (first whose
// `when` rules all pass wins; an entry without `when` always matches).
function pick(spec, ctx) {
  if (spec === undefined || spec === null) return null;
  const list = Array.isArray(spec) ? spec : [spec];
  for (const r of list) {
    if (!r || typeof r !== 'object') continue;
    const when = Array.isArray(r.when) ? r.when : r.when ? [r.when] : [];
    if (when.every((rule) => !checkRule(rule, ctx, 'when'))) return r;
  }
  return null;
}

async function send(spec, ctx) {
  const ms = Math.min(Number(spec.delay_ms) || 0, MAX_DELAY_MS);
  if (ms > 0) await new Promise((res) => setTimeout(res, ms));
  return { status: Number(spec.status) || 200, body: render(spec.body === undefined ? {} : spec.body, ctx), headers: spec.headers };
}

async function answerRoute(route, ctx, bodyInfo) {
  if (bodyInfo.invalid) {
    return send(route.invalid_json || CONFIG.invalid_json || { status: 400, body: { error: 'invalid_json' } }, ctx);
  }
  // Validation: global rules (config.validate) first, then the route's own.
  const rules = [...(CONFIG.validate || []), ...(route.validate || [])];
  for (const rule of rules) {
    const err = checkRule(rule, ctx, 'validate');
    if (err) {
      ctx.error = err;
      const spec = rule.error || route.error || CONFIG.validation_error || {
        status: 400,
        body: { error: 'validation_error', field: '{{error.field}}', reason: '{{error.reason}}' },
      };
      return send(pick(spec, ctx) || spec, ctx);
    }
  }
  // Fixture lookup.
  if (route.key) {
    const parts = (Array.isArray(route.key) ? route.key : [route.key]).map((k) => readSource(ctx, k));
    if (parts.every(present)) ctx.key = route.norm(parts.map(String).join('|'));
    const hit = ctx.key !== undefined && Object.prototype.hasOwnProperty.call(route.fixtures, ctx.key)
      ? pick(route.fixtures[ctx.key], ctx)
      : null;
    if (hit) return send(hit, ctx);
  }
  const fallback = pick(route.default !== undefined ? route.default : route.response, ctx);
  if (fallback) return send(fallback, ctx);
  return { status: 404, body: { error: 'no_fixture', key: ctx.key === undefined ? null : ctx.key } };
}

function buildOpenapi(origin) {
  let doc = data.openapi && typeof data.openapi === 'object' ? structuredClone(data.openapi) : null;
  if (!doc || !doc.paths || Object.keys(doc.paths).length === 0) {
    // Fallback: a minimal description generated from the routes.
    doc = doc || { openapi: '3.0.3', info: { title: 'Bank mock', version: '0.1.0' } };
    doc.paths = {};
    for (const r of COMPILED) {
      const op = { summary: r.summary || `${r.method} ${r.path}`, responses: { 200: { description: 'OK' } } };
      if (r.operationId) op.operationId = r.operationId;
      if (r.names.length) op.parameters = r.names.map((n) => ({ name: n, in: 'path', required: true, schema: { type: 'string' } }));
      doc.paths[r.path] = { ...(doc.paths[r.path] || {}), [r.method.toLowerCase()]: op };
    }
  }
  doc.servers = [{ url: origin }, ...(Array.isArray(doc.servers) ? doc.servers.slice(1) : [])];
  return doc;
}

// ---------- handler ----------

async function handle(request) {
  const url = new URL(request.url);
  const method = request.method.toUpperCase();
  const pathname = url.pathname;

  if (pathname === '/__log') {
    if (method === 'DELETE') {
      LOG.length = 0;
      return { status: 200, body: { ok: true, cleared: true }, skipLog: true };
    }
    const limit = Math.max(1, Math.min(LOG_MAX, Number(url.searchParams.get('limit')) || LOG_MAX));
    return {
      status: 200,
      body: {
        note: 'best effort: in-memory per isolate, isolates are not shared and may be recycled',
        count: Math.min(limit, LOG.length),
        entries: LOG.slice(-limit).reverse(),
      },
      skipLog: true,
    };
  }

  const bodyInfo = await readBody(request);
  const ctx = {
    path: {},
    query: Object.fromEntries(url.searchParams),
    body: bodyInfo.body,
    headers: Object.fromEntries([...request.headers].map(([k, v]) => [k.toLowerCase(), v])),
    now: new Date().toISOString(),
    today: new Date().toISOString().slice(0, 10),
    method,
    url: url.pathname + url.search,
  };

  let pathMatched = false;
  for (const route of COMPILED) {
    const m = pathname.match(route.re);
    if (!m) continue;
    pathMatched = true;
    if (route.method !== method && route.method !== '*') continue;
    route.names.forEach((n, i) => {
      try {
        ctx.path[n] = decodeURIComponent(m[i + 1]);
      } catch (_) {
        ctx.path[n] = m[i + 1];
      }
    });
    const out = await answerRoute(route, ctx, bodyInfo);
    return { ...out, route: `${route.method} ${route.path}`, key: ctx.key, ctx, bodyInfo };
  }

  if (method === 'GET' && pathname === '/') {
    const body = { ok: true, routes: COMPILED.map((r) => `${r.method} ${r.path}`), openapi: '/openapi.json', log: '/__log' };
    if (SPEC_ERRORS.length) body.spec_errors = SPEC_ERRORS;
    return { status: 200, body, ctx, bodyInfo };
  }
  if (method === 'GET' && pathname === '/openapi.json') {
    return { status: 200, body: buildOpenapi(url.origin), ctx, bodyInfo, skipLog: true };
  }
  if (pathMatched) {
    return { status: 405, body: { error: 'method_not_allowed', method, path: pathname }, ctx, bodyInfo };
  }
  const nf = CONFIG.not_found;
  if (nf) return { ...(await send(nf, ctx)), ctx, bodyInfo };
  return { status: 404, body: { error: 'not_found', method, path: pathname }, ctx, bodyInfo };
}

export default {
  async fetch(request) {
    const started = Date.now();
    let out;
    try {
      out = await handle(request);
    } catch (e) {
      out = { status: 500, body: { error: 'mock_internal_error', detail: String((e && e.message) || e) } };
    }
    if (!out.skipLog) {
      const url = new URL(request.url);
      const bi = out.bodyInfo || {};
      logRequest({
        time: new Date(started).toISOString(),
        method: request.method,
        path: url.pathname,
        query: Object.fromEntries(url.searchParams),
        body: bi.body !== undefined ? bi.body : bi.raw ? String(bi.raw).slice(0, 2000) : null,
        status: out.status,
        route: out.route || null,
        key: out.key === undefined ? null : out.key,
        ms: Date.now() - started,
      });
    }
    return jsonResponse(out.status, out.body, out.headers);
  },
};
