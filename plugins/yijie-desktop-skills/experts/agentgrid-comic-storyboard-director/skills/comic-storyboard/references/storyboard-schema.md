# 分镜 JSON 私有结构

版本：0.1.0；schemaVersion 保留原 1.0。只有 targetDurationSec 的未知值为 null，不使用字符串 pending。

```json
{
  "schemaVersion": "1.0",
  "episodeId": "EP-001",
  "targetDurationSec": 6,
  "durationToleranceSec": 0,
  "registries": {"characters": ["CHAR-001"], "scenes": ["SC-001"], "props": ["PROP-001"]},
  "shots": [{
    "shotId": "SH-001", "sceneId": "SC-001", "durationSec": 6,
    "version": 1, "status": "draft", "characters": ["CHAR-001"], "props": ["PROP-001"],
    "narrativePurpose": "发现归还钥匙的任务",
    "framing": "中景", "camera": "固定", "action": "小林捡起门前钥匙",
    "dialogue": "是谁落下的？", "continuityIn": ["钥匙在地上"],
    "continuityOut": ["小林手持钥匙"], "productionPrompt": "固定中景，人物拾取钥匙，位置连续"
  }]
}
```

## 必需约束

- 顶层有 schemaVersion、episodeId、targetDurationSec、durationToleranceSec、registries、shots。
- 角色/场景/道具台账是唯一字符串数组。场景至少一项；角色和道具可为空。
- shots 非空；每镜必需 shotId、sceneId、durationSec、version、status、characters、props、narrativePurpose、framing、camera、action、dialogue、continuityIn、continuityOut、productionPrompt。无对白可写空字符串；无连续性状态可写空数组并说明原因。
- durationSec 是有限正数；targetDurationSec 是有限正数或 null；durationToleranceSec 是有限非负数，默认零，不能为凑通过临时增加。
- version 是不含布尔值的正整数；status 为 draft、approved、locked、blocked。
- 台账与镜头引用一致；shotId 唯一。ID 创建后稳定，不能因插镜重排原 ID。
- 当前字段结构与脚本校验范围一致。人工还需检查对白、动作与连续性语义；结构通过不代表语义质量通过。

## 结果解释

status=pass 仅表示已检查的结构/引用/时长/版本约束通过。durationPass=true 表示在明确容差内对齐；targetDurationSec=null 时 durationPass=null 且有警告。锁定/局部修改对比需传入 baseline；未传入时不能说已自动验证保留历史镜头。
