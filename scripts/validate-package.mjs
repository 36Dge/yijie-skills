import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { lstat, readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { parse } from "smol-toml";
import { createStoredZip, isSafeRelativePath } from "./lib/deterministic-zip.mjs";

const execFileAsync = promisify(execFile);
const CONTRACT_VERSION = "0.5.1";
const CONTRACT_REVISION = "164b14f609537d727a52326832da04430aecc4ab";
const LICENSE_EXPRESSION = "LicenseRef-YiJie-Desktop-Distribution-Owner-Attestation";
const ATTESTATION_ID = "FEAT-129-DESKTOP-DISTRIBUTION-2026-08-25";
const CATEGORY_COUNTS = {
  "sourcing-selection": 5,
  "market-research": 9,
  "content-marketing": 7,
  "traffic-advertising": 9,
  "store-operations": 8,
};
const CATEGORY_ICONS = {
  "sourcing-selection": "skillSourcing",
  "market-research": "skillResearch",
  "content-marketing": "skillContent",
  "traffic-advertising": "skillTraffic",
  "store-operations": "skillOperations",
};
const EXPECTED_RUNTIME_NAMES = {
  "sourcing-selection": [
    "aliexpress-supplier-evaluator",
    "dropshipping-supplier-integrator",
    "product-supplier-sourcing",
    "sales-negotiator",
    "supplier-performance-manager",
  ],
  "market-research": [
    "alibaba-amazon-market-intel",
    "competitor-deep-analysis",
    "cross-border-selection",
    "jungle-scout-deep-dive-analyzer",
    "market-insight-product-selection",
    "product-attribute-analyzer",
    "product-selection",
    "review-analyst-agent",
    "scenario-driven-product-scout",
  ],
  "content-marketing": [
    "content-breakdown",
    "content-strategy",
    "copywriting",
    "product-marketing-context",
    "social-media-content-creator",
    "vibe-marketing",
    "xiaohongshu-content-creator",
  ],
  "traffic-advertising": [
    "amazon-listing-expert",
    "amazon-ppc-campaign-manager",
    "amz-hot-keywords",
    "amz-product-optimizer",
    "ecommerce-seo-optimizer",
    "etsy-seo-optimizer",
    "product-description-generator",
    "seo-keyword-research",
    "tiktok-ads-strategy",
  ],
  "store-operations": [
    "amazon-brand-protection",
    "buy-now-pay-later-setup",
    "ecommerce-gdpr-compliance",
    "invoice-generator",
    "multichannel-inventory-sync",
    "payment-fraud-detector",
    "tiktok-shop-setup",
    "warehouse-fulfillment-workflow",
  ],
};
const HIGH_CONFIDENCE_SECRET_PATTERNS = [
  /-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----/,
  /\bAKIA[0-9A-Z]{16}\b/,
  /\bAIza[0-9A-Za-z_-]{35}\b/,
  /\bgh[pousr]_[0-9A-Za-z]{30,}\b/,
  /\bsk-[A-Za-z0-9]{20,}\b/,
  /\bxox[baprs]-[0-9A-Za-z-]{20,}\b/,
];

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function assertUnique(values, label) {
  if (new Set(values).size !== values.length) throw new Error(`Duplicate ${label}`);
}

function packageTreeSha256(skillId, entries) {
  const digest = createHash("sha256");
  for (const entry of [...entries].sort((left, right) => left.name.localeCompare(right.name))) {
    for (const value of [skillId, entry.name, sha256(entry.content)]) {
      const bytes = Buffer.from(value, "utf8");
      const size = Buffer.alloc(8);
      size.writeBigUInt64BE(BigInt(bytes.length));
      digest.update(size);
      digest.update(bytes);
    }
  }
  return digest.digest("hex");
}

async function listSourceFiles(root, current = root) {
  const files = [];
  for (const directoryEntry of await readdir(current, { withFileTypes: true })) {
    const absolute = path.join(current, directoryEntry.name);
    const stat = await lstat(absolute);
    if (stat.isSymbolicLink()) throw new Error(`Vendored source contains a symlink: ${absolute}`);
    if (stat.isDirectory()) {
      files.push(...await listSourceFiles(root, absolute));
    } else if (stat.isFile()) {
      files.push(path.relative(root, absolute).split(path.sep).join("/"));
    } else {
      throw new Error(`Vendored source contains an unsupported file type: ${absolute}`);
    }
  }
  return files.sort();
}

async function readReviewedEntries(skill) {
  const sourceRoot = path.resolve(skill.source_dir);
  const actualFiles = await listSourceFiles(sourceRoot);
  const declaredFiles = [...skill.package_files].sort();
  const exactSnapshot = skill.source_dir.startsWith("vendor/feat-129/");
  const filesMatch = exactSnapshot
    ? JSON.stringify(actualFiles) === JSON.stringify(declaredFiles)
    : declaredFiles.every((file) => actualFiles.includes(file));
  if (!filesMatch) {
    throw new Error(`${skill.runtime_name} declared package files do not match its source snapshot`);
  }
  const entries = [];
  for (const relative of declaredFiles) {
    if (!isSafeRelativePath(relative)) throw new Error(`Unsafe source path: ${skill.runtime_name}/${relative}`);
    if (relative === ".DS_Store" || relative.endsWith("/.DS_Store") || relative.endsWith("debug_page.html")) {
      throw new Error(`${skill.runtime_name} contains an excluded local/debug artifact: ${relative}`);
    }
    const content = await readFile(path.join(sourceRoot, relative));
    if (content.length > 262144) throw new Error(`${skill.runtime_name}/${relative} exceeds the reviewed file limit`);
    for (const pattern of HIGH_CONFIDENCE_SECRET_PATTERNS) {
      if (pattern.test(content.toString("utf8"))) {
        throw new Error(`${skill.runtime_name}/${relative} contains high-confidence credential material`);
      }
    }
    entries.push({ name: relative, content });
  }
  if (!declaredFiles.includes("SKILL.md") || !declaredFiles.includes("NOTICE.md")) {
    throw new Error(`${skill.runtime_name} must package SKILL.md and NOTICE.md`);
  }
  const skillText = entries.find(({ name }) => name === "SKILL.md").content.toString("utf8");
  const declaredName = skillText.match(/^name:\s*([^\r\n]+)$/m)?.[1]?.trim();
  if (declaredName !== skill.runtime_name) {
    throw new Error(`${skill.runtime_name} frontmatter name drifted: ${declaredName ?? "missing"}`);
  }
  for (const entry of entries.filter(({ name }) => name.endsWith(".py"))) {
    const absolute = path.join(sourceRoot, entry.name);
    await execFileAsync("python3", [
      "-c",
      "import ast,pathlib,sys; p=pathlib.Path(sys.argv[1]); ast.parse(p.read_text(encoding='utf-8'), filename=str(p))",
      absolute,
    ]);
  }
  return entries;
}

const marketplace = parse(await readFile("marketplace/yijie-marketplace.toml", "utf8"));
const pluginDirectories = (await readdir("plugins", { withFileTypes: true }))
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();
for (const directory of pluginDirectories) {
  const plugin = parse(await readFile(`plugins/${directory}/plugin.toml`, "utf8"));
  const registered = marketplace.plugins?.find((entry) => entry.id === plugin.id);
  if (!registered || registered.version !== plugin.version || registered.risk_level !== plugin.risk_level) {
    throw new Error(`${plugin.id} metadata does not match the marketplace entry`);
  }
}

const listingSchema = JSON.parse(await readFile("shared/output-schemas/listing-diagnosis.schema.json", "utf8"));
const listingExample = JSON.parse(
  await readFile("plugins/amazon-listing-optimizer/skills/listing-diagnosis/examples/output-001.json", "utf8"),
);
const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
const validateListing = ajv.compile(listingSchema);
if (!validateListing(listingExample)) {
  throw new Error(`Invalid example output: ${ajv.errorsText(validateListing.errors)}`);
}

const [lockBytes, v1SchemaBytes, v2SchemaBytes, bundleBytes, sourceAuditBytes, securityReviewBytes, attestationBytes] =
  await Promise.all([
    readFile("contracts/lock.json"),
    readFile("contracts/skill-bundle-manifest-v1.schema.json"),
    readFile("contracts/skill-bundle-manifest-v2.schema.json"),
    readFile("plugins/yijie-desktop-skills/bundle-source.json"),
    readFile("docs/provenance/source-audits/FEAT-129-catalog-38-source-audit.json"),
    readFile("docs/provenance/source-audits/FEAT-129-catalog-38-security-review.json"),
    readFile("docs/provenance/FEAT-129-desktop-distribution-attestation.json"),
  ]);
const lock = JSON.parse(lockBytes);
const v2Schema = JSON.parse(v2SchemaBytes);
const bundleSource = JSON.parse(bundleBytes);
const sourceAudit = JSON.parse(sourceAuditBytes);
const securityReview = JSON.parse(securityReviewBytes);
const attestation = JSON.parse(attestationBytes);
if (
  lock.contracts_version !== CONTRACT_VERSION ||
  lock.source_revision_kind !== "git-commit" ||
  lock.source_revision !== CONTRACT_REVISION
) {
  throw new Error("FEAT-129 contracts lock must identify the exact immutable 0.5.1 Catalog First commit");
}
for (const [artifactName, bytes] of [
  ["skill_bundle_manifest_v1", v1SchemaBytes],
  ["skill_bundle_manifest_v2", v2SchemaBytes],
]) {
  const artifact = lock.artifacts[artifactName];
  if (!artifact || sha256(bytes) !== artifact.sha256) {
    throw new Error(`Vendored contract digest drifted: ${artifactName}`);
  }
}
if (
  bundleSource.schema_version !== 2 ||
  bundleSource.bundle_version !== "0.3.0" ||
  bundleSource.bundle_id !== "yijie.desktop.skill-packages" ||
  bundleSource.distribution_channel !== "local-development" ||
  JSON.stringify(bundleSource.authorized_distribution_channels) !==
    JSON.stringify(["local-development", "desktop-release"])
) {
  throw new Error("Desktop Skill source must be the authorized 0.3.0 dual-channel bundle");
}
if (bundleSource.skills.length !== 38) throw new Error("FEAT-129 Catalog must contain exactly 38 Skills");
assertUnique(bundleSource.skills.map(({ id }) => id), "Skill id");
assertUnique(bundleSource.skills.map(({ runtime_name: runtimeName }) => runtimeName), "Runtime name");

const categoryCounts = Object.fromEntries(Object.keys(CATEGORY_COUNTS).map((category) => [category, 0]));
for (const skill of bundleSource.skills) {
  if (!(skill.category in categoryCounts)) throw new Error(`Unknown category: ${skill.category}`);
  categoryCounts[skill.category] += 1;
  if (
    skill.catalog_entry_mode !== "bundled" ||
    skill.release.catalog_status !== "installable" ||
    "blocked_reason" in skill.release ||
    skill.provenance.review_status !== "verified" ||
    skill.license.expression !== LICENSE_EXPRESSION ||
    skill.license.redistribution_status !== "verified" ||
    skill.license.authorization_scope !== "desktop-distribution"
  ) {
    throw new Error(`${skill.runtime_name} is not fully authorized and installable`);
  }
  if (!skill.icon?.key || skill.risk.reasons.length === 0) {
    throw new Error(`${skill.runtime_name} is missing icon or risk metadata`);
  }
  if (skill.capabilities.execution_mode === "model-only" && (
    skill.capabilities.network !== "none" ||
    skill.capabilities.filesystem !== "none" ||
    skill.capabilities.required_tools.length !== 0
  )) {
    throw new Error(`${skill.runtime_name} model-only capability has an undeclared dependency`);
  }
}
if (JSON.stringify(categoryCounts) !== JSON.stringify(CATEGORY_COUNTS)) {
  throw new Error(`FEAT-129 category counts drifted: ${JSON.stringify(categoryCounts)}`);
}
for (const [category, expectedNames] of Object.entries(EXPECTED_RUNTIME_NAMES)) {
  const actualEntries = bundleSource.skills
    .filter((skill) => skill.category === category)
    .sort((left, right) => left.order - right.order);
  if (JSON.stringify(actualEntries.map(({ runtime_name: runtimeName }) => runtimeName)) !== JSON.stringify(expectedNames)) {
    throw new Error(`FEAT-129 ${category} stable Catalog entries drifted`);
  }
  if (actualEntries.some(({ order }, index) => order !== index)) {
    throw new Error(`FEAT-129 ${category} order must be contiguous from zero`);
  }
}

if (
  attestation.attestation_id !== ATTESTATION_ID ||
  attestation.status !== "effective" ||
  attestation.desktop_redistribution_authorized !== true ||
  JSON.stringify(attestation.authorization_scopes) !==
    JSON.stringify(["local-development", "desktop-distribution"])
) {
  throw new Error("FEAT-129 Desktop distribution attestation is not effective");
}
const catalogIds = bundleSource.skills.map(({ id }) => id).sort();
if (JSON.stringify([...attestation.skill_ids].sort()) !== JSON.stringify(catalogIds)) {
  throw new Error("Desktop distribution attestation does not cover the exact 38-Skill Catalog");
}
if (
  sourceAudit.schema_version !== 2 ||
  sourceAudit.entries.length !== 38 ||
  sourceAudit.decisions.installable_entry_count !== 38 ||
  sourceAudit.decisions.catalog_only_entry_count !== 0 ||
  sourceAudit.decisions.desktop_redistribution_authorized !== true ||
  sourceAudit.decisions.source_or_license_blocker !== null
) {
  throw new Error("FEAT-129 source/provenance audit is not fully authorized");
}
if (
  securityReview.entries.length !== 38 ||
  securityReview.all_entries_installable !== true ||
  securityReview.all_entries_runtime_callable !== true ||
  securityReview.overall_decision !== "approved-for-local-development-and-desktop-release" ||
  securityReview.unresolved_release_blockers.length !== 0
) {
  throw new Error("FEAT-129 security review is not approved for all 38 Skills");
}

const sourceAuditById = new Map(sourceAudit.entries.map((entry) => [entry.id, entry]));
const securityById = new Map(securityReview.entries.map((entry) => [entry.id, entry]));
let reviewedFileCount = 0;
for (const skill of bundleSource.skills) {
  const entries = await readReviewedEntries(skill);
  reviewedFileCount += entries.length;
  const packageTree = packageTreeSha256(skill.id, entries);
  const archive = createStoredZip(entries);
  const sourceRecord = sourceAuditById.get(skill.id);
  const securityRecord = securityById.get(skill.id);
  if (
    !sourceRecord ||
    sourceRecord.packaged_tree_sha256 !== packageTree ||
    sourceRecord.package_file_count !== entries.length ||
    sourceRecord.packaged_skill_md_sha256 !== sha256(entries.find(({ name }) => name === "SKILL.md").content) ||
    sourceRecord.redistribution_status !== "verified" ||
    sourceRecord.authorization_scope !== "desktop-distribution"
  ) {
    throw new Error(`${skill.runtime_name} source digest/provenance record drifted`);
  }
  if (
    !securityRecord ||
    securityRecord.package_tree_sha256 !== packageTree ||
    securityRecord.archive_sha256 !== sha256(archive) ||
    securityRecord.package_file_count !== entries.length ||
    securityRecord.installation_authorized !== true ||
    securityRecord.runtime_discovery_authorized !== true ||
    securityRecord.desktop_distribution_authorized !== true
  ) {
    throw new Error(`${skill.runtime_name} security review record drifted`);
  }
  const pythonCheck = entries.some(({ name }) => name.endsWith(".py")) ? "passed" : "not-applicable";
  if (securityRecord.static_checks.python_syntax_check !== pythonCheck) {
    throw new Error(`${skill.runtime_name} Python syntax review status drifted`);
  }
}
if (reviewedFileCount !== 258) throw new Error(`Expected 258 reviewed package files, got ${reviewedFileCount}`);

if (/\/(?:Users|home)\//.test(sourceAuditBytes.toString("utf8")) ||
    /\/(?:Users|home)\//.test(securityReviewBytes.toString("utf8")) ||
    /\/(?:Users|home)\//.test(attestationBytes.toString("utf8"))) {
  throw new Error("FEAT-129 governance evidence contains an absolute local path");
}

const contractAjv = new Ajv2020({ allErrors: true, strict: true });
addFormats(contractAjv);
contractAjv.compile(v2Schema);

console.log(
  `Validated ${pluginDirectories.length} plugin manifest(s), 38 authorized/installable Skills, ${reviewedFileCount} reviewed files, and exact Contracts ${CONTRACT_VERSION} v2.`,
);
