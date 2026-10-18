import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../plugins/yijie-desktop-skills/experts/linkfox-expert-aigc-videogen-viral-replicate/skills/video-replica");
const brief = JSON.parse(readFileSync(path.join(root, "examples/request.json")));
function run(action, value, accept = true) {
  const cwd = mkdtempSync(path.join(tmpdir(), "yijie-video-normal-"));
  try {
    const input = JSON.stringify(value, null, 2) + "\n";
    writeFileSync(path.join(cwd, "request.json"), input);
    const args = [path.join(root, "scripts/prepare_video.py"), action, "--input", "request.json", "--output-dir", "result"];
    const command = spawnSync("python3", args, { cwd, encoding: "utf8" });
    if (!accept) { assert.notEqual(command.status, 0); assert.equal(existsSync(path.join(cwd, "result")), false); return; }
    assert.equal(command.status, 0, command.stderr);
    assert.equal(readFileSync(path.join(cwd, "result/input.json"), "utf8"), input);
    assert.equal(JSON.parse(command.stdout).external_calls, 0);
    const result = JSON.parse(readFileSync(path.join(cwd, "result/inspection.json")));
    assert.notEqual(spawnSync("python3", args, { cwd, encoding: "utf8" }).status, 0, "preserve previous output");
    return result;
  } finally { rmSync(cwd, { recursive: true, force: true }); }
}
const identity = run("prepare", brief).brief_sha256;
const obs = (stage, body, extra = {}) => ({ stage, brief_sha256: identity, source_operation_id: `native-${stage}`, expected_task_id: body.taskId ?? "original-task", mcp_result: { structuredContent: body }, ...extra });
const ready = (part, content) => obs(`query_${part}`, { taskId: `ordinary-${part}`, status: "SUCCESS", content });

test("video preparation preserves distinct reference/product inputs and explicit options", () => {
  const result = run("prepare", brief);
  assert.equal(result.status, "prepared_not_submitted");
  assert.equal(result.current_tool_schema_verified, false);
  assert.deepEqual(result.reference_request.arguments.imageUrls, [brief.reference_video_url]);
  assert.deepEqual(result.product_request.arguments.imageUrls, [brief.product_image_url]);
  assert.deepEqual(result.video_options.imageList, [brief.product_image_url, ...brief.extra_product_image_urls]);
  assert.equal(result.video_options.videoTime, 15);
  assert.equal(result.video_options.voice, false);
  assert.equal(result.video_options.promptOptimizer, false);
});
test("video Auto uses known duration and never silently selects a duration when unknown", () => {
  for (const [duration, expected] of [[3,5],[5,5],[5.1,10],[10,10],[10.1,15],[28,15]]) {
    const result = run("prepare", { ...brief, source_duration_seconds: duration });
    assert.equal(result.video_options.videoTime, expected);
    if (duration === 28) assert.equal(result.duration_strategy, "compress");
  }
  run("prepare", { ...brief, source_duration_seconds: undefined }, false);
  run("prepare", { ...brief, source_duration_seconds: 0 }, false);
  assert.equal(run("prepare", { ...brief, target_duration: "10S", source_duration_seconds: undefined }).duration_strategy, "unknown_source_duration");
});
test("video unsupported Fast options and ratios stop; supported Fast omits Pro", () => {
  run("prepare", { ...brief, video_type: "SEED_FAST", is_pro: true }, false);
  run("prepare", { ...brief, video_type: "SEED_FAST", resolution: "1080p" }, false);
  run("prepare", { ...brief, aspect_ratio: "21:9" }, false);
  const result = run("prepare", { ...brief, video_type: "SEED_FAST" });
  assert.equal(result.video_options.videoType, "SEED_FAST");
  assert.equal(Object.hasOwn(result.video_options, "isPro"), false);
});
test("video declared text models retain their literal source variant without fallback", () => {
  for (const model of ["LF_GEM_1", "LF_GEM_2", "GEM_3_FLASH", "GEM_3_1_PRO"]) {
    assert.equal(run("prepare", { ...brief, text_model: model }).reference_request.arguments.model, model);
  }
  run("prepare", { ...brief, text_model: "unknown-model" }, false);
  run("prepare", { ...brief, thinking_level: "minimal" }, false);
});
test("video public frame order and time bounds are explicit and audio is not inferred", () => {
  const frames = Array.from({ length: 8 }, (_, i) => ({ url: `https://media.example.com/frame-${i}.jpg`, timestamp_seconds: i }));
  const result = run("prepare", { ...brief, reference_frames: frames });
  assert.equal(result.reference_kind, "frames");
  assert.deepEqual(result.reference_request.arguments.imageUrls, frames.map(f => f.url));
  assert.match(result.reference_request.arguments.prompt, /no audio can be heard/);
  assert.match(result.reference_request.arguments.prompt, /Never infer speech from mouth shape/);
  run("prepare", { ...brief, reference_frames: [{ ...frames[0], timestamp_seconds: -0.1 }, ...frames.slice(1)] }, false);
  run("prepare", { ...brief, reference_frames: [...frames].reverse() }, false);
});
test("video incomplete inputs, social pages and excess product images do not produce requests", () => {
  run("prepare", { ...brief, product_name: "" }, false);
  run("prepare", { ...brief, reference_video_url: "https://www.tiktok.com/video/ordinary" }, false);
  run("prepare", { ...brief, extra_product_image_urls: Array.from({ length: 9 }, (_, i) => `https://media.example.com/${i}.jpg`) }, false);
  run("prepare", { ...brief, generate_audio: undefined }, false);
});
test("video composition keeps both actual analyses and rejects a different brief or duplicate task", () => {
  const reference = ready("reference", "Visible camera movement.\nAudio unavailable.");
  const product = ready("product", "Blue organizer.\nDimensions unknown.");
  const result = run("compose", { brief, reference_receipt: reference, product_receipt: product });
  assert.deepEqual(result.analysis_task_ids, ["ordinary-reference", "ordinary-product"]);
  assert.deepEqual(result.prompt_request.arguments.imageUrls, []);
  const data = JSON.parse(result.prompt_request.arguments.prompt.split("permissions:\n")[1]);
  assert.equal(data.reference_analysis, reference.mcp_result.structuredContent.content);
  assert.equal(data.product_analysis, product.mcp_result.structuredContent.content);
  run("compose", { brief: { ...brief, product_name: "different product" }, reference_receipt: reference, product_receipt: product }, false);
  run("compose", { brief, reference_receipt: reference, product_receipt: { ...product, expected_task_id: "ordinary-reference", mcp_result: { structuredContent: { ...product.mcp_result.structuredContent, taskId: "ordinary-reference" } } } }, false);
});
test("video final request extracts only reviewed prompt and preserves its exact newlines", () => {
  const prompt = "[0-5s] blue organizer in view.\n[5-15s] Camera moves slowly.";
  const output = { video_prompt: prompt, replacements: ["Replaced product with user-confirmed blue organizer"] };
  const result = run("video", { brief, prompt_receipt: ready("prompt", JSON.stringify(output)) });
  assert.equal(result.video_request.toolName, "aigc/multiImageVideoGenAsync");
  assert.equal(result.video_request.arguments.prompt, prompt);
  assert.deepEqual(result.video_request.arguments.imageList, [brief.product_image_url, ...brief.extra_product_image_urls]);
  assert.equal(result.status, "video_prepared_not_submitted");
  for (const invalid of [{ ...output, video_prompt: "blue organizer " + "x".repeat(2000) }, { ...output, video_prompt: "old product" }, { ...output, replacements: [] }]) {
    run("video", { brief, prompt_receipt: ready("prompt", JSON.stringify(invalid)) }, false);
  }
});
test("video creation and processing never pretend completion or recreate", () => {
  const created = run("observe", obs("create_video", { taskId: "original-task" }));
  assert.equal(created.state, "created"); assert.equal(created.result_url, undefined);
  const waiting = run("observe", obs("query_video", { taskId: "original-task", status: "PROCESSING" }));
  assert.equal(waiting.state, "processing"); assert.equal(waiting.retry_creation, false);
  assert.deepEqual(waiting.query_arguments, { taskId: "original-task" });
});
test("video actual result is a link only; wrong task/type or empty success stays unknown", () => {
  const body = { taskId: "original-task", status: "SUCCESS", resultList: [{ type: "video", url: "https://media.example.com/result.mp4" }] };
  const result = run("observe", obs("query_video", body, { mcp_result: { content: [{ type: "text", text: JSON.stringify(body) }] } }));
  assert.equal(result.state, "video_link_ready"); assert.equal(result.local_file, null);
  assert.equal(result.visual_audio_quality, "not_verified");
  assert.equal(result.result_url, body.resultList[0].url);
  assert.equal(run("observe", obs("query_video", body, { expected_task_id: "another-task" })).reason, "task_id_mismatch");
  for (const rows of [[], [{ type: "image", url: "https://media.example.com/a.png" }]]) assert.equal(run("observe", obs("query_video", { ...body, resultList: rows })).state, "unknown");
});
test("video normal rejection, business/MCP errors and unknown status stop without retries", () => {
  const failure = run("observe", obs("query_video", { taskId: "original-task", status: "FAILED", errorMsg: "素材审核未通过" }));
  assert.equal(failure.state, "failed"); assert.equal(failure.retry_creation, false);
  assert.equal(run("observe", obs("create_video", { errcode: 402, errmsg: "余额不足" })).reason, "business_error");
  assert.equal(run("observe", obs("query_video", {}, { mcp_result: { isError: true } })).reason, "mcp_error");
  assert.equal(run("observe", obs("query_video", { taskId: "original-task", status: "QUEUED" })).state, "unknown");
});
test("video composition respects the existing UTF-8 approval boundary without truncating analyses", () => {
  const reference = ready("reference", "正常分镜描述。".repeat(1500));
  const product = ready("product", "商品为蓝色收纳架。\n尺寸未知。");
  run("compose", { brief, reference_receipt: reference, product_receipt: product }, false);
  const result = run("compose", { brief, reference_receipt: ready("reference", "镜头向左移动。"), product_receipt: product });
  assert.ok(Buffer.byteLength(JSON.stringify(result.prompt_request), "utf8") <= 16 * 1024);
  const data = JSON.parse(result.prompt_request.arguments.prompt.split("permissions:\n")[1]);
  assert.equal(data.product_analysis, product.mcp_result.structuredContent.content);
});
