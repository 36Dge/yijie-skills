import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { promisify } from "node:util";

const exec = promisify(execFile);
const sourcePath = "plugins/yijie-desktop-skills/experts/bundle-source.json";
const newIds = ["xiaohongshu-copywriter", "agentgrid-comic-storyboard-director", "cross-border-ecommerce-operations-expert"];
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const comicRoot = "plugins/yijie-desktop-skills/experts/agentgrid-comic-storyboard-director/skills/comic-storyboard";
const validator = path.join(comicRoot, "scripts/validate_storyboard.py");

test("three adapted experts include exactly reviewed files, bounded roles and resolvable references", async () => {
  const source = JSON.parse(await readFile(sourcePath, "utf8"));
  assert.deepEqual(source.skills.slice(1, 4).map(({ expert }) => expert.expert_id), newIds);
  for (const entry of source.skills.filter(entry => newIds.includes(entry.expert.expert_id))) {
    const review = JSON.parse(await readFile(entry.provenance.source_reference, "utf8"));
    const actual = [];
    const queue = [entry.source_dir];
    while (queue.length) {
      const folder = queue.shift();
      for (const item of await readdir(folder, { withFileTypes: true })) {
        const full = path.join(folder, item.name);
        assert.equal(item.isSymbolicLink(), false);
        if (item.isDirectory()) { queue.push(full); continue; }
        actual.push(path.relative(entry.source_dir, full));
        const bytes = await readFile(full);
        const record = review.files.find(({ path: relative }) => relative === path.relative(entry.source_dir, full));
        assert.equal(record?.sha256, hash(bytes));
        assert.equal(record?.bytes, bytes.length);
        if (!full.endsWith(".md")) continue;
        const text = bytes.toString("utf8");
        assert.doesNotMatch(text, /\/(?:Users|home)\//);
        for (const match of text.matchAll(/\]\(([^)]+)\)/g)) {
          assert.doesNotMatch(match[1], /^(?:https?:|file:)/);
          const target = path.resolve(path.dirname(full), match[1].split("#")[0]);
          assert.ok(target.startsWith(`${path.resolve(entry.source_dir)}${path.sep}`));
          await readFile(target);
        }
      }
    }
    assert.deepEqual(actual.sort(), [...entry.package_files].sort());
    assert.equal(actual.filter((name) => name.endsWith("SKILL.md")).length, 1);
    assert.ok((await readFile(path.join(entry.source_dir, "ROLE.md"))).length < 4096);
    assert.equal(review.decisions.local_development_authorized, true);
    assert.equal(review.decisions.desktop_redistribution_verified, false);
    assert.ok(review.source_files.length > 0);
    const cases = (await readFile(path.join(entry.source_dir, "evals/dataset.jsonl"), "utf8")).trim().split("\n").map(JSON.parse);
    assert.equal(cases.length, entry.version === "0.1.1" ? 7 : 5);
    assert.ok(cases.every((item) => item.source === "synthetic" && item.expected.length > 15));
  }
});

// Only normal complete/incomplete authoring documents; no hostile fixture or environment mutation.
async function withStoryboard(run) {
  const temporary = await mkdtemp(path.join(os.tmpdir(), "yijie-storyboard-"));
  try {
    const data = JSON.parse(await readFile(path.join(comicRoot, "examples/storyboard-001.json"), "utf8"));
    const input = path.join(temporary, "storyboard.json");
    await writeFile(input, JSON.stringify(data));
    await run({ temporary, data, input });
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
}

async function validate(input, output, baseline) {
  const args = [validator, "--input", input, "--output", output];
  if (baseline) args.push("--baseline", baseline);
  let code = 0;
  try { await exec("python3", args); } catch (error) { code = error.code; }
  return { code, result: JSON.parse(await readFile(output, "utf8")) };
}

test("comic validator writes an actual report for complete and unknown-duration storyboards without editing inputs", async () => {
  await withStoryboard(async ({ temporary, data, input }) => {
    const before = await readFile(input);
    const complete = await validate(input, path.join(temporary, "complete.json"));
    assert.equal(complete.code, 0);
    assert.equal(complete.result.status, "pass");
    assert.equal(complete.result.actualDurationSec, 12);
    assert.equal(complete.result.durationPass, true);
    assert.deepEqual(await readFile(input), before);
    data.targetDurationSec = null;
    const draft = path.join(temporary, "draft.json");
    await writeFile(draft, JSON.stringify(data));
    const unknown = await validate(draft, path.join(temporary, "unknown.json"));
    assert.equal(unknown.code, 0);
    assert.equal(unknown.result.durationPass, null);
    assert.equal(unknown.result.actualDurationSec, 12);
    assert.ok(unknown.result.warnings.length > 0);
  });
});

test("comic validator reports ordinary missing fields and duration mismatch instead of claiming success", async () => {
  await withStoryboard(async ({ temporary, data, input }) => {
    delete data.shots[0].sceneId;
    data.targetDurationSec = 30;
    await writeFile(input, JSON.stringify(data));
    const result = await validate(input, path.join(temporary, "validation.json"));
    assert.equal(result.code, 1);
    assert.equal(result.result.status, "fail");
    assert.equal(result.result.durationPass, false);
    assert.ok(result.result.errors.some((error) => error.includes("sceneId")));
  });
});

test("comic local revision preserves other shots and validates changed version against the original file", async () => {
  await withStoryboard(async ({ temporary, data, input }) => {
    data.shots[1].dialogue = "邻居，你的钥匙落在门口了。";
    data.shots[1].version = 2;
    const revised = path.join(temporary, "revised.json");
    await writeFile(revised, JSON.stringify(data));
    const result = await validate(revised, path.join(temporary, "revision-report.json"), input);
    assert.equal(result.code, 0);
    assert.deepEqual(result.result.changedShotIds, ["SH-002"]);
    assert.deepEqual(result.result.unchangedShotIds, ["SH-001"]);
    assert.deepEqual(result.result.addedShotIds, []);
    assert.deepEqual(result.result.removedShotIds, []);
    const original = JSON.parse(await readFile(input, "utf8"));
    assert.equal(original.shots[1].version, 1);
    assert.deepEqual(original.shots[0], data.shots[0]);
  });
});

test("comic validator checks ordinary revision mistakes and does not overwrite earlier reports", async () => {
  await withStoryboard(async ({ temporary, data, input }) => {
    data.shots[1].dialogue = "请收好钥匙。";
    const revised = path.join(temporary, "revised.json");
    await writeFile(revised, JSON.stringify(data));
    const output = path.join(temporary, "report.json");
    const result = await validate(revised, output, input);
    assert.equal(result.code, 1);
    assert.ok(result.result.errors.some((error) => error.includes("increase version")));
    const originalReport = await readFile(output);
    await assert.rejects(exec("python3", [validator, "--input", input, "--output", output]), (error) => error.code === 2);
    assert.deepEqual(await readFile(output), originalReport);
  });
});
