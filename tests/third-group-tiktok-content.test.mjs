import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, readFile, writeFile, rm, access } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { promisify } from "node:util";
const exec = promisify(execFile);
const root = path.resolve("plugins/yijie-desktop-skills/experts/chuhaijiang-tiktok-shop-operations-expert/skills/tiktok-shop-operations");
const load = async file => JSON.parse(await readFile(file, "utf8"));
const run = (cwd, input = "input.json", output = "result") => exec("python3", ["-B", path.join(root, "scripts/analyze_shop_report.py"), "--input", input, "--output-dir", output], { cwd });
async function sample(check) {
  const cwd = await mkdtemp(path.join(os.tmpdir(), "yijie-tiktok-report-"));
  try { await check(cwd, await load(path.join(root, "examples/report-input.json"))); }
  finally { await rm(cwd, { recursive: true, force: true }); }
}
const save = (cwd, input) => writeFile(path.join(cwd, "input.json"), JSON.stringify(input));
test("TikTok same-scope report computes exact amounts and preserves missing, source and original file bytes", async () => sample(async (cwd, input) => {
  await save(cwd, input); const original = await readFile(path.join(cwd, "input.json"));
  await run(cwd); const output = await load(path.join(cwd, "result/calculation.json"));
  assert.equal(output.data_mode, "user_provided_report");
  assert.equal(output.current.derived.order_average_value.value, "20.0000");
  assert.equal(output.current.derived.paying_buyer_conversion_percent.value, "9.0000");
  assert.deepEqual(output.current.missing, ["refund_orders"]);
  assert.deepEqual(output.current.derived.refund_order_percent, { value: null, reason: "missing_input" });
  assert.deepEqual(output.comparison.metrics.gmv, { difference: "200", change_percent: { value: "25.0000", reason: null } });
  assert.deepEqual(await readFile(path.join(cwd, "result/data.json")), original);
  assert.deepEqual(await readFile(path.join(cwd, "input.json")), original);
  const calculation = await readFile(path.join(cwd, "result/calculation.json"));
  await assert.rejects(run(cwd), error => error.code === 1);
  assert.deepEqual(await readFile(path.join(cwd, "result/calculation.json")), calculation);
}));
test("TikTok zero baseline and zero denominator are not missing or invented growth", async () => sample(async (cwd, input) => {
  input.previous.metrics.gmv = "0"; input.current.metrics.orders = 0; input.current.metrics.visitors = 0; input.current.metrics.paying_buyers = 0; input.current.metrics.refund_orders = 0;
  await save(cwd, input); await run(cwd); const output = await load(path.join(cwd, "result/calculation.json"));
  assert.equal(output.current.metrics.orders, "0"); assert.deepEqual(output.current.missing, []);
  assert.deepEqual(output.current.derived.order_average_value, { value: null, reason: "zero_denominator" });
  assert.equal(output.current.derived.paying_buyer_conversion_percent.value, null);
  assert.deepEqual(output.comparison.metrics.gmv, { difference: "1000", change_percent: { value: null, reason: "zero_denominator" } });
}));
test("TikTok different currencies, periods and time bases remain visible and never produce comparison", async () => sample(async (cwd, input) => {
  input.previous.currency = "CNY"; input.previous.timezone = "UTC"; input.previous.basis = "realtime-orders"; input.previous.start = "2026-09-30";
  await save(cwd, input); await run(cwd); const output = await load(path.join(cwd, "result/calculation.json"));
  assert.equal(output.comparison.available, false);
  assert.deepEqual(output.comparison.reasons, ["currency_differs", "timezone_differs", "basis_differs", "duration_differs"]);
  assert.equal(output.comparison.metrics, undefined); assert.equal(output.previous.metadata.currency, "CNY");
}));
test("TikTok incomplete periods and omitted metrics fail before writing output", async () => sample(async (cwd, input) => {
  input.current.data_available_date = "2026-10-12";
  await save(cwd, input); await assert.rejects(run(cwd), error => error.code === 1 && error.stderr.includes("period must be complete"));
  await assert.rejects(access(path.join(cwd, "result")));
  input.current.data_available_date = "2026-10-14"; delete input.current.metrics.visitors;
  await save(cwd, input); await assert.rejects(run(cwd), error => error.code === 1 && error.stderr.includes("use null for missing"));
  await assert.rejects(access(path.join(cwd, "result")));
}));
test("TikTok refund-event counts do not become current-order refund rates or cross-basis deltas", async () => sample(async (cwd, input) => {
  input.current.refund_basis = "refund_event_date"; input.current.metrics.refund_orders = 60;
  await save(cwd, input); await run(cwd); const output = await load(path.join(cwd, "result/calculation.json"));
  assert.deepEqual(output.current.derived.refund_order_percent, { value: null, reason: "refund_cohort_unconfirmed" });
  assert.equal(output.comparison.metrics.refund_orders.change_percent.reason, "refund_basis_unconfirmed_or_differs");
}));
