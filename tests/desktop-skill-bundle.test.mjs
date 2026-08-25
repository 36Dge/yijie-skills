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
const LICENSE_EXPRESSION = "LicenseRef-YiJie-Desktop-Distribution-Owner-Attestation";
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

test("FEAT-129 deterministically emits 38 installable archives for local and Desktop release", async () => {
  const temporaryRoot = await mkdtemp(path.join(os.tmpdir(), "yijie-desktop-skill-bundle-"));
  const localFirst = path.join(temporaryRoot, "local-first");
  const localSecond = path.join(temporaryRoot, "local-second");
  const releaseFirst = path.join(temporaryRoot, "release-first");
  const releaseSecond = path.join(temporaryRoot, "release-second");
  try {
    const localManifest = await buildDesktopSkillBundle(localFirst);
    const localManifestAgain = await buildDesktopSkillBundle(localSecond);
    const releaseManifest = await buildDesktopSkillBundle(releaseFirst, {
      distributionChannel: "desktop-release",
    });
    const releaseManifestAgain = await buildDesktopSkillBundle(releaseSecond, {
      distributionChannel: "desktop-release",
    });
    assert.deepEqual(localManifestAgain, localManifest);
    assert.deepEqual(releaseManifestAgain, releaseManifest);
    assert.equal(localManifest.schema_version, 2);
    assert.equal(localManifest.bundle_version, "0.3.0");
    assert.equal(localManifest.distribution_channel, "local-development");
    assert.equal(releaseManifest.distribution_channel, "desktop-release");
    assert.equal(localManifest.source.tree_sha256, releaseManifest.source.tree_sha256);
    assert.equal(localManifest.skills.length, 38);
    assert.deepEqual(releaseManifest.skills, localManifest.skills);

    const counts = Object.fromEntries(Object.keys(CATEGORY_COUNTS).map((category) => [category, 0]));
    for (const skill of localManifest.skills) {
      counts[skill.category] += 1;
      assert.equal(skill.catalog_entry_mode, "bundled");
      assert.equal(skill.release.catalog_status, "installable");
      assert.equal("blocked_reason" in skill.release, false);
      assert.equal(skill.license.expression, LICENSE_EXPRESSION);
      assert.equal(skill.license.redistribution_status, "verified");
      assert.equal(skill.license.authorization_scope, "desktop-distribution");
      assert.equal(skill.provenance.review_status, "verified");
      assert.ok(skill.archive);
    }
    assert.deepEqual(counts, CATEGORY_COUNTS);

    const bundleSource = JSON.parse(
      await readFile("plugins/yijie-desktop-skills/bundle-source.json", "utf8"),
    );
    const sourceById = new Map(bundleSource.skills.map((skill) => [skill.id, skill]));
    const expectedArchives = localManifest.skills.map(({ archive }) => path.basename(archive.path)).sort();
    assert.deepEqual((await readdir(path.join(localFirst, "packages"))).sort(), expectedArchives);
    assert.equal(expectedArchives.length, 38);

    for (const skill of localManifest.skills) {
      const localArchive = await readFile(path.join(localFirst, skill.archive.path));
      const localArchiveAgain = await readFile(path.join(localSecond, skill.archive.path));
      const releaseArchive = await readFile(path.join(releaseFirst, skill.archive.path));
      assert.deepEqual(localArchiveAgain, localArchive);
      assert.deepEqual(releaseArchive, localArchive);
      assert.equal(sha256(localArchive), skill.archive.sha256);
      assert.deepEqual(readLocalEntries(localArchive), [...sourceById.get(skill.id).package_files].sort());
    }

    const copywriting = localManifest.skills.find(({ runtime_name: runtimeName }) => runtimeName === "copywriting");
    assert.equal(copywriting.id, "yijie.content-marketing.copywriting");
    assert.equal(copywriting.version, "0.1.0");
    assert.deepEqual(copywriting.icon, { registry: "yj-icon-v1", key: "edit" });
    assert.deepEqual(copywriting.capabilities, {
      execution_mode: "model-only",
      network: "none",
      filesystem: "none",
      required_tools: [],
    });

    const schema = JSON.parse(await readFile("contracts/skill-bundle-manifest-v2.schema.json", "utf8"));
    const ajv = new Ajv2020({ strict: true, allErrors: true });
    addFormats(ajv);
    const validate = ajv.compile(schema);
    assert.equal(validate(localManifest), true, JSON.stringify(validate.errors));
    assert.equal(validate(releaseManifest), true, JSON.stringify(validate.errors));
    assert.deepEqual(
      await readFile(path.join(localFirst, "bundle-manifest.json")),
      await readFile(path.join(localSecond, "bundle-manifest.json")),
    );
    assert.deepEqual(
      await readFile(path.join(releaseFirst, "bundle-manifest.json")),
      await readFile(path.join(releaseSecond, "bundle-manifest.json")),
    );
  } finally {
    await rm(temporaryRoot, { recursive: true, force: true });
  }
});

test("ownership attestation exactly authorizes all 38 stable Skill IDs", async () => {
  const [bundle, attestation] = await Promise.all([
    readFile("plugins/yijie-desktop-skills/bundle-source.json", "utf8").then(JSON.parse),
    readFile("docs/provenance/FEAT-129-desktop-distribution-attestation.json", "utf8").then(JSON.parse),
  ]);
  assert.equal(attestation.attestation_id, "FEAT-129-DESKTOP-DISTRIBUTION-2026-08-25");
  assert.equal(attestation.status, "effective");
  assert.equal(attestation.source_ownership_or_control_attested, true);
  assert.equal(attestation.desktop_redistribution_authorized, true);
  assert.deepEqual(attestation.authorization_scopes, ["local-development", "desktop-distribution"]);
  assert.deepEqual(
    [...attestation.skill_ids].sort(),
    bundle.skills.map(({ id }) => id).sort(),
  );
});

test("per-Skill source and security reviews have no release blocker", async () => {
  const [sourceAudit, securityReview] = await Promise.all([
    readFile("docs/provenance/source-audits/FEAT-129-catalog-38-source-audit.json", "utf8").then(JSON.parse),
    readFile("docs/provenance/source-audits/FEAT-129-catalog-38-security-review.json", "utf8").then(JSON.parse),
  ]);
  assert.equal(sourceAudit.entries.length, 38);
  assert.equal(sourceAudit.decisions.installable_entry_count, 38);
  assert.equal(sourceAudit.decisions.catalog_only_entry_count, 0);
  assert.equal(sourceAudit.decisions.desktop_redistribution_authorized, true);
  assert.equal(sourceAudit.decisions.source_or_license_blocker, null);
  for (const entry of sourceAudit.entries) {
    assert.match(entry.observed_skill_md_sha256, /^[a-f0-9]{64}$/);
    assert.match(entry.packaged_skill_md_sha256, /^[a-f0-9]{64}$/);
    assert.match(entry.packaged_tree_sha256, /^[a-f0-9]{64}$/);
    assert.equal(entry.provenance_review_status, "verified");
    assert.equal(entry.redistribution_status, "verified");
    assert.equal(entry.authorization_scope, "desktop-distribution");
  }

  assert.equal(securityReview.entries.length, 38);
  assert.equal(securityReview.all_entries_installable, true);
  assert.equal(securityReview.all_entries_runtime_callable, true);
  assert.equal(securityReview.runtime_permission_controls_remain_enforced, true);
  assert.deepEqual(securityReview.unresolved_release_blockers, []);
  for (const entry of securityReview.entries) {
    assert.equal(entry.review_decision, "approved-with-runtime-controls");
    assert.equal(entry.static_checks.symlinks_detected, false);
    assert.equal(entry.static_checks.credential_material_detected, false);
    assert.equal(entry.static_checks.packaged_scripts_executed_during_review, false);
    assert.equal(entry.installation_authorized, true);
    assert.equal(entry.runtime_discovery_authorized, true);
    assert.equal(entry.desktop_distribution_authorized, true);
  }
});

test("copywriting audit keeps observed upstream content separate from the distributed implementation", async () => {
  const audit = JSON.parse(
    await readFile("docs/provenance/source-audits/FEAT-129-copywriting-source-audit.json", "utf8"),
  );
  assert.equal(audit.observed.runtime_name, "copywriting");
  assert.equal(audit.observed.version, "0.0.94");
  assert.deepEqual(audit.observed.license_files, []);
  assert.deepEqual(audit.observed.declared_external_dependencies, []);
  assert.equal(audit.decisions.source_content_copied, false);
  assert.equal(audit.decisions.local_candidate_status, "model-only-eligible");
  assert.equal(audit.decisions.candidate_redistribution_status, "verified");
  assert.equal(audit.decisions.candidate_authorization_scope, "desktop-distribution");
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
