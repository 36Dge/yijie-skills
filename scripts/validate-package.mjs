import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { parse } from "smol-toml";

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
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

const [lockBytes, contractSchemaBytes, bundleSourceBytes] = await Promise.all([
  readFile("contracts/lock.json"),
  readFile("contracts/skill-bundle-manifest-v1.schema.json"),
  readFile("plugins/yijie-desktop-skills/bundle-source.json"),
]);
const lock = JSON.parse(lockBytes);
const contractSchema = JSON.parse(contractSchemaBytes);
const bundleSource = JSON.parse(bundleSourceBytes);
const locked = lock.artifacts.skill_bundle_manifest_v1;
if (
  lock.contracts_version !== "0.5.0" ||
  lock.source_revision_kind !== "git-commit" ||
  lock.source_revision !== "d6dff903e0c12b6a5e69599df1e33ef46d8bea6b"
) {
  throw new Error("FEAT-129 contracts lock must identify the exact immutable 0.5.0 candidate");
}
if (sha256(contractSchemaBytes) !== locked.sha256) throw new Error("Vendored Skill bundle schema digest drifted");
if (bundleSource.bundle_id !== "yijie.desktop.skill-packages" || bundleSource.distribution_channel !== "local-development") {
  throw new Error("Desktop Skill source must remain a local-development bundle candidate");
}
if (bundleSource.skills.length !== 1) throw new Error("FEAT-129 first bundle must contain exactly one reviewed Skill");
const [skill] = bundleSource.skills;
if (
  skill.id !== "yijie.content-marketing.copywriting" ||
  skill.runtime_name !== "copywriting" ||
  skill.icon?.key !== "edit" ||
  skill.risk?.level !== "medium"
) {
  throw new Error("copywriting stable metadata drifted");
}
if (
  skill.capabilities.execution_mode !== "model-only" ||
  skill.capabilities.network !== "none" ||
  skill.capabilities.filesystem !== "none" ||
  skill.capabilities.required_tools.length !== 0
) {
  throw new Error("copywriting must remain model-only with no external dependency");
}
if (
  skill.license.authorization_scope !== "local-development" ||
  bundleSource.distribution_channel === "desktop-release"
) {
  throw new Error("unreleased copywriting candidate cannot claim Desktop distribution authorization");
}
for (const requiredFile of [
  "NOTICE.md",
  "SKILL.md",
  "agents/openai.yaml",
  "examples/input-001.json",
  "examples/output-001.md",
]) {
  if (!skill.package_files.includes(requiredFile)) {
    throw new Error(`copywriting package is missing required reviewed file: ${requiredFile}`);
  }
}

const contractAjv = new Ajv2020({ allErrors: true, strict: true });
addFormats(contractAjv);
contractAjv.compile(contractSchema);

console.log(`Validated ${pluginDirectories.length} plugin manifest(s), marketplace entries, schema snapshot, and FEAT-129 source metadata.`);
