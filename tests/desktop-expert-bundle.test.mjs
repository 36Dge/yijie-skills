import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { buildDesktopSkillBundle } from "../scripts/package-desktop-skills.mjs";
import { knowledgeManifestDigest } from "../contracts/experts-canonical.gen.mjs";

const sourcePath = "plugins/yijie-desktop-skills/experts/bundle-source.json";
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");

// Only reads normal archives produced by the canonical builder; no malformed fixtures.
function archiveEntries(archive) {
  const entries = new Map();
  let offset = 0;
  while (offset + 30 <= archive.length && archive.readUInt32LE(offset) === 0x04034b50) {
    assert.equal(archive.readUInt16LE(offset + 8), 0);
    const size = archive.readUInt32LE(offset + 18);
    const nameLength = archive.readUInt16LE(offset + 26);
    const extraLength = archive.readUInt16LE(offset + 28);
    const name = archive.subarray(offset + 30, offset + 30 + nameLength).toString("utf8");
    const start = offset + 30 + nameLength + extraLength;
    assert.ok(start + size <= archive.length);
    assert.equal(entries.has(name), false);
    entries.set(name, archive.subarray(start, start + size));
    offset = start + size;
  }
  return entries;
}

test("v3 expert local candidate preserves all 38 ordinary package bytes and emits repeatable reviewed expert authority", async () => {
  const temporary = await mkdtemp(path.join(os.tmpdir(), "yijie-expert-bundle-"));
  try {
    const baseDir = path.join(temporary, "v2");
    const firstDir = path.join(temporary, "v3-first");
    const secondDir = path.join(temporary, "v3-second");
    const base = await buildDesktopSkillBundle(baseDir);
    const first = await buildDesktopSkillBundle(firstDir, { sourcePath });
    const second = await buildDesktopSkillBundle(secondDir, { sourcePath });
    assert.equal(base.schema_version, 2);
    assert.equal(first.schema_version, 3);
    assert.equal(first.skills.length, 39);
    assert.deepEqual(first, second);
    assert.deepEqual(first.skills.filter(({ asset_kind }) => asset_kind !== "expert_resources"), base.skills);
    for (const skill of base.skills) {
      assert.deepEqual(await readFile(path.join(baseDir, skill.archive.path)), await readFile(path.join(firstDir, skill.archive.path)));
    }
    const expert = first.skills.find(({ asset_kind }) => asset_kind === "expert_resources");
    assert.equal(expert.id, "yijie.experts.jd-ops-expert");
    assert.equal(expert.expert.runtime_projection, "expert_only");
    assert.equal(expert.expert.platform, "jd");
    assert.equal(expert.license.redistribution_status, "unverified");
    assert.equal(expert.license.authorization_scope, "local-development");
    assert.equal(expert.capabilities.network, "none");
    assert.equal(expert.capabilities.filesystem, "read");
    assert.deepEqual(expert.capabilities.required_tools, []);
    const archive = await readFile(path.join(firstDir, expert.archive.path));
    assert.equal(hash(archive), expert.archive.sha256);
    assert.deepEqual(archive, await readFile(path.join(secondDir, expert.archive.path)));
    const entries = archiveEntries(archive);
    assert.equal(entries.size, expert.archive.file_count);
    assert.ok(entries.has("SKILL.md") && entries.has("NOTICE.md"));
    assert.equal([...entries.keys()].filter((name) => name.endsWith("SKILL.md")).length, 1);
    for (const resource of [expert.expert.role_resource, ...expert.expert.knowledge_resources]) {
      assert.ok(entries.has(resource.path), resource.path);
      assert.equal(hash(entries.get(resource.path)), resource.sha256, resource.path);
      assert.equal(entries.get(resource.path).length, resource.bytes, resource.path);
    }
    const authorityBytes = await readFile(path.join(firstDir, "authority.json"));
    assert.deepEqual(authorityBytes, await readFile(path.join(secondDir, "authority.json")));
    const authority = JSON.parse(authorityBytes);
    assert.equal(authority.release, false);
    assert.equal(authority.manifest_sha256, hash(await readFile(path.join(firstDir, "bundle-manifest.json"))));
    assert.deepEqual(authority.source, first.source);
    const record = authority.experts[0];
    assert.equal(record.knowledge_manifest_sha256, knowledgeManifestDigest(expert.expert.knowledge_resources));
    assert.equal(record.local_use_authorization.evidence_sha256, hash(await readFile(record.local_use_authorization.evidence_reference)));
    assert.equal(record.content_review.sha256, hash(await readFile(record.content_review.path)));
    assert.equal(authority.contracts_candidate.sha256, hash(await readFile(authority.contracts_candidate.path)));
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});

test("expert candidate declines an unsupported release-channel request before creating output", async () => {
  await assert.rejects(
    buildDesktopSkillBundle("dist/unused-expert-release", { sourcePath, distributionChannel: "desktop-release" }),
    /Distribution channel is not authorized/,
  );
});
