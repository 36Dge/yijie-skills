import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";

function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

const sourceDirectory = argument("--source");
const cachePath = argument("--cache");
const outputPath = argument("--output") ?? "docs/provenance/source-audits/FEAT-129-copywriting-source-audit.json";
if (!sourceDirectory || !cachePath) {
  throw new Error("Usage: audit-copywriting-source.mjs --source <copywriting-dir> --cache <remote_skills_cache.json> [--output <file>]");
}

const [sourceEntries, skillBytes, cache] = await Promise.all([
  readdir(sourceDirectory, { withFileTypes: true }),
  readFile(path.join(sourceDirectory, "SKILL.md")),
  readFile(cachePath, "utf8").then(JSON.parse),
]);
const cacheEntry = cache.skills?.find((entry) => entry.name === "copywriting");
if (!cacheEntry) throw new Error("copywriting is absent from the supplied cache");
const skillText = skillBytes.toString("utf8");
if (!/^name:\s*copywriting\s*$/m.test(skillText)) throw new Error("source SKILL.md name is not copywriting");

const licenseNames = new Set(["license", "license.md", "license.txt", "notice", "notice.md", "notice.txt", "copying"]);
const licenseFiles = sourceEntries
  .filter((entry) => entry.isFile() && licenseNames.has(entry.name.toLowerCase()))
  .map((entry) => entry.name)
  .sort();
const dependencyPatterns = [
  /\bbrowser\b/i,
  /\bweb\s*search\b/i,
  /\bmcp\b/i,
  /\bapi\b/i,
  /\bpython\b/i,
  /\bshell\b/i,
  /\bselenium\b/i,
  /\bjungle\s*scout\b/i,
  /supplier[_ -]?search/i,
];
const declaredExternalDependencies = dependencyPatterns
  .filter((pattern) => pattern.test(skillText))
  .map((pattern) => pattern.source);

const report = {
  schema_version: 1,
  feature_id: "FEAT-129",
  source_label: "user-provided/05Skill广场/内容创作与营销/copywriting",
  observed_at: "2026-08-25T00:00:00Z",
  observed: {
    cache_id: cacheEntry.id,
    runtime_name: cacheEntry.name,
    version: cacheEntry.version,
    owner_type: cacheEntry.ownerType,
    official_marker: cacheEntry.official,
    source_url: cacheEntry.oss,
    skill_sha256: sha256(skillBytes),
    top_level_files: sourceEntries.filter((entry) => entry.isFile()).map((entry) => entry.name).sort(),
    top_level_directories: sourceEntries.filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort(),
    license_files: licenseFiles,
    declared_external_dependencies: declaredExternalDependencies,
  },
  decisions: {
    selected_capability: true,
    source_content_copied: false,
    reauthored_candidate: "plugins/yijie-desktop-skills/skills/copywriting",
    upstream_redistribution_status: licenseFiles.length === 0 ? "blocked" : "review_required",
    local_candidate_status: declaredExternalDependencies.length === 0 ? "model-only-eligible" : "dependency-review-required",
  },
};

await mkdir(path.dirname(outputPath), { recursive: true });
await writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(`Wrote sanitized source audit to ${outputPath}.`);
