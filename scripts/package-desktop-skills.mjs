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
const CONTRACT_SCHEMA_PATH = "contracts/skill-bundle-manifest-v1.schema.json";
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

function treeSha256(skills) {
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

async function readPackagedEntries(pluginRoot, skill) {
  const sourceRoot = path.resolve(pluginRoot, skill.source_dir);
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

function publicSkillMetadata(skill, entries, archive) {
  const sourceDigest = treeSha256([{ id: skill.id, entries }]);
  return {
    id: skill.id,
    runtime_name: skill.runtime_name,
    category: skill.category,
    order: skill.order,
    display_name: skill.display_name,
    description: skill.description,
    version: skill.version,
    entrypoint: skill.entrypoint,
    icon: skill.icon,
    risk: skill.risk,
    provenance: { ...skill.provenance, source_sha256: sourceDigest },
    license: skill.license,
    capabilities: skill.capabilities,
    archive: {
      path: `packages/${skill.id}-${skill.version}.zip`,
      sha256: sha256(archive),
      compressed_size_bytes: archive.length,
      uncompressed_size_bytes: entries.reduce((total, entry) => total + entry.content.length, 0),
      file_count: entries.length,
    },
    release: skill.release,
  };
}

export async function buildDesktopSkillBundle(outputDirectory = DEFAULT_OUTPUT) {
  const source = JSON.parse(await readFile(SOURCE_PATH, "utf8"));
  const pluginRoot = path.dirname(SOURCE_PATH);
  assertUnique(source.skills.map(({ id }) => id), "Skill id");
  assertUnique(source.skills.map(({ runtime_name: runtimeName }) => runtimeName), "Runtime name");
  const builtSkills = [];
  for (const skill of source.skills) {
    const entries = await readPackagedEntries(pluginRoot, skill);
    const archive = createStoredZip(entries);
    builtSkills.push({ source: skill, entries, archive });
  }

  const revision = await repositoryRevision([
    SOURCE_PATH,
    pluginRoot,
    CONTRACT_SCHEMA_PATH,
    "scripts/package-desktop-skills.mjs",
    "scripts/lib/deterministic-zip.mjs",
  ]);
  const manifest = {
    schema_version: source.schema_version,
    bundle_id: source.bundle_id,
    bundle_version: source.bundle_version,
    distribution_channel: source.distribution_channel,
    source: {
      repository: source.repository,
      ...revision,
      tree_sha256: treeSha256(
        builtSkills.map(({ source: skill, entries }) => ({ id: skill.id, entries })),
      ),
    },
    skills: builtSkills.map(({ source: skill, entries, archive }) =>
      publicSkillMetadata(skill, entries, archive),
    ),
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
    for (const { source: skill, archive } of builtSkills) {
      await writeFile(path.join(staging, "packages", `${skill.id}-${skill.version}.zip`), archive);
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
  const outputDirectory = outputIndex >= 0 ? process.argv[outputIndex + 1] : DEFAULT_OUTPUT;
  if (!outputDirectory) throw new Error("--output requires a directory");
  const manifest = await buildDesktopSkillBundle(outputDirectory);
  console.log(
    `Packaged ${manifest.skills.length} deterministic Desktop Skill archive(s) in ${outputDirectory} (${manifest.distribution_channel}).`,
  );
}
