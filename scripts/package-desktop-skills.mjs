import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { lstat, mkdir, mkdtemp, readFile, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { createStoredZip, isSafeRelativePath } from "./lib/deterministic-zip.mjs";
import { knowledgeManifestDigest } from "../contracts/experts-canonical.gen.mjs";

const execFileAsync = promisify(execFile);
const SOURCE_PATH = "plugins/yijie-desktop-skills/bundle-source.json";
const CONTRACT_SCHEMA_PATH = "contracts/skill-bundle-manifest-v2.schema.json";
const EXPERT_CONTRACT_SCHEMA_PATH = "contracts/skill-bundle-manifest-v3.schema.json";
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

async function verifyExpertContentReview(skill, entries) {
  const reference = skill.provenance.source_reference;
  if (!isSafeRelativePath(reference)) throw new Error(`${skill.id} has no relative content review`);
  const review = JSON.parse(await readFile(reference, "utf8"));
  if (review.source_root !== skill.source_dir || review.content_version !== skill.version ||
      review.decisions?.local_development_authorized !== true || review.decisions?.desktop_redistribution_verified !== false ||
      review.files?.length !== entries.length) {
    throw new Error(`${skill.id} content review does not match its local candidate`);
  }
  assertUnique(review.files.map(({ path: relative }) => relative), "review file path");
  for (const entry of entries) {
    const evidence = review.files.find(({ path: relative }) => relative === entry.name);
    if (!evidence || evidence.sha256 !== sha256(entry.content) || evidence.bytes !== entry.content.length) {
      throw new Error(`${skill.id} reviewed content drifted: ${entry.name}`);
    }
  }
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
  if (skill.asset_kind === "expert_resources") {
    const resource = (relative) => {
      const entry = entries.find(({ name }) => name === relative);
      if (!entry) throw new Error(`${skill.id} resource is not packaged: ${relative}`);
      return { path: relative, sha256: sha256(entry.content), bytes: entry.content.length };
    };
    const knowledge = skill.expert.knowledge_resources.map((entry) => ({
      ...entry,
      ...resource(entry.path),
    }));
    assertUnique(knowledge.map(({ id }) => id), "knowledge resource id");
    assertUnique([skill.expert.role_resource.path, ...knowledge.map(({ path: resourcePath }) => resourcePath)], "expert resource path");
    // Use the generated Contracts implementation; this is also checked by consumers.
    knowledgeManifestDigest(knowledge);
    metadata.asset_kind = "expert_resources";
    metadata.expert = {
      ...skill.expert,
      role_resource: resource(skill.expert.role_resource.path),
      knowledge_resources: knowledge,
    };
  } else if (skill.asset_kind !== undefined) {
    metadata.asset_kind = skill.asset_kind;
  }
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
  const sourcePath = options.sourcePath ?? SOURCE_PATH;
  const source = JSON.parse(await readFile(sourcePath, "utf8"));
  const sourceInputs = [sourcePath];
  if (source.base_source !== undefined) {
    if (source.schema_version !== 3 || source.base_source !== SOURCE_PATH) {
      throw new Error("Expert local candidate must extend the canonical existing Skill source");
    }
    const base = JSON.parse(await readFile(SOURCE_PATH, "utf8"));
    if (base.schema_version !== 2) throw new Error("Expert candidate expects the unchanged v2 base source");
    source.skills = [...base.skills, ...source.skills];
    sourceInputs.push(SOURCE_PATH);
  }
  const schemaPath = source.schema_version === 3 ? EXPERT_CONTRACT_SCHEMA_PATH : CONTRACT_SCHEMA_PATH;
  const pluginRoot = path.dirname(SOURCE_PATH);
  const distributionChannel = options.distributionChannel ?? source.distribution_channel;
  if (!source.authorized_distribution_channels?.includes(distributionChannel)) {
    throw new Error(`Distribution channel is not authorized by bundle source: ${distributionChannel}`);
  }
  if (source.skills.some(({ asset_kind: kind }) => kind === "expert_resources")) {
    if (source.schema_version !== 3 || distributionChannel !== "local-development") {
      throw new Error("Expert candidates require v3 and explicit local-development authorization");
    }
    const candidate = JSON.parse(await readFile("contracts/experts.candidate.json", "utf8"));
    if (candidate.release !== false || candidate.consumer !== "skills") throw new Error("Missing local Contracts expert candidate");
    for (const artifact of candidate.consumer_generated) {
      if (sha256(await readFile(artifact.path)) !== artifact.sha256) throw new Error(`Contracts candidate drift: ${artifact.path}`);
    }
    for (const expert of source.skills.filter(({ asset_kind: kind }) => kind === "expert_resources")) {
      const reference = expert.expert.local_use_authorization?.evidence_reference;
      if (expert.expert.local_use_authorization?.status !== "local-use-authorized" || !isSafeRelativePath(reference)) {
        throw new Error(`${expert.id} lacks explicit local-use evidence`);
      }
      await readFile(reference);
      sourceInputs.push(reference);
    }
  }
  assertUnique(source.skills.map(({ id }) => id), "Skill id");
  assertUnique(source.skills.map(({ runtime_name: runtimeName }) => runtimeName), "Runtime name");
  assertUnique(source.skills.filter(({ asset_kind }) => asset_kind === "expert_resources")
    .map(({ expert, version }) => `${expert.expert_id}@${version}`), "expert version identity");
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
    if (skill.asset_kind === "expert_resources") {
      await verifyExpertContentReview(skill, entries);
      sourceInputs.push(skill.provenance.source_reference);
    }
    const archive = createStoredZip(entries);
    builtSkills.push({ source: skill, packaged: { entries, archive } });
  }

  const revision = await repositoryRevision([
    ...sourceInputs,
    pluginRoot,
    "vendor/feat-129",
    "contracts/lock.json",
    schemaPath,
    ...(source.schema_version === 3 ? ["contracts/experts.candidate.json", "contracts/experts-canonical.gen.mjs"] : []),
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

  const schema = JSON.parse(await readFile(schemaPath, "utf8"));
  const ajv = new Ajv2020({ strict: true, allErrors: true });
  addFormats(ajv);
  if (source.schema_version === 3) {
    ajv.addSchema(JSON.parse(await readFile(CONTRACT_SCHEMA_PATH, "utf8")));
  }
  const validate = ajv.compile(schema);
  if (!validate(manifest)) throw new Error(`Generated bundle manifest is invalid: ${ajv.errorsText(validate.errors)}`);

  const manifestBytes = Buffer.from(`${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  let authority = null;
  if (source.schema_version === 3) {
    const experts = publicSkills.filter(({ asset_kind: kind }) => kind === "expert_resources");
    authority = {
      schema_version: 1,
      feature: "FEAT-158",
      release: false,
      distribution_channel: distributionChannel,
      bundle_id: manifest.bundle_id,
      bundle_version: manifest.bundle_version,
      manifest_path: "bundle-manifest.json",
      manifest_sha256: sha256(manifestBytes),
      source: manifest.source,
      source_definition: { path: sourcePath, sha256: sha256(await readFile(sourcePath)) },
      contracts_candidate: { path: "contracts/experts.candidate.json", sha256: sha256(await readFile("contracts/experts.candidate.json")) },
      experts: await Promise.all(experts.map(async (entry) => ({
        installation_id: entry.id,
        expert_id: entry.expert.expert_id,
        source_id: entry.expert.source_id,
        version: entry.version,
        archive: entry.archive,
        role_resource: entry.expert.role_resource,
        knowledge_manifest_sha256: knowledgeManifestDigest(entry.expert.knowledge_resources),
        knowledge_resources: entry.expert.knowledge_resources,
        local_use_authorization: {
          ...entry.expert.local_use_authorization,
          evidence_sha256: sha256(await readFile(entry.expert.local_use_authorization.evidence_reference)),
        },
        content_review: { path: entry.provenance.source_reference, sha256: sha256(await readFile(entry.provenance.source_reference)) },
      }))),
    };
  }

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
    await writeFile(path.join(staging, "bundle-manifest.json"), manifestBytes);
    if (authority) await writeFile(path.join(staging, "authority.json"), `${JSON.stringify(authority, null, 2)}\n`);
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
  const sourceIndex = process.argv.indexOf("--source");
  const outputDirectory = outputIndex >= 0 ? process.argv[outputIndex + 1] : DEFAULT_OUTPUT;
  const distributionChannel = channelIndex >= 0 ? process.argv[channelIndex + 1] : undefined;
  const sourcePath = sourceIndex >= 0 ? process.argv[sourceIndex + 1] : undefined;
  if (!outputDirectory) throw new Error("--output requires a directory");
  if (channelIndex >= 0 && !distributionChannel) throw new Error("--channel requires a value");
  if (sourceIndex >= 0 && (!sourcePath || outputIndex < 0)) throw new Error("--source requires a value and an explicit --output candidate directory");
  const manifest = await buildDesktopSkillBundle(outputDirectory, { distributionChannel, sourcePath });
  const archiveCount = manifest.skills.filter(({ archive }) => archive).length;
  console.log(
    `Generated ${manifest.skills.length} catalog entries and ${archiveCount} deterministic Desktop Skill archive(s) in ${outputDirectory} (${manifest.distribution_channel}).`,
  );
}
