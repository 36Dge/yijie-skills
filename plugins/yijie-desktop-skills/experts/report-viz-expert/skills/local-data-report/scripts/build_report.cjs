/* Local-only report generator. Node >= 18. No package installation or network. */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const echarts = require("../vendor/echarts.cjs");
const hash = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const html = value => String(value).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const safeJSON = value => JSON.stringify(value).replace(/</g, "\\u003c").replace(/\u2028/g, "\\u2028").replace(/\u2029/g, "\\u2029");
const read = file => {
  if (fs.statSync(file).size > 8 * 1024 * 1024) throw new Error("input exceeds 8 MiB");
  return fs.readFileSync(file, "utf8").replace(/^\uFEFF/, "");
};
function required(value, field) {
  if (typeof value !== "string" || !value.trim() || value.length > 500) throw new Error(`missing/invalid ${field}`);
  return value;
}
function csv(source) {
  const rows = []; let row = [], field = "", quoted = false;
  for (let i = 0; i < source.length; i++) {
    const c = source[i];
    if (c === '"') {
      if (quoted && source[i + 1] === '"') { field += '"'; i++; }
      else if (quoted || field === "") quoted = !quoted;
      else throw new Error("invalid CSV quoting");
    } else if (c === "," && !quoted) { row.push(field); field = ""; }
    else if ((c === "\n" || c === "\r") && !quoted) {
      if (c === "\r" && source[i + 1] === "\n") i++;
      row.push(field); if (row.some(v => v !== "")) rows.push(row); row = []; field = "";
    } else field += c;
  }
  if (quoted) throw new Error("unfinished CSV quoted field");
  if (field || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift();
  if (!headers?.length || headers.some(h => !h.trim()) || new Set(headers).size !== headers.length) throw new Error("CSV needs unique nonempty headers");
  return rows.map(row => {
    if (row.length !== headers.length) throw new Error("CSV column count differs from header");
    return Object.fromEntries(headers.map((h, i) => [h, row[i]]));
  });
}
// Six decimal fixed-point arithmetic keeps totals independent of chart floats.
const SCALE = 1000000n;
function scaled(value, location) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value !== "number" && typeof value !== "string") throw new Error(`invalid number: ${location}`);
  const text = String(value).trim();
  if (!/^-?\d{1,10}(?:\.\d{1,6})?$/.test(text)) throw new Error(`use a finite decimal (up to 6 places): ${location}`);
  const [integer, fraction = ""] = text.replace(/^-/, "").split(".");
  const number = (BigInt(integer) * SCALE + BigInt(fraction.padEnd(6, "0"))) * (text.startsWith("-") ? -1n : 1n);
  if (number > 1000000000n * SCALE || number < -1000000000n * SCALE) throw new Error(`out of range: ${location}`);
  return number;
}
function decimal(value) {
  const sign = value < 0n ? "-" : "", absolute = value < 0n ? -value : value;
  const fraction = String(absolute % SCALE).padStart(6, "0").replace(/0+$/, "");
  return sign + String(absolute / SCALE) + (fraction ? "." + fraction : "");
}
function validate(config, rows) {
  ["title", "dimension", "unit", "period", "source"].forEach(k => required(config[k], k));
  if (!["bar", "line"].includes(config.chart_type)) throw new Error("chart_type must be bar or line");
  if (config.chart_type === "line" && config.ordered_dimension !== true) throw new Error("line chart requires an explicitly ordered dimension");
  if (!Array.isArray(config.series) || !config.series.length || config.series.length > 8 || new Set(config.series).size !== config.series.length) throw new Error("need 1–8 unique series columns with a common unit");
  config.series.forEach(k => required(k, "series"));
  if (!Array.isArray(rows) || !rows.length || rows.length > 1000) throw new Error("need 1–1000 rows; split larger reports explicitly without dropping rows");
  for (const series of config.series) if (!rows.some(row => row && Object.hasOwn(row, series))) throw new Error(`series column absent: ${series}`);
  const labels = new Set();
  const data = rows.map((row, index) => {
    if (!row || typeof row !== "object" || Array.isArray(row)) throw new Error(`invalid row ${index + 1}`);
    for (const v of Object.values(row)) if (v !== null && !["string", "number", "boolean"].includes(typeof v)) throw new Error("only scalar table fields supported");
    const label = required(row[config.dimension], `row ${index + 1} dimension`);
    if (labels.has(label)) throw new Error("duplicate dimension labels; explicitly aggregate or give each record a unique label first");
    labels.add(label);
    return config.series.map(s => scaled(row[s], `row ${index + 1} ${s}`));
  });
  const stats = config.series.map((name, i) => {
    const known = data.map(row => row[i]).filter(value => value !== null);
    return { name, known: known.length, missing: rows.length - known.length, sum: known.length ? decimal(known.reduce((a, b) => a + b, 0n)) : null,
      min: known.length ? decimal(known.reduce((a, b) => a < b ? a : b)) : null,
      max: known.length ? decimal(known.reduce((a, b) => a > b ? a : b)) : null };
  });
  return { data, stats };
}
function generate(config, rows, inputs, output) {
  const { data, stats } = validate(config, rows);
  const options = [];
  // Snapshot of YiJie semantic chart tokens; no additional UI or rendering library.
  const palette = ["#4b651d", "#356bea", "#0e7490", "#7c3aed", "#b45309", "#c2410c", "#dc2626", "#475569"];
  for (let start = 0; start < rows.length; start += 30) {
    const group = rows.slice(start, start + 30);
    options.push({ animation: false, color: palette, backgroundColor: "#ffffff",
      textStyle: { fontFamily: 'Arial, "PingFang SC", "Microsoft YaHei", sans-serif', color: "#25282b" },
      title: { text: `${config.title} · ${start + 1}–${start + group.length}`, textStyle: { fontSize: 16, fontWeight: 500 } },
      legend: { type: "scroll", top: 38, data: config.series },
      tooltip: { trigger: "axis", renderMode: "richText", confine: true },
      grid: { top: 90, left: 85, right: 40, bottom: 100 },
      xAxis: { type: "category", data: group.map(r => r[config.dimension]), axisLabel: { interval: 0, rotate: group.length > 8 ? 40 : 0, fontSize: 12 } },
      yAxis: { type: "value", name: config.unit, scale: false, splitLine: { lineStyle: { color: "#edf0f2" } } },
      series: config.series.map((name, i) => ({ name, type: config.chart_type, connectNulls: false, label: { show: group.length <= 12, position: "top" },
        data: data.slice(start, start + 30).map(row => row[i] === null ? null : Number(decimal(row[i]))) })) });
  }
  const svgs = options.map(option => {
    const chart = echarts.init(null, null, { renderer: "svg", ssr: true, width: 1200, height: 520 });
    try { chart.setOption(option); return chart.renderToSVGString(); } finally { chart.dispose(); }
  });
  const audit = { schema_version: 1, title: config.title, source: config.source, period: config.period, unit: config.unit, input_rows: rows.length,
    series: config.series, chart_pages: options.length, statistics: stats, inputs, rounding: "exact decimal sums up to 6 places; chart uses numeric coordinates", missing_policy: "null/empty remains missing; never zero-filled", chart_type: config.chart_type };
  const fields = [...new Set(rows.flatMap(row => Object.keys(row)))];
  const table = `<table><thead><tr>${fields.map(f => `<th>${html(f)}</th>`).join("")}</tr></thead><tbody>${rows.map((row, index) => `<tr data-row="${index + 1}">${fields.map(f => `<td>${row[f] === null || row[f] === undefined || row[f] === "" ? '<span class="missing">缺失</span>' : html(row[f])}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  const conclusions = stats.map(s => `<li><strong>${html(s.name)}</strong>：已知值合计 ${html(s.sum ?? "不可计算")} ${html(config.unit)}；${s.known} 项已知，${s.missing} 项缺失。${s.known ? `范围 ${html(s.min)}–${html(s.max)} ${html(config.unit)}。` : ""}${s.missing ? "这是已知值小计，不能当作完整总额。" : ""}</li>`).join("");
  const lib = fs.readFileSync(path.join(__dirname, "../vendor/echarts.cjs"), "utf8").replace(/<\/script/gi, "<\\/script");
  const license = fs.readFileSync(path.join(__dirname, "../vendor/ECHARTS-LICENSE.txt"), "utf8");
  const notice = fs.readFileSync(path.join(__dirname, "../vendor/ECHARTS-NOTICE.txt"), "utf8");
  const document = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'"><title>${html(config.title)}</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f7f8fa;color:#25282b;font:15px/1.65 Arial,"PingFang SC","Microsoft YaHei",sans-serif}main{max-width:1280px;margin:auto;padding:40px 28px}header{margin-bottom:30px}h1{font-size:28px;font-weight:600;margin:8px 0}h2{font-size:18px;font-weight:600;margin:0 0 16px}p,.muted{color:#656b74}.label{font-size:12px;letter-spacing:2px;color:#4c6252}section{background:white;border:1px solid #e6e8eb;border-radius:12px;padding:24px;margin:20px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;min-width:100%;font-size:14px;font-variant-numeric:tabular-nums}th,td{text-align:left;white-space:nowrap;padding:10px 16px;border-bottom:1px solid #edf0f2}th{background:#f4f6f7;font-weight:500}.missing{color:#9a6b24}li{margin:10px 0}.chart{height:520px;min-width:700px}.chart svg{max-width:100%}details{font-size:12px;color:#656b74}pre{white-space:pre-wrap}@media print{body{background:white}main{padding:0}section{break-inside:avoid}details{display:none}}@media(max-width:700px){main{padding:24px 12px}section{padding:16px}h1{font-size:24px}}
    </style></head><body><main><header><div class="label">易界 · 数据报告</div><h1>${html(config.title)}</h1><p>${html(config.period)} · 单位：${html(config.unit)} · 数据来源：${html(config.source)}</p><p>${rows.length} 条原始记录 · ${config.series.length} 个系列 · 本文件无需联网</p></header><section><h2>数据摘要</h2><ul>${conclusions}</ul><p>展示原始数值，纵轴不截断；缺失值留空。结论仅描述输入，不推断原因或预测。</p></section>${options.map((_, i) => `<section><h2>图表 ${i + 1} / ${options.length}</h2><p>点击图例可切换系列，悬停读取数值。静态打印图保留同一批数据。</p><div class="scroll"><div class="chart" id="chart-${i}">${svgs[i]}</div></div></section>`).join("")}<section><h2>完整原始数据 · ${rows.length} 行</h2><div class="scroll">${table}</div></section><details><summary>计算口径与图表许可</summary><pre>${html(JSON.stringify(audit, null, 2))}</pre><pre>${html(notice + "\n" + license)}</pre></details></main><script id="report-data" type="application/json">${safeJSON({ audit, rows, options })}</script><script>${lib}</script><script>
    const report=JSON.parse(document.getElementById('report-data').textContent); const charts=[];
    report.options.forEach((option,i)=>{const element=document.getElementById('chart-'+i);element.innerHTML='';const chart=echarts.init(element,null,{renderer:'svg'});chart.setOption(option);charts.push(chart)});
    window.reportAudit=Object.freeze({...report.audit,rendered_charts:charts.length});
    window.addEventListener('resize',()=>charts.forEach(chart=>chart.resize()));
    </script></body></html>`;
  fs.mkdirSync(output); // New version directory only; never overwrite user input/history.
  fs.writeFileSync(path.join(output, "report.html"), document, { flag: "wx" });
  svgs.forEach((svg, i) => fs.writeFileSync(path.join(output, `chart-${i + 1}.svg`), svg, { flag: "wx" }));
  fs.writeFileSync(path.join(output, "data.json"), JSON.stringify(rows, null, 2) + "\n", { flag: "wx" });
  fs.writeFileSync(path.join(output, "validation.json"), JSON.stringify(audit, null, 2) + "\n", { flag: "wx" });
  return audit;
}
function main() {
  const args = process.argv.slice(2), values = {};
  for (let i = 0; i < args.length; i += 2) {
    if (!["--config", "--data", "--output-dir"].includes(args[i]) || !args[i + 1]) throw new Error("Usage: node build_report.cjs --config config.json --data data.csv|data.json --output-dir new-folder");
    values[args[i]] = args[i + 1];
  }
  const configFile = required(values["--config"], "--config"), dataFile = required(values["--data"], "--data");
  const output = path.resolve(required(values["--output-dir"], "--output-dir"));
  const relative = path.relative(fs.realpathSync(process.cwd()), path.resolve(fs.realpathSync(path.dirname(output)), path.basename(output)));
  if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) throw new Error("output must be a new subfolder of current task workspace");
  const source = read(dataFile);
  if (![".csv", ".json"].includes(path.extname(dataFile).toLowerCase())) throw new Error("data must be CSV or JSON");
  const rows = path.extname(dataFile).toLowerCase() === ".csv" ? csv(source) : JSON.parse(source);
  const config = JSON.parse(read(configFile));
  const audit = generate(config, rows, [configFile, dataFile].map(file => ({ file: path.basename(file), sha256: hash(fs.readFileSync(file)) })), output);
  console.log(JSON.stringify({ status: "complete", directory: output, rows: audit.input_rows, series: audit.series, chart_pages: audit.chart_pages }));
}
if (require.main === module) { try { main(); } catch (error) { console.error("report not completed: " + error.message); process.exitCode = 2; } }
module.exports = { csv, validate, generate };
