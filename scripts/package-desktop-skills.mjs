import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { lstat, mkdir, mkdtemp, readFile, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { createStoredZip, isSafeRelativePath } from "./lib/deterministic-zip.mjs";

const execFileAsync = promisify(execFile);
const SOURCE_PATH = "plugins/yijie-desktop-skills/bundle-source.json";
const CONTRACT_SCHEMA_PATH = "contracts/skill-bundle-manifest-v2.schema.json";
const CATALOG_AUDIT_PATH = "docs/provenance/source-audits/FEAT-129-catalog-38-source-audit.json";
const DEFAULT_OUTPUT = "dist/skill-packages";

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function assertUnique(values, label) {
  const seen = new Set();
  for (const value of values) {
    if (seen.has(value)) throw new Error(`Duplicate ${label}: ${value}`);
    seen.add(value);
  }
}

function packageTreeSha256(skills) {
  const digest = createHash("sha256");
  for (const skill of [...skills].sort((left, right) => left.id.localeCompare(right.id))) {
    for (const entry of [...skill.entries].sort((left, right) => left.name.localeCompare(right.name))) {
      for (const value of [skill.id, entry.name, sha256(entry.content)]) {
        const bytes = Buffer.from(value, "utf8");
        const size = Buffer.alloc(8);
        size.writeBigUInt64BE(BigInt(bytes.length));
        digest.update(size);
        digest.update(bytes);
      }
    }
  }
  return digest.digest("hex");
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value !== null && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

async function readPackagedEntries(skill) {
  const sourceRoot = path.resolve(skill.source_dir);
  const entries = [];
  for (const relative of [...skill.package_files].sort()) {
    if (!isSafeRelativePath(relative)) throw new Error(`Unsafe package file: ${relative}`);
    const absolute = path.resolve(sourceRoot, relative);
    if (!absolute.startsWith(`${sourceRoot}${path.sep}`)) throw new Error(`Package file escaped source root: ${relative}`);
    const stat = await lstat(absolute);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`Package file is not a regular file: ${relative}`);
    entries.push({ name: relative.split(path.sep).join("/"), content: await readFile(absolute) });
  }
  if (!entries.some(({ name }) => name === skill.entrypoint)) {
    throw new Error(`${skill.id} package does not include ${skill.entrypoint}`);
  }
  return entries;
}

async function repositoryRevision(inputPaths) {
  const [{ stdout: revision }, { stdout: status }] = await Promise.all([
    execFileAsync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }),
    execFileAsync("git", ["status", "--porcelain", "--", ...inputPaths], { encoding: "utf8" }),
  ]);
  return {
    revision_kind: status.trim() === "" ? "git-commit" : "working-tree",
    revision: revision.trim(),
  };
}

function publicSkillMetadata(skill, packaged) {
  const metadata = {
    id: skill.id,
    runtime_name: skill.runtime_name,
    category: skill.category,
    order: skill.order,
    display_name: skill.display_name,
    description: skill.description,
    version: skill.version,
    catalog_entry_mode: skill.catalog_entry_mode,
    icon: skill.icon,
    risk: skill.risk,
    provenance: skill.provenance,
    license: skill.license,
    capabilities: skill.capabilities,
    release: skill.release,
  };
  if (skill.catalog_entry_mode === "catalog-only") return metadata;
  if (!packaged) throw new Error(`${skill.id} is bundled but has no packaged content`);
  const { entries, archive } = packaged;
  return {
    ...metadata,
    entrypoint: skill.entrypoint,
    provenance: {
      ...skill.provenance,
      source_sha256: packageTreeSha256([{ id: skill.id, entries }]),
    },
    archive: {
      path: `packages/${skill.id}-${skill.version}.zip`,
      sha256: sha256(archive),
      compressed_size_bytes: archive.length,
      uncompressed_size_bytes: entries.reduce((total, entry) => total + entry.content.length, 0),
      file_count: entries.length,
    },
  };
}

export async function buildDesktopSkillBundle(outputDirectory = DEFAULT_OUTPUT, options = {}) {
  const source = JSON.parse(await readFile(SOURCE_PATH, "utf8"));
  const pluginRoot = path.dirname(SOURCE_PATH);
  const distributionChannel = options.distributionChannel ?? source.distribution_channel;
  if (!source.authorized_distribution_channels?.includes(distributionChannel)) {
    throw new Error(`Distribution channel is not authorized by bundle source: ${distributionChannel}`);
  }
  assertUnique(source.skills.map(({ id }) => id), "Skill id");
  assertUnique(source.skills.map(({ runtime_name: runtimeName }) => runtimeName), "Runtime name");
  const builtSkills = [];
  for (const skill of source.skills) {
    if (skill.catalog_entry_mode === "catalog-only") {
      builtSkills.push({ source: skill, packaged: null });
      continue;
    }
    if (skill.catalog_entry_mode !== "bundled") {
      throw new Error(`${skill.id} has unsupported catalog_entry_mode: ${skill.catalog_entry_mode}`);
    }
    const entries = await readPackagedEntries(skill);
    const archive = createStoredZip(entries);
    builtSkills.push({ source: skill, packaged: { entries, archive } });
  }

  const revision = await repositoryRevision([
    SOURCE_PATH,
    pluginRoot,
    "vendor/feat-129",
    "contracts/lock.json",
    CONTRACT_SCHEMA_PATH,
    CATALOG_AUDIT_PATH,
    "scripts/package-desktop-skills.mjs",
    "scripts/lib/deterministic-zip.mjs",
  ]);
  const publicSkills = builtSkills.map(({ source: skill, packaged }) => publicSkillMetadata(skill, packaged));
  const manifest = {
    schema_version: source.schema_version,
    bundle_id: source.bundle_id,
    bundle_version: source.bundle_version,
    distribution_channel: distributionChannel,
    source: {
      repository: source.repository,
      ...revision,
      tree_sha256: sha256(Buffer.from(canonicalJson(publicSkills), "utf8")),
    },
    skills: publicSkills,
  };

  const schema = JSON.parse(await readFile(CONTRACT_SCHEMA_PATH, "utf8"));
  const ajv = new Ajv2020({ strict: true, allErrors: true });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  if (!validate(manifest)) throw new Error(`Generated bundle manifest is invalid: ${ajv.errorsText(validate.errors)}`);

  const parent = path.dirname(outputDirectory);
  await mkdir(parent, { recursive: true });
  const staging = await mkdtemp(path.join(parent, ".skill-packages-"));
  try {
    await mkdir(path.join(staging, "packages"), { recursive: true });
    for (const { source: skill, packaged } of builtSkills) {
      if (packaged) {
        await writeFile(path.join(staging, "packages", `${skill.id}-${skill.version}.zip`), packaged.archive);
      }
    }
    await writeFile(path.join(staging, "bundle-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
    await rm(outputDirectory, { recursive: true, force: true });
    await rename(staging, outputDirectory);
  } catch (error) {
    await rm(staging, { recursive: true, force: true });
    throw error;
  }
  return manifest;
}

const invokedPath = process.argv[1] ? path.resolve(process.argv[1]) : "";
if (invokedPath === fileURLToPath(import.meta.url)) {
  const outputIndex = process.argv.indexOf("--output");
  const channelIndex = process.argv.indexOf("--channel");
  const outputDirectory = outputIndex >= 0 ? process.argv[outputIndex + 1] : DEFAULT_OUTPUT;
  const distributionChannel = channelIndex >= 0 ? process.argv[channelIndex + 1] : undefined;
  if (!outputDirectory) throw new Error("--output requires a directory");
  if (channelIndex >= 0 && !distributionChannel) throw new Error("--channel requires a value");
  const manifest = await buildDesktopSkillBundle(outputDirectory, { distributionChannel });
  const archiveCount = manifest.skills.filter(({ archive }) => archive).length;
  console.log(
    `Generated ${manifest.skills.length} catalog entries and ${archiveCount} deterministic Desktop Skill archive(s) in ${outputDirectory} (${manifest.distribution_channel}).`,
  );
}
