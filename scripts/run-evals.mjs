import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

async function findDatasets(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const child = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await findDatasets(child)));
    else if (entry.name === "dataset.jsonl") files.push(child);
  }
  return files.sort();
}

const datasets = await findDatasets("plugins");
if (datasets.length === 0) throw new Error("No eval datasets found");
const ids = new Set();
let cases = 0;
for (const dataset of datasets) {
  const lines = (await readFile(dataset, "utf8")).split("\n").filter(Boolean);
  if (lines.length === 0) throw new Error(`${dataset} is empty`);
  for (const [index, line] of lines.entries()) {
    const entry = JSON.parse(line);
    if (!entry.id || ids.has(entry.id)) throw new Error(`Invalid or duplicate eval ID at ${dataset}:${index + 1}`);
    if (entry.source !== "synthetic" || entry.input === null || typeof entry.input !== "object" || Array.isArray(entry.input)) {
      throw new Error(`Eval input must be a synthetic object at ${dataset}:${index + 1}`);
    }
    if (typeof entry.expected !== "string" || entry.expected.length === 0) {
      throw new Error(`Missing expected behavior at ${dataset}:${index + 1}`);
    }
    ids.add(entry.id);
    cases += 1;
  }
}

console.log(`Validated ${cases} synthetic eval case(s) across ${datasets.length} dataset(s).`);
