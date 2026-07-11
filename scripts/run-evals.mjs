import { readFile } from "node:fs/promises";

const datasetPath = "plugins/amazon-listing-optimizer/skills/listing-diagnosis/evals/dataset.jsonl";
const lines = (await readFile(datasetPath, "utf8")).split("\n").filter(Boolean);
if (lines.length === 0) throw new Error("Eval dataset is empty.");

const ids = new Set();
for (const [index, line] of lines.entries()) {
  const entry = JSON.parse(line);
  if (!entry.id || ids.has(entry.id)) throw new Error(`Invalid or duplicate eval ID at line ${index + 1}.`);
  if (entry.input?.platform !== "amazon" || !URL.canParse(entry.input?.url)) {
    throw new Error(`Invalid eval input at line ${index + 1}.`);
  }
  if (typeof entry.expected !== "string" || entry.expected.length === 0) {
    throw new Error(`Missing expected behavior at line ${index + 1}.`);
  }
  ids.add(entry.id);
}

console.log(`Validated ${lines.length} synthetic eval case(s).`);
