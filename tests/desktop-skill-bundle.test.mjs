import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { buildDesktopSkillBundle } from "../scripts/package-desktop-skills.mjs";

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

test("FEAT-129 packages one deterministic, model-only, locally authorized Skill", async () => {
  const temporaryRoot = await mkdtemp(path.join(os.tmpdir(), "yijie-desktop-skill-bundle-"));
  const firstOutput = path.join(temporaryRoot, "first");
  const secondOutput = path.join(temporaryRoot, "second");
  try {
    const firstManifest = await buildDesktopSkillBundle(firstOutput);
    const secondManifest = await buildDesktopSkillBundle(secondOutput);
    assert.deepEqual(secondManifest, firstManifest);
    assert.equal(firstManifest.distribution_channel, "local-development");
    assert.ok(["working-tree", "git-commit"].includes(firstManifest.source.revision_kind));
    assert.equal(firstManifest.skills.length, 1);

    const [skill] = firstManifest.skills;
    assert.equal(skill.id, "yijie.content-marketing.copywriting");
    assert.equal(skill.runtime_name, "copywriting");
    assert.equal(skill.version, "0.1.0");
    assert.deepEqual(skill.icon, { registry: "yj-icon-v1", key: "edit" });
    assert.deepEqual(skill.capabilities, {
      execution_mode: "model-only",
      network: "none",
      filesystem: "none",
      required_tools: [],
    });
    assert.equal(skill.license.authorization_scope, "local-development");
    assert.equal(skill.release.catalog_status, "installable");

    const firstArchive = await readFile(path.join(firstOutput, skill.archive.path));
    const secondArchive = await readFile(path.join(secondOutput, skill.archive.path));
    assert.deepEqual(secondArchive, firstArchive);
    assert.equal(sha256(firstArchive), skill.archive.sha256);
    assert.deepEqual(readLocalEntries(firstArchive), [
      "NOTICE.md",
      "SKILL.md",
      "agents/openai.yaml",
      "examples/input-001.json",
      "examples/output-001.md",
    ]);

    const schema = JSON.parse(await readFile("contracts/skill-bundle-manifest-v1.schema.json", "utf8"));
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

test("source audit selects copywriting without treating upstream cache metadata as a license", async () => {
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

test("vendored Skill bundle contract snapshot remains digest locked", async () => {
  const lock = JSON.parse(await readFile("contracts/lock.json", "utf8"));
  const snapshot = await readFile(lock.artifacts.skill_bundle_manifest_v1.snapshot_path);
  assert.equal(sha256(snapshot), lock.artifacts.skill_bundle_manifest_v1.sha256);
  assert.equal(lock.contracts_version, "0.5.0");
  assert.equal(lock.source_revision_kind, "git-commit");
  assert.equal(lock.source_revision, "d6dff903e0c12b6a5e69599df1e33ef46d8bea6b");
});
