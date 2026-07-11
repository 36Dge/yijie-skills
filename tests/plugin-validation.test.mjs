import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { parse } from "smol-toml";

test("Amazon plugin has a stable identifier and semantic version", async () => {
  const plugin = parse(await readFile("plugins/amazon-listing-optimizer/plugin.toml", "utf8"));
  assert.equal(plugin.id, "amazon-listing-optimizer");
  assert.match(plugin.version, /^\d+\.\d+\.\d+$/);
});
