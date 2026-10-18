import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../plugins/yijie-desktop-skills/experts/linkfox-expert-aigc-imagegen-mannequin-to-model/skills/mannequin-to-model");
const preparation = JSON.parse(readFileSync(path.join(root, "examples/request.json")));
function run(action, value, accept = true) {
  const cwd = mkdtempSync(path.join(tmpdir(), "yijie-mannequin-normal-"));
  try {
    const input = JSON.stringify(value, null, 2) + "\n";
    writeFileSync(path.join(cwd, "request.json"), input);
    const args = [path.join(root, "scripts/prepare_mannequin.py"), action, "--input", "request.json", "--output-dir", "result"];
    const command = spawnSync("python3", args, { cwd, encoding: "utf8" });
    if (!accept) {
      assert.notEqual(command.status, 0);
      assert.equal(existsSync(path.join(cwd, "result")), false);
      return;
    }
    assert.equal(command.status, 0, command.stderr);
    assert.equal(readFileSync(path.join(cwd, "result/input.json"), "utf8"), input);
    const result = JSON.parse(readFileSync(path.join(cwd, "result/inspection.json")));
    assert.equal(JSON.parse(command.stdout).external_calls, 0);
    assert.notEqual(spawnSync("python3", args, { cwd, encoding: "utf8" }).status, 0, "existing output must not be overwritten");
    return result;
  } finally { rmSync(cwd, { recursive: true, force: true }); }
}
const observation = (stage, data, extra = {}) => ({ stage, source_operation_id: "ordinary-operation", expected_task_id: "ordinary-task", mcp_result: { isError: false, structuredContent: data }, ...extra });

test("mannequin preparation keeps reference order, explicit options and unsubmitted state", () => {
  const result = run("prepare", preparation);
  assert.equal(result.status, "prepared_not_submitted");
  assert.equal(result.current_tool_schema_verified, false);
  assert.deepEqual(result.text_request.arguments.imageUrls, [preparation.garment_url, preparation.model_url, preparation.background_url]);
  assert.equal(result.image_request_options.outputNum, 1);
  assert.equal(result.text_request.arguments.model, "LF_GEM_2");
});
test("mannequin incomplete roles and unsupported model combinations stop before output", () => {
  run("prepare", { ...preparation, model_url: undefined }, false);
  run("prepare", { ...preparation, text_model: "GEM_3_1_PRO" }, false);
  run("prepare", { ...preparation, thinking_level: "minimal" }, false);
  run("prepare", { ...preparation, image_provider: "BANANA", resolution: "2K" }, false);
});
test("mannequin creation records only its returned identity, never successful media", () => {
  const result = run("observe", observation("create_image", { taskId: "ordinary-task" }));
  assert.equal(result.state, "created");
  assert.deepEqual(result.query_arguments, { taskId: "ordinary-task" });
  assert.equal(result.result_url, undefined);
  assert.equal(result.retry_creation, false);
});
test("mannequin processing waits for explicit continuation without re-creation", () => {
  const result = run("observe", observation("query_image", { taskId: "ordinary-task", status: "PROCESSING" }));
  assert.equal(result.state, "processing");
  assert.equal(result.reason, "wait_for_explicit_user_continuation");
  assert.equal(result.retry_creation, false);
});
test("mannequin successful text preserves exact newlines into the image request", () => {
  const prompt = "Preserve the garment reference.\nNeutral pose and studio lighting.\n";
  const result = run("observe", observation("query_text", { taskId: "ordinary-task", status: "SUCCESS", content: prompt }, { preparation }));
  assert.equal(result.state, "text_ready");
  assert.equal(result.image_request.arguments.prompt, prompt);
  assert.deepEqual(result.image_request.arguments.imageUrls, [preparation.garment_url, preparation.model_url, preparation.background_url]);
});
test("mannequin successful image returns an actual link and no invented local path or quality verdict", () => {
  const value = { taskId: "ordinary-task", status: "SUCCESS", resultList: [{ type: "image", url: "https://images.example.com/result.png" }] };
  const result = run("observe", observation("query_image", value, { mcp_result: { content: [{ type: "text", text: JSON.stringify(value) }] } }));
  assert.equal(result.state, "image_link_ready");
  assert.equal(result.result_url, value.resultList[0].url);
  assert.equal(result.local_file, null);
  assert.equal(result.visual_fidelity, "not_verified");
});
test("mannequin normal failure, empty result, unknown status and identity mismatch never become success", () => {
  for (const value of [
    { taskId: "ordinary-task", status: "FAILED", errorMsg: "generation unavailable" },
    { taskId: "ordinary-task", status: "SUCCESS", resultList: [] },
    { taskId: "ordinary-task", status: "QUEUED" },
    { taskId: "different-task", status: "SUCCESS", content: "ordinary" },
  ]) {
    const result = run("observe", observation("query_image", value));
    assert.ok(["unknown", "failed"].includes(result.state));
    assert.equal(result.retry_creation, false);
  }
});
test("mannequin MCP and business errors retain failure boundaries", () => {
  const error = run("observe", observation("create_text", {}, { mcp_result: { isError: true, content: [{ type: "text", text: "unavailable" }] } }));
  assert.equal(error.reason, "mcp_error");
  assert.equal(run("observe", observation("create_text", { errcode: 402, errmsg: "insufficient credits" })).reason, "business_error");
});
