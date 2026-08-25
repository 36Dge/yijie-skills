import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { buildDesktopSkillBundle } from "../scripts/package-desktop-skills.mjs";

const CONTRACT_REVISION = "164b14f609537d727a52326832da04430aecc4ab";
const CATEGORY_COUNTS = {
  "sourcing-selection": 5,
  "market-research": 9,
  "content-marketing": 7,
  "traffic-advertising": 9,
  "store-operations": 8,
};

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function readLocalEntries(archive) {
  const entries = [];
  let offset = 0;
  while (offset + 4 <= archive.length && archive.readUInt32LE(offset) === 0x04034b50) {
    const size = archive.readUInt32LE(offset + 18);
    const nameLength = archive.readUInt16LE(offset + 26);
    const extraLength = archive.readUInt16LE(offset + 28);
    const nameStart = offset + 30;
    const dataStart = nameStart + nameLength + extraLength;
    const dataEnd = dataStart + size;
    assert.ok(dataEnd <= archive.length);
    entries.push(archive.subarray(nameStart, nameStart + nameLength).toString("utf8"));
    offset = dataEnd;
  }
  return entries;
}

test("FEAT-129 deterministically emits 38 Catalog entries and one reviewed archive", async () => {
  const temporaryRoot = await mkdtemp(path.join(os.tmpdir(), "yijie-desktop-skill-bundle-"));
  const firstOutput = path.join(temporaryRoot, "first");
  const secondOutput = path.join(temporaryRoot, "second");
  try {
    const firstManifest = await buildDesktopSkillBundle(firstOutput);
    const secondManifest = await buildDesktopSkillBundle(secondOutput);
    assert.deepEqual(secondManifest, firstManifest);
    assert.equal(firstManifest.schema_version, 2);
    assert.equal(firstManifest.bundle_version, "0.2.0");
    assert.equal(firstManifest.distribution_channel, "local-development");
    assert.ok(["working-tree", "git-commit"].includes(firstManifest.source.revision_kind));
    assert.match(firstManifest.source.tree_sha256, /^[a-f0-9]{64}$/);
    assert.equal(firstManifest.skills.length, 38);

    const counts = Object.fromEntries(Object.keys(CATEGORY_COUNTS).map((category) => [category, 0]));
    for (const skill of firstManifest.skills) counts[skill.category] += 1;
    assert.deepEqual(counts, CATEGORY_COUNTS);

    const installable = firstManifest.skills.filter(({ release }) => release.catalog_status === "installable");
    const blocked = firstManifest.skills.filter(({ release }) => release.catalog_status === "blocked");
    assert.equal(installable.length, 1);
    assert.equal(blocked.length, 37);
    for (const skill of blocked) {
      assert.equal(skill.catalog_entry_mode, "catalog-only");
      assert.equal(skill.release.blocked_reason, "license_unverified");
      assert.equal(skill.license.authorization_scope, "none");
      assert.equal("entrypoint" in skill, false);
      assert.equal("archive" in skill, false);
    }

    const [copywriting] = installable;
    assert.equal(copywriting.id, "yijie.content-marketing.copywriting");
    assert.equal(copywriting.runtime_name, "copywriting");
    assert.equal(copywriting.version, "0.1.0");
    assert.equal(copywriting.catalog_entry_mode, "bundled");
    assert.deepEqual(copywriting.icon, { registry: "yj-icon-v1", key: "edit" });
    assert.deepEqual(copywriting.capabilities, {
      execution_mode: "model-only",
      network: "none",
      filesystem: "none",
      required_tools: [],
    });
    assert.equal(copywriting.license.authorization_scope, "local-development");

    const firstArchive = await readFile(path.join(firstOutput, copywriting.archive.path));
    const secondArchive = await readFile(path.join(secondOutput, copywriting.archive.path));
    assert.deepEqual(secondArchive, firstArchive);
    assert.equal(sha256(firstArchive), copywriting.archive.sha256);
    assert.deepEqual(readLocalEntries(firstArchive), [
      "NOTICE.md",
      "SKILL.md",
      "agents/openai.yaml",
      "examples/input-001.json",
      "examples/output-001.md",
    ]);
    assert.deepEqual(await readdir(path.join(firstOutput, "packages")), [
      "yijie.content-marketing.copywriting-0.1.0.zip",
    ]);

    const schema = JSON.parse(await readFile("contracts/skill-bundle-manifest-v2.schema.json", "utf8"));
    const ajv = new Ajv2020({ strict: true, allErrors: true });
    addFormats(ajv);
    const validate = ajv.compile(schema);
    assert.equal(validate(firstManifest), true, JSON.stringify(validate.errors));
    assert.deepEqual(
      await readFile(path.join(firstOutput, "bundle-manifest.json")),
      await readFile(path.join(secondOutput, "bundle-manifest.json")),
    );
  } finally {
    await rm(temporaryRoot, { recursive: true, force: true });
  }
});

test("38-Skill audit keeps upstream contents and redistribution outside the repository", async () => {
  const audit = JSON.parse(
    await readFile("docs/provenance/source-audits/FEAT-129-catalog-38-source-audit.json", "utf8"),
  );
  assert.equal(audit.entries.length, 38);
  assert.equal(new Set(audit.entries.map(({ runtime_name: runtimeName }) => runtimeName)).size, 38);
  assert.equal(audit.source_disclosure.content_included, false);
  assert.equal(audit.source_disclosure.absolute_local_paths_included, false);
  assert.equal(audit.source_disclosure.owner_marker_is_license_evidence, false);
  assert.equal(audit.decisions.source_content_copied_for_catalog_only_entries, false);
  assert.equal(audit.decisions.desktop_release_status, "blocked-pending-license-and-source-proof");
  for (const entry of audit.entries) {
    assert.deepEqual(entry.license_files, []);
    assert.equal(entry.redistribution_status, "blocked");
    assert.match(entry.observed_skill_md_sha256, /^[a-f0-9]{64}$/);
  }
});

test("copywriting source audit does not treat upstream cache metadata as a license", async () => {
  const audit = JSON.parse(
    await readFile("docs/provenance/source-audits/FEAT-129-copywriting-source-audit.json", "utf8"),
  );
  assert.equal(audit.observed.runtime_name, "copywriting");
  assert.equal(audit.observed.version, "0.0.94");
  assert.deepEqual(audit.observed.license_files, []);
  assert.deepEqual(audit.observed.declared_external_dependencies, []);
  assert.equal(audit.decisions.source_content_copied, false);
  assert.equal(audit.decisions.upstream_redistribution_status, "blocked");
  assert.equal(audit.decisions.local_candidate_status, "model-only-eligible");
});

test("vendored v1 and v2 contract snapshots remain digest locked to Contracts 0.5.1", async () => {
  const lock = JSON.parse(await readFile("contracts/lock.json", "utf8"));
  for (const artifact of Object.values(lock.artifacts)) {
    const snapshot = await readFile(artifact.snapshot_path);
    assert.equal(sha256(snapshot), artifact.sha256);
  }
  assert.equal(lock.contracts_version, "0.5.1");
  assert.equal(lock.source_revision_kind, "git-commit");
  assert.equal(lock.source_revision, CONTRACT_REVISION);
  assert.equal(
    lock.artifacts.skill_bundle_manifest_v2.sha256,
    "39a898111ba3dcae2f369fdcb571a2e892830d1d0a57c90ab6210a0ab897a649",
  );
});
