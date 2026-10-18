import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../plugins/yijie-desktop-skills/experts/linkfox-expert-1688-sourcing-expert/skills/sourcing-1688');
const sample = JSON.parse(readFileSync(path.join(root, 'examples/scenario.json')));
const copy = () => structuredClone(sample);
function run(action, value, accept = true) {
  const cwd = mkdtempSync(path.join(tmpdir(), 'yijie-sourcing-normal-'));
  try {
    const input = JSON.stringify(value, null, 2) + '\n';
    writeFileSync(path.join(cwd, 'input.json'), input);
    const args = [path.join(root, 'scripts/sourcing.py'), action, '--input', 'input.json', '--output-dir', 'result'];
    const result = spawnSync('python3', args, { cwd, encoding: 'utf8' });
    if (!accept) { assert.notEqual(result.status, 0); assert.equal(existsSync(path.join(cwd, 'result')), false); return; }
    assert.equal(result.status, 0, result.stderr);
    assert.equal(JSON.parse(result.stdout).external_calls, 0);
    assert.equal(readFileSync(path.join(cwd, 'result/input.json'), 'utf8'), input);
    const parsed = JSON.parse(readFileSync(path.join(cwd, 'result/inspection.json')));
    if (action === 'calculate') parsed.report = readFileSync(path.join(cwd, 'result/report.html'), 'utf8');
    assert.notEqual(spawnSync('python3', args, { cwd, encoding: 'utf8' }).status, 0, 'preserve previous output');
    return parsed;
  } finally { rmSync(cwd, { recursive: true, force: true }); }
}
const query = (method, extra = {}) => ({ method, target_asin: 'B0TEST0001', market: 'US', ...extra });
const obs = (q, body, extra = {}) => ({ query: q, request: run('prepare', q).request, source_operation_id: 'normal-source', captured_at: '2026-10-17T02:00:00Z', mcp_result: { structuredContent: body }, ...extra });
const result = value => run('calculate', value).candidates[0];

test('1688 ten supported methods preserve exact US target and documented parameter names', () => {
  const methods = [
    ['keepa/productRequest', {}, { asin: 'B0TEST0001', domain: '1', history: 0 }],
    ['keepa/productSeries', { days: 90 }, { asin: 'B0TEST0001', domain: '1', days: 90 }],
    ['sif/asinKeywords', {}, { asin: 'B0TEST0001', country: 'US', pageNum: 1, pageSize: 20, timePieceType: 'latelyDay', timePieceValue: '7' }],
    ['sif/asinSummary', {}, { searchValue: 'B0TEST0001', country: 'US', pageNum: 1, pageSize: 20, last7d: true }],
    ['sellersprite/trafficKeyword', {}, { asin: 'B0TEST0001', marketplace: 'US', page: 1, size: 20 }],
    ['alibaba1688/imageSearch', { image_url: 'https://media.example.com/a.jpg' }, { imageUrl: 'https://media.example.com/a.jpg', page: 1, pageSize: 20 }],
    ['dld/productSearch', { keyword: '收纳架' }, { keyWord: '收纳架', cycle: '30', searchType: 1, pageIndex: 1, pageSize: 20 }],
    ['amazon/search', { keyword: 'organizer' }, { keyword: 'organizer', amazonDomain: 'amazon.com', language: 'en_US', page: 1 }],
    ['jiimore/getNicheInfoByKeyword', { keyword: 'organizer' }, { keyword: 'organizer', countryCode: 'US', page: 1, pageSize: 20 }],
    ['aiMode/googleSearch', { keyword: '收纳架 1688' }, { keyword: '收纳架 1688' }],
  ];
  for (const [method, extra, expected] of methods) {
    const r = run('prepare', query(method, extra)); assert.deepEqual(r.request, { toolName: method, arguments: expected });
    assert.equal(r.state, 'prepared_not_submitted'); assert.equal(r.current_tool_schema_verified, false);
  }
});
test('1688 unsupported market, method, options and incomplete media stop without guessing', () => {
  for (const q of [query('keepa/productRequest', { market: 'UK' }), query('other/query'), query('keepa/productRequest', { page: 2 }), query('keepa/productSeries'), query('sif/asinSummary', { page: 0 }), query('alibaba1688/imageSearch', { image_url: 'https://example.com/product' })]) run('prepare', q, false);
});
test('1688 history requires exact unique ASIN, never first-row fallback', () => {
  const q = query('keepa/productSeries', { days: 90 });
  const correct = { asin: 'B0TEST0001', buyboxPrice: [{ time: '2026-10-01', value: 30 }] };
  const wrong = { asin: 'B0TEST0002', buyboxPrice: [{ time: '2026-10-01', value: 99 }] };
  for (const body of [wrong, [wrong], [correct, correct]]) run('observe', obs(q, body), false);
  assert.equal(run('observe', obs(q, [wrong, correct])).row.buyboxPrice[0].value, 30);
});
test('1688 supplier offer ID is distinct from Amazon ASIN and selection is unique', () => {
  const v = copy().observations[1]; const r = run('observe', v);
  assert.equal(r.row.asin, '16880001'); assert.equal(r.target_asin, 'B0TEST0001');
  const unselected = structuredClone(v); delete unselected.offer_id; assert.equal(run('observe', unselected).state, 'candidates_only');
  run('observe', { ...v, offer_id: '16880002' }, false);
  v.mcp_result.structuredContent.products.push(v.mcp_result.structuredContent.products[0]); run('observe', v, false);
});
test('1688 request, product ASIN, currency and site mismatches stop', () => {
  const v = copy().observations[0];
  run('observe', { ...v, request: { ...v.request, arguments: { ...v.request.arguments, asin: 'B0TEST0002' } } }, false);
  for (const change of [b => b.products[0].currency = 'CNY', b => delete b.products[0].currency, b => b.products[0].asin = 'B0TEST0002', b => b.country = 'UK']) {
    const w = structuredClone(v); change(w.mcp_result.structuredContent); run('observe', w, false);
  }
});
test('1688 niche selection requires ID and never uses first row or fuzzy title', () => {
  const q = query('jiimore/getNicheInfoByKeyword', { keyword: 'organizer' });
  const body = { data: [{ nicheId: 'other', nicheTitle: 'organizer accessories', acos: 0.8 }, { nicheId: 'exact', nicheTitle: 'organizer', acos: 0.2 }] };
  assert.equal(run('observe', obs(q, body)).state, 'candidates_only');
  assert.equal(run('observe', obs(q, body, { niche_id: 'exact' })).row.acos, 0.2);
  run('observe', obs(q, body, { niche_id: 'organizer' }), false);
});
test('1688 missing and zero SP counts never infer free advertising or TACoS', () => {
  for (const count of [undefined, 0]) {
    const r = run('observe', obs(query('sif/asinSummary'), { code: '200', data: [{ asin: 'B0TEST0001', sponsoredProductsKeywordCount: count }] }));
    assert.equal(r.advertising_cost_inferred, false); assert.equal(r.row.sponsoredProductsKeywordCount, count);
  }
  const v = copy(); delete v.candidates[0].costs.advertising_usd; assert.equal(result(v).unit_contribution_usd, null);
});
test('1688 ordinary text success, MCP rejection, business errors and unknown shape remain distinct', () => {
  const v = copy().observations[0]; const body = { ...v.mcp_result.structuredContent, code: '200', errmsg: 'ok' };
  assert.equal(run('observe', { ...v, mcp_result: { content: [{ type: 'text', text: JSON.stringify(body) }] } }).state, 'matched');
  for (const mcp_result of [{ isError: true }, { structuredContent: { errcode: 402, errmsg: '余额不足' } }, { structuredContent: { code: 'unknown' } }, { structuredContent: {} }]) run('observe', { ...v, mcp_result }, false);
});
test('1688 explicit decimal scenario handles incremental return cost once', () => {
  const r = result(copy());
  assert.equal(r.state, 'scenario_complete'); assert.equal(r.base_cost_usd, '16.70');
  assert.equal(r.return_adjustment_usd, '2.74'); assert.equal(r.unit_contribution_usd, '10.56');
  assert.equal(r.expected_net_revenue_usd, '27.00'); assert.equal(r.margin_on_net_revenue_percent, '39.11');
  assert.equal(r.monthly_profit, null); assert.equal(r.rank, 1);
});
test('1688 every missing or null cost blocks profit and ranking without defaults', () => {
  for (const field of Object.keys(sample.candidates[0].costs)) {
    for (const mode of ['absent', 'null']) {
      const v = copy(); if (mode === 'absent') delete v.candidates[0].costs[field]; else v.candidates[0].costs[field].value = null;
      const r = result(v); assert.equal(r.state, 'incomplete', field); assert.equal(r.unit_contribution_usd, null); assert.equal(r.rank, null);
    }
  }
});
test('1688 zero provenance, units, source values and timestamps are enforced', () => {
  for (const change of [c => c.other_usd.value = false, c => c.fx_cny_per_usd.unit = 'USD/CNY', c => c.recovery_usd.note = '', c => c.purchase_cny.value = '35', c => c.sale_usd.as_of = '2026-10-16T02:00:00Z', c => c.sale_usd.field = 'monthlySalesUnits']) {
    const v = copy(); change(v.candidates[0].costs); assert.equal(result(v).state, 'incomplete');
  }
  assert.equal(result(copy()).state, 'scenario_complete');
});
test('1688 source order never changes results; wrong target or offer stays incomplete', () => {
  const v = copy(); v.observations.reverse(); assert.equal(result(v).unit_contribution_usd, '10.56');
  v.observations[0].query.target_asin = 'B0TEST0002'; v.observations[0].request = run('prepare', v.observations[0].query).request;
  assert.equal(result(v).state, 'incomplete');
  const w = copy(); w.candidates[0].offer_id = '16880002'; assert.equal(result(w).state, 'incomplete');
  const duplicate = copy(); duplicate.observations.push(duplicate.observations[0]); run('calculate', duplicate, false);
});
test('1688 quote requires matching variant, MOQ and unit', () => {
  for (const change of [q => q.variant = 'red', q => q.purchase_quantity = 99, q => q.purchase_quantity = 100.5, q => q.price_basis = 'CNY/carton', q => q.source = '', q => q.minimum_order_quantity = null]) {
    const v = copy(); change(v.candidates[0].quote); assert.equal(result(v).state, 'incomplete');
  }
});
test('1688 return assumptions are bounded; zero net revenue has no margin and losses remain negative', () => {
  for (const [field, value] of [['return_rate', '1.1'], ['refunded_revenue_usd', '31'], ['referral_refund_usd', '5'], ['recovery_usd', '8']]) {
    const v = copy(); v.candidates[0].costs[field].value = value; assert.equal(result(v).state, 'incomplete');
  }
  const v = copy(); v.candidates[0].costs.return_rate.value = '1'; const r = result(v);
  assert.equal(r.expected_net_revenue_usd, '0.00'); assert.equal(r.margin_on_net_revenue_percent, null); assert.equal(r.unit_contribution_usd, '-14.10');
});
test('1688 report retains inputs, ordinary punctuation and missing-cost evidence without active content', () => {
  const v = copy(); delete v.candidates[0].costs.fba_usd; const r = run('calculate', v);
  assert.match(r.report, /缺项待补，不参与排名/); assert.match(r.report, /fba_usd/); assert.match(r.report, /收纳架 &amp; 配件/);
  assert.doesNotMatch(r.report, /<script|<img|<iframe/); assert.equal(r.candidates[0].unit_contribution_usd, null);
});
test('1688 wrong historical source is preserved as failure without fabricated profit', () => {
  const v = copy(); const q = query('keepa/productSeries', { days: 90 });
  v.observations[0] = obs(q, [{ asin: 'B0TEST0002', buyboxPrice: [{ time: '2026-10-01', value: 99 }] }], { source_operation_id: 'synthetic-product' });
  v.candidates[0].costs.sale_usd.field = 'buyboxPrice.0.value';
  const r = run('calculate', v); assert.ok(r.source_failures['synthetic-product']); assert.equal(r.candidates[0].rank, null);
});

test('1688 historical currency, timestamp and field bounds remain explicit', () => {
  const q = query('keepa/productSeries', { days: 90 });
  run('observe', obs(q, { asin: 'B0TEST0001', currency: 'GBP', buyboxPrice: [{ time: '2026-10-01', value: 30 }] }), false);
  for (const field of ['buyboxPrice.0.value', 'buyboxPrice.9.value']) {
    const v = copy();
    v.observations[0] = obs(q, { asin: 'B0TEST0001', buyboxPrice: [{ value: 30 }] }, { source_operation_id: 'synthetic-product' });
    v.candidates[0].costs.sale_usd.field = field;
    assert.equal(result(v).state, 'incomplete');
  }
});
test('1688 quotation cannot silently lower the selected supplier minimum order', () => {
  const v = copy(); v.observations[1].mcp_result.structuredContent.products[0].quantityBegin = 200;
  assert.equal(result(v).state, 'incomplete');
});
test('1688 normal empty observation input and unknown status stop cleanly', () => {
  const v = copy(); v.observations.push(null); run('calculate', v, false);
  const o = copy().observations[0]; o.mcp_result.structuredContent.status = 'PROCESSING'; run('observe', o, false);
});

test('1688 matching ASIN cannot hide a conflicting row-level market', () => {
  const v = copy().observations[0]; v.mcp_result.structuredContent.products[0].domain = '2'; run('observe', v, false);
  const q = query('keepa/productSeries', { days: 90 });
  run('observe', obs(q, [{ asin: 'B0TEST0001', domain: '2', buyboxPrice: [] }]), false);
  run('observe', obs(q, [null]), false);
});
