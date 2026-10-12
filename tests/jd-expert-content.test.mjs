import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import test from "node:test";

const root = "plugins/yijie-desktop-skills/experts/jd-ops-expert/skills/jd-ops-kb";
const read = (relative) => readFile(path.join(root, relative), "utf8");

test("JD content index locates 42 real scenes across 14 modules with bounded original-source ranges", async () => {
  const index = JSON.parse(await read("references/scene-index.json"));
  assert.equal(index.content_version, "0.1.3");
  assert.equal(index.source.lines, 2291);
  assert.equal(index.source.sha256, "ce352f4f8ce2e21b5526ac5471104aff52802d5c36b099c0f6b425718f026d4e");
  assert.equal(index.modules.length, 14);
  assert.equal(index.scenes.length, 42);
  assert.equal(new Set(index.scenes.map((scene) => scene.id)).size, 42);
  const seen = new Set();
  for (const [offset, module] of index.modules.entries()) {
    assert.equal(module.id, `M${String(offset + 1).padStart(2, "0")}`);
    assert.equal(module.scene_ids.length, 3);
    assert.match(module.file, /^references\/m\d{2}-[a-z-]+\.md$/);
    const text = await read(module.file);
    assert.ok(text.includes(`版本：${index.content_version}`), `${module.id}: module version matches index`);
    const actual = [...text.matchAll(/^## (M\d{2}-\d{2}) (.+)$/gm)].map((match) => match[1]);
    assert.deepEqual(actual, module.scene_ids);
    for (const id of module.scene_ids) {
      const scene = index.scenes.find((entry) => entry.id === id);
      assert.ok(scene, id);
      assert.equal(scene.file, module.file);
      assert.equal(scene.source_id, index.source.id);
      assert.equal(scene.policy_verification, "NOT RUN");
      assert.ok(["reviewed-reference", "conflicted", "incomplete"].includes(scene.status));
      const section = text.split(`## ${scene.heading}\n`)[1]?.split("\n## ")[0];
      assert.ok(section, `${id} heading must resolve`);
      for (const field of ["输入：", "输出：", "待核实：", `状态：${scene.status}`]) assert.ok(section.includes(field), `${id}: ${field}`);
      assert.ok(scene.source_line_ranges.length > 0);
      for (const range of scene.source_line_ranges) {
        assert.ok(Number.isInteger(range.start) && Number.isInteger(range.end));
        assert.ok(range.start >= 1 && range.end >= range.start && range.end <= index.source.lines);
        const label = range.start === range.end ? String(range.start) : `${range.start}–${range.end}`;
        assert.ok(section.includes(label), `${id}: missing original range ${label}`);
      }
      assert.equal(seen.has(id), false);
      seen.add(id);
    }
  }
  assert.equal(seen.size, 42);
  assert.equal(index.scenes.find(({ id }) => id === "M08-05").status, "conflicted");
  assert.equal(index.scenes.find(({ id }) => id === "M14-04").status, "incomplete");
});

test("JD archive source remains local text resources with resolvable references and short role", async () => {
  const role = await read("ROLE.md");
  assert.ok(Buffer.byteLength(role, "utf8") < 4096);
  assert.match(role, /京东单平台/);
  assert.match(role, /不得因选择专家而自动请求网络/);
  assert.match(role, /不附加循环\/轮数上限/);
  const queue = [root];
  while (queue.length) {
    const directory = queue.shift();
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const absolute = path.join(directory, entry.name);
      assert.equal(entry.isSymbolicLink(), false);
      if (entry.isDirectory()) { queue.push(absolute); continue; }
      assert.ok(/\.(md|json|jsonl)$/.test(entry.name), absolute);
      const text = await readFile(absolute, "utf8");
      assert.doesNotMatch(text, /\/(?:Users|home)\//);
      if (!entry.name.endsWith(".md")) continue;
      for (const match of text.matchAll(/\]\(([^)]+)\)/g)) {
        assert.doesNotMatch(match[1], /^(?:https?:|file:)/);
        const target = path.resolve(path.dirname(absolute), match[1].split("#")[0]);
        assert.ok(target.startsWith(`${path.resolve(root)}${path.sep}`));
        await readFile(target);
      }
    }
  }
});

test("JD good-faith evaluation covers source gaps, scope, arithmetic and ordinary unavailable resources", async () => {
  const cases = (await read("evals/dataset.jsonl")).trim().split("\n").map(JSON.parse);
  assert.equal(cases.length, 12);
  for (const entry of cases) {
    assert.equal(entry.source, "synthetic");
    assert.ok(entry.expected.length > 15);
    assert.equal(typeof entry.input.question, "string");
  }
  assert.ok(cases.some(({ input }) => input.resource_state === "unavailable" && input.user_cancelled));
  assert.ok(cases.some(({ input }) => input.requested_content_version === "unknown-version"));
  assert.ok(cases.some(({ input }) => input.available_capabilities?.includes("local-reference-read")));
  const output = await read("examples/output-001.md");
  assert.match(output, /聚酯纤维衣物收纳袋 10件装/);
  assert.match(output, /未发布或修改/);
  const rubric = await read("evals/rubric.md");
  assert.match(rubric, /真实模型评测 NOT RUN/);
  assert.match(rubric, /引用可定位率为100%/);
});
