import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, writeFile, rm, cp, readdir } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { promisify } from "node:util";

const exec = promisify(execFile);
const data = path.resolve("plugins/yijie-desktop-skills/experts/data-analyst-pro/skills/data-workbench");
const ui = path.resolve("plugins/yijie-desktop-skills/experts/ui-designer/skills/ui-workbench");
const hash = v => createHash("sha256").update(v).digest("hex");
const json = async p => JSON.parse(await readFile(p, "utf8"));
async function workspace(fn) {
  const cwd = await mkdtemp(path.join(os.tmpdir(), "yijie-data-ui-"));
  try { await fn(cwd); } finally { await rm(cwd, { recursive: true, force: true }); }
}
const run = (script, cwd, args) => exec("python3", ["-B", script, ...args], { cwd });
async function analyze(cwd, config, output = "result") {
  await writeFile(path.join(cwd, "input.json"), JSON.stringify(config));
  await run(path.join(data, "scripts/analyze.py"), cwd, ["--input", "input.json", "--output", output]);
  return json(path.join(cwd, output, "analysis.json"));
}

test("data EDA independently matches exact sums, type7 quartiles, sample variance, missing states and source rows", async () => workspace(async cwd => {
  await cp(path.join(data, "examples/sample.csv"), path.join(cwd, "sample.csv"));
  const input = await json(path.join(data, "examples/input.json"));
  const before = await readFile(path.join(cwd, "sample.csv"));
  const r = await analyze(cwd, input);
  assert.equal(r.cleaning.before, 7); assert.equal(r.cleaning.after, 6); assert.equal(r.cleaning.removed, 1);
  assert.deepEqual(r.cleaning.cell_quality.amount, { valid: 4, missing: 1, invalid: 1 });
  assert.deepEqual(r.cleaning.identifiers.id.repeated, { R1: [2, 7] });
  assert.equal(r.metrics.amount.known_sum, "600"); assert.equal(r.metrics.amount.mean, "150");
  assert.equal(r.metrics.amount.median, "150.0"); assert.equal(r.metrics.amount.q1_type7, "75.00");
  assert.equal(r.metrics.amount.q3_type7, "225.00");
  assert.equal(Number(r.metrics.amount.sample_variance), 50000 / 3);
  assert.equal(r.groups.find(g => g.group === "C").metrics.amount.known_sum, null);
  assert.equal(r.groups.find(g => g.group === "B").metrics.amount.known_sum, "0");
  assert.deepEqual(r.trend.excluded_rows, [7]);
  assert.deepEqual(r.histograms.amount.counts, [1, 1, 2]);
  assert.equal(r.histograms.amount.unavailable, 2);
  const ledger = await json(path.join(cwd, "result/row-ledger.json"));
  assert.equal(ledger[2].duplicate_of, 3); assert.equal(ledger[2].retained, false);
  assert.equal(ledger[6].cells.amount.raw.raw, "invalid");
  assert.deepEqual(await readFile(path.join(cwd, "sample.csv")), before);
  const receipt = await json(path.join(cwd, "result/receipt.json"));
  assert.equal(receipt.source_sha256, hash(before)); assert.equal(receipt.browser_validation, "NOT RUN");
  for (const [name, digest] of Object.entries(receipt.files)) assert.equal(hash(await readFile(path.join(cwd, "result", name))), digest);
  await run(path.join(cwd, "result/reproduce/scripts/analyze.py"), cwd, ["--input", "result/reproduce/input.json", "--output", "rerun"]);
  const replay = await json(path.join(cwd, "rerun/analysis.json"));
  replay.source.filename = r.source.filename;
  assert.deepEqual(replay, r);
  await assert.rejects(analyze(cwd, input), e => e.code === 2 && e.stderr.includes("File exists"));
  assert.deepEqual(await json(path.join(cwd, "result/analysis.json")), r);
  const html = await readFile(path.join(cwd, "result/report.html"), "utf8");
  assert.ok(html.includes("样本标准差") && html.includes("切换暗色"));
  await exec(process.execPath, ["--check", path.join(cwd, "result/report.js")]);
}));

test("data empty/all-missing/one-value/keep-all cases preserve unavailable versus actual zero", async () => workspace(async cwd => {
  const input = await json(path.join(data, "examples/input.json"));
  await writeFile(path.join(cwd, "sample.csv"), "id,channel,day,amount\n");
  const empty = await analyze(cwd, input, "empty");
  assert.equal(empty.cleaning.after, 0); assert.equal(empty.metrics.amount.known_sum, null);
  assert.equal(empty.metrics.amount.coverage, null); assert.equal(empty.groups.length, 3);
  await writeFile(path.join(cwd, "sample.csv"), "id,channel,day,amount\n1,A,2026-10-01,NA\n2,A,2026-10-01,NA\n");
  const missing = await analyze(cwd, input, "missing");
  assert.equal(missing.metrics.amount.valid, 0); assert.equal(missing.metrics.amount.mean, null);
  await writeFile(path.join(cwd, "sample.csv"), "id,channel,day,amount\n1,A,2026-10-01,0\n");
  const single = await analyze(cwd, input, "single");
  assert.equal(single.metrics.amount.mean, "0"); assert.equal(single.metrics.amount.sample_stddev, null);
  await cp(path.join(data, "examples/sample.csv"), path.join(cwd, "sample.csv"));
  input.duplicate_policy = "keep_all";
  const kept = await analyze(cwd, input, "kept");
  assert.equal(kept.cleaning.after, 7); assert.equal(kept.metrics.amount.known_sum, "800");
  assert.deepEqual(kept.cleaning.identifiers.id.repeated, { R1: [2, 7], R2: [3, 4] });
}));

test("data JSON and value-only XLSX agree with CSV; explicit date and histogram exclusions remain visible", async () => workspace(async cwd => {
  const input = await json(path.join(data, "examples/input.json"));
  const records = [{ id: "001", channel: "A", day: "2026-10-01", amount: "0.1" }, { id: "002", channel: "B", day: "2026-10-02", amount: "0.2" }, { id: "003", channel: "B", day: "2026-10-09", amount: "400" }];
  await writeFile(path.join(cwd, "source.json"), JSON.stringify(records));
  input.source = "source.json"; input.json_columns = Object.keys(records[0]);
  const j = await analyze(cwd, input, "json-output");
  assert.equal(j.metrics.amount.known_sum, "400.3"); assert.equal(j.histograms.amount.outside, 1);
  assert.deepEqual(j.trend.excluded_rows, [3]);
  const quotation = path.resolve("plugins/yijie-desktop-skills/experts/tradebuddy-baojia/skills/local-quotation/scripts/quotation.py");
  await run(quotation, cwd, ["--help"]);
  await exec("python3", ["-B", "-c", "import importlib.util,sys,json; s=importlib.util.spec_from_file_location('q',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=json.load(open(sys.argv[2]));m.write_xlsx(sys.argv[3],[('Data',[list(r[0])]+[list(x.values()) for x in r])])", quotation, path.join(cwd, "source.json"), path.join(cwd, "source.xlsx")]);
  input.source = "source.xlsx"; input.sheet = "Data"; delete input.json_columns;
  const x = await analyze(cwd, input, "xlsx-output");
  assert.deepEqual(x.metrics, j.metrics); assert.deepEqual(x.groups, j.groups); assert.deepEqual(x.histograms, j.histograms);
  input.source = "sample.csv"; delete input.sheet;
  await writeFile(path.join(cwd, "sample.csv"), "id,channel,day,amount\n001,A,2026-10-01,0.1\n002,B,2026-10-02,0.2\n003,B,2026-10-09,400\n");
  const c = await analyze(cwd, input, "csv-output");
  assert.deepEqual(c.metrics, j.metrics); assert.deepEqual(c.groups, j.groups);
  input.columns[3].name = "not-provided";
  await assert.rejects(analyze(cwd, input, "missing-column"), e => e.code === 2);
}));

async function uiProject(cwd) {
  const files = { "index.html": '<!doctype html><html lang="zh-CN"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>合成页面</title><link rel="stylesheet" href="tokens.css"></head><body><h1>合成页面</h1><button>操作</button><script src="app.js"></script></body></html>', "app.js": 'document.querySelector("button").addEventListener("click",e=>{e.target.textContent="已操作";});', "brief.md": "合成验收需求", "README.md": "五种状态与操作待真实浏览器验证。", "tokens.css": await readFile(path.join(ui, "templates/yijie-tokens.css"), "utf8") };
  for (const [name, content] of Object.entries(files)) await writeFile(path.join(cwd, name), content);
  const manifest = { schema_version: 1, mode: "local-prototype", title: "合成页面", brief: "brief.md", entry: "index.html", readme: "README.md", tokens: "tokens.css", brief_sha256: hash(files["brief.md"]), tokens_sha256: hash(files["tokens.css"]), files: Object.keys(files), asset_sources: Object.fromEntries(Object.keys(files).map(n => [n, n === "tokens.css" ? "Current Yijie tokens" : "Synthetic test"])), states: ["loading", "empty", "error", "permission-denied", "ready"], interactions: ["操作按钮改变可见文本"] };
  await writeFile(path.join(cwd, "project.json"), JSON.stringify(manifest));
  return { files, manifest };
}

test("UI local manifest verifies real references and source hashes without pretending runtime PASS", async () => workspace(async cwd => {
  const project = path.join(cwd, "page"); await cp(path.join(ui, "examples"), project, { recursive: true });
  const { files, manifest } = await uiProject(project);
  await run(path.join(ui, "scripts/validate_project.py"), cwd, ["--project", project, "--output", "receipt"]);
  const receipt = await json(path.join(cwd, "receipt/validation.json"));
  assert.equal(receipt.static_validation, "PASS"); assert.equal(receipt.runtime_validation, "NOT RUN");
  for (const [name, content] of Object.entries(files)) assert.equal(receipt.files[name], hash(content));
  manifest.files = manifest.files.filter(n => n !== "app.js"); delete manifest.asset_sources["app.js"];
  await writeFile(path.join(project, "project.json"), JSON.stringify(manifest));
  await assert.rejects(run(path.join(ui, "scripts/validate_project.py"), cwd, ["--project", project, "--output", "incomplete"]), e => e.code === 2 && e.stderr.includes("missing from manifest"));
  assert.equal(await readFile(path.join(project, "brief.md"), "utf8"), files["brief.md"]);
}));

test("UI preview serves its real local snapshot and ends through normal shutdown", async () => workspace(async cwd => {
  await uiProject(cwd);
  const probe = "import sys,threading,urllib.request,json;sys.path.insert(0,sys.argv[1]);from preview import server_for;s=server_for(__import__('pathlib').Path(sys.argv[2]),0);t=threading.Thread(target=s.serve_forever);t.start();\ntry:\n r=urllib.request.urlopen('http://127.0.0.1:'+str(s.server_port)+'/');print(json.dumps({'status':r.status,'body':r.read().decode(),'csp':r.headers['Content-Security-Policy']}))\nfinally:\n s.shutdown();s.server_close();t.join()";
  const result = await exec("python3", ["-B", "-c", probe, path.join(ui, "scripts"), cwd]);
  const r = JSON.parse(result.stdout); assert.equal(r.status, 200); assert.ok(r.body.includes("合成页面")); assert.ok(r.csp.includes("connect-src 'none'"));
}));

test("data report 0.1.1 preserves the entire analysis and source receipt while independently retaining 0.1.0", async () => workspace(async cwd => {
  await cp(path.join(data, "examples/sample.csv"), path.join(cwd, "sample.csv"));
  const input = await json(path.join(data, "examples/input.json"));
  const original = await analyze(cwd, input, "v010");
  const repaired = path.resolve("plugins/yijie-desktop-skills/experts/data-analyst-pro/versions/0.1.1/data-workbench");
  await run(path.join(repaired, "scripts/analyze.py"), cwd, ["--input", "input.json", "--output", "v011"]);
  const current = await json(path.join(cwd, "v011/analysis.json"));
  assert.equal(current.expert_version, "0.1.1");
  assert.deepEqual({ ...current, expert_version: "0.1.0" }, original);
  assert.deepEqual(await readFile(path.join(cwd, "v011/row-ledger.json")), await readFile(path.join(cwd, "v010/row-ledger.json")));
  assert.deepEqual(await readFile(path.join(cwd, "v011/cleaned.csv")), await readFile(path.join(cwd, "v010/cleaned.csv")));
  const receipt = await json(path.join(cwd, "v011/receipt.json"));
  assert.equal(receipt.expert_version, "0.1.1");
  assert.equal(receipt.source_sha256, original.source.sha256);
}));

async function tree(root, relative = "") {
  const files = {};
  for (const entry of await readdir(path.join(root, relative), { withFileTypes: true })) {
    const name = path.join(relative, entry.name);
    if (entry.isDirectory()) Object.assign(files, await tree(root, name));
    else files[name] = hash(await readFile(path.join(root, name)));
  }
  return files;
}

test("data 0.1.2 normal Python execution leaves its writable resource tree byte-identical without relying on -B", async () => workspace(async cwd => {
  const source = path.resolve("plugins/yijie-desktop-skills/experts/data-analyst-pro/versions/0.1.2/data-workbench");
  const asset = path.join(cwd, "resource"); await cp(source, asset, { recursive: true });
  const before = await tree(asset);
  await exec("python3", [path.join(asset, "scripts/analyze.py"), "--input", path.join(asset, "examples/input.json"), "--output", path.join(cwd, "result")], { env: { ...process.env, PYTHONDONTWRITEBYTECODE: "" } });
  assert.deepEqual(await tree(asset), before);
  const r = await json(path.join(cwd, "result/analysis.json"));
  assert.equal(r.expert_version, "0.1.2"); assert.equal(r.metrics.amount.known_sum, "600");
  assert.equal(r.cleaning.after, 6);
}));

test("UI 0.1.1 normal approved-style preview import and HTTP/stop never add resource bytecode", async () => workspace(async cwd => {
  const source = path.resolve("plugins/yijie-desktop-skills/experts/ui-designer/versions/0.1.1/ui-workbench");
  const asset = path.join(cwd, "resource"), project = path.join(cwd, "page");
  await cp(source, asset, { recursive: true }); await cp(path.join(ui, "examples"), project, { recursive: true });
  await uiProject(project); const before = await tree(asset);
  const probe = "import subprocess,sys,json,urllib.request,os;p=subprocess.Popen([sys.executable,sys.argv[1],'--project',sys.argv[2]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE=''));\ntry:\n info=json.loads(p.stdout.readline());r=urllib.request.urlopen(info['url']);print(json.dumps({'status':r.status,'body':r.read().decode()}))\nfinally:\n out,err=p.communicate('stop\\n',timeout=10);print(out);assert p.returncode==0,err";
  const result = await exec("python3", ["-c", probe, path.join(asset, "scripts/preview.py"), project]);
  assert.ok(result.stdout.includes('"status": 200'));
  assert.ok(result.stdout.includes("Preview stopped normally."));
  assert.deepEqual(await tree(asset), before);
}));
