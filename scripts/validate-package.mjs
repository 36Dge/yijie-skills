import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { parse } from "smol-toml";

const CONTRACT_VERSION = "0.5.1";
const CONTRACT_REVISION = "164b14f609537d727a52326832da04430aecc4ab";
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

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function assertUnique(values, label) {
  if (new Set(values).size !== values.length) throw new Error(`Duplicate ${label}`);
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

const schema = JSON.parse(await readFile("shared/output-schemas/listing-diagnosis.schema.json", "utf8"));
const example = JSON.parse(
  await readFile("plugins/amazon-listing-optimizer/skills/listing-diagnosis/examples/output-001.json", "utf8"),
);
const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
const validate = ajv.compile(schema);
if (!validate(example)) throw new Error(`Invalid example output: ${ajv.errorsText(validate.errors)}`);

const [lockBytes, v1SchemaBytes, v2SchemaBytes, bundleSourceBytes, auditBytes] = await Promise.all([
  readFile("contracts/lock.json"),
  readFile("contracts/skill-bundle-manifest-v1.schema.json"),
  readFile("contracts/skill-bundle-manifest-v2.schema.json"),
  readFile("plugins/yijie-desktop-skills/bundle-source.json"),
  readFile("docs/provenance/source-audits/FEAT-129-catalog-38-source-audit.json"),
]);
const lock = JSON.parse(lockBytes);
const v2Schema = JSON.parse(v2SchemaBytes);
const bundleSource = JSON.parse(bundleSourceBytes);
const audit = JSON.parse(auditBytes);
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
  bundleSource.bundle_version !== "0.2.0" ||
  bundleSource.bundle_id !== "yijie.desktop.skill-packages" ||
  bundleSource.distribution_channel !== "local-development"
) {
  throw new Error("Desktop Skill source must be the 0.2.0 local-development Catalog First bundle");
}
if (bundleSource.skills.length !== 38) throw new Error("FEAT-129 Catalog must contain exactly 38 Skills");
assertUnique(bundleSource.skills.map(({ id }) => id), "Skill id");
assertUnique(bundleSource.skills.map(({ runtime_name: runtimeName }) => runtimeName), "Runtime name");

const categoryCounts = Object.fromEntries(Object.keys(CATEGORY_COUNTS).map((category) => [category, 0]));
for (const skill of bundleSource.skills) {
  if (!(skill.category in categoryCounts)) throw new Error(`Unknown category: ${skill.category}`);
  categoryCounts[skill.category] += 1;
  if (!skill.id || !skill.version || !skill.provenance || !skill.license || !skill.risk || !skill.capabilities) {
    throw new Error(`${skill.runtime_name} is missing required Catalog metadata`);
  }
  if (!skill.icon?.key) throw new Error(`${skill.runtime_name} is missing iconKey`);
  if (skill.capabilities.execution_mode === "model-only" && (
    skill.capabilities.network !== "none" ||
    skill.capabilities.filesystem !== "none" ||
    skill.capabilities.required_tools.length !== 0
  )) {
    throw new Error(`${skill.runtime_name} model-only capability must have no external dependency`);
  }
}
if (JSON.stringify(categoryCounts) !== JSON.stringify(CATEGORY_COUNTS)) {
  throw new Error(`FEAT-129 category counts drifted: ${JSON.stringify(categoryCounts)}`);
}
for (const [category, expectedNames] of Object.entries(EXPECTED_RUNTIME_NAMES)) {
  const actualEntries = bundleSource.skills
    .filter((skill) => skill.category === category)
    .sort((left, right) => left.order - right.order);
  const actualNames = actualEntries.map(({ runtime_name: runtimeName }) => runtimeName);
  if (JSON.stringify(actualNames) !== JSON.stringify(expectedNames)) {
    throw new Error(`FEAT-129 ${category} stable Catalog entries drifted`);
  }
  if (actualEntries.some(({ order }, index) => order !== index)) {
    throw new Error(`FEAT-129 ${category} order must be contiguous from zero`);
  }
}

const installable = bundleSource.skills.filter(({ release }) => release.catalog_status === "installable");
const blocked = bundleSource.skills.filter(({ release }) => release.catalog_status === "blocked");
if (installable.length !== 1 || blocked.length !== 37) {
  throw new Error("Catalog must contain one installable bundle and 37 blocked metadata-only entries");
}
const [copywriting] = installable;
if (
  copywriting.id !== "yijie.content-marketing.copywriting" ||
  copywriting.runtime_name !== "copywriting" ||
  copywriting.catalog_entry_mode !== "bundled" ||
  copywriting.version !== "0.1.0" ||
  copywriting.icon?.key !== "edit" ||
  copywriting.risk?.level !== "medium"
) {
  throw new Error("copywriting stable metadata drifted");
}
if (
  copywriting.capabilities.execution_mode !== "model-only" ||
  copywriting.capabilities.network !== "none" ||
  copywriting.capabilities.filesystem !== "none" ||
  copywriting.capabilities.required_tools.length !== 0
) {
  throw new Error("copywriting must remain model-only with no external dependency");
}
if (
  copywriting.license.authorization_scope !== "local-development" ||
  bundleSource.distribution_channel === "desktop-release"
) {
  throw new Error("copywriting lacks desktop-distribution authorization");
}
for (const requiredFile of [
  "NOTICE.md",
  "SKILL.md",
  "agents/openai.yaml",
  "examples/input-001.json",
  "examples/output-001.md",
]) {
  if (!copywriting.package_files.includes(requiredFile)) {
    throw new Error(`copywriting package is missing required reviewed file: ${requiredFile}`);
  }
}

for (const skill of blocked) {
  if (
    skill.catalog_entry_mode !== "catalog-only" ||
    skill.release.blocked_reason !== "license_unverified" ||
    skill.provenance.review_status !== "blocked" ||
    skill.license.redistribution_status !== "blocked" ||
    skill.license.authorization_scope !== "none"
  ) {
    throw new Error(`${skill.runtime_name} must remain a license-blocked catalog-only entry`);
  }
  for (const forbidden of ["source_dir", "package_files", "entrypoint", "archive"]) {
    if (forbidden in skill) throw new Error(`${skill.runtime_name} catalog-only metadata contains ${forbidden}`);
  }
  if (skill.icon.key !== CATEGORY_ICONS[skill.category]) {
    throw new Error(`${skill.runtime_name} iconKey does not match its category registry key`);
  }
}

if (
  audit.feature_id !== "FEAT-129" ||
  audit.entries.length !== 38 ||
  audit.decisions.source_content_copied_for_catalog_only_entries !== false ||
  audit.decisions.official_marker_treated_as_distribution_authorization !== false ||
  audit.decisions.desktop_release_status !== "blocked-pending-license-and-source-proof"
) {
  throw new Error("FEAT-129 38-Skill source audit boundary drifted");
}
assertUnique(audit.entries.map(({ runtime_name: runtimeName }) => runtimeName), "audit Runtime name");
const catalogRuntimeNames = bundleSource.skills.map(({ runtime_name: runtimeName }) => runtimeName).sort();
const auditRuntimeNames = audit.entries.map(({ runtime_name: runtimeName }) => runtimeName).sort();
if (JSON.stringify(catalogRuntimeNames) !== JSON.stringify(auditRuntimeNames)) {
  throw new Error("Catalog entries and source audit entries do not match");
}
for (const entry of audit.entries) {
  if (entry.license_files.length !== 0 || entry.redistribution_status !== "blocked") {
    throw new Error(`${entry.runtime_name} source audit cannot claim redistribution rights`);
  }
}
if (/\/(?:Users|home)\//.test(auditBytes.toString("utf8"))) {
  throw new Error("Catalog source audit contains an absolute local path");
}

const contractAjv = new Ajv2020({ allErrors: true, strict: true });
addFormats(contractAjv);
contractAjv.compile(v2Schema);

console.log(
  `Validated ${pluginDirectories.length} plugin manifest(s), exact Contracts ${CONTRACT_VERSION} v2 snapshot, and FEAT-129 38-Skill Catalog metadata.`,
);
