# FEAT-158 内容 0.1.3 最小事实保真修订

2026-10-11。专家 `jd-ops-expert@0.1.3`，bundle `0.4.3`，仅本地候选，`release=false`。用户最新将工作收窄为逻辑实现检查，不继续扩大真实模型或 UI 验收。本次真实模型调用为 0，0.1.3 模型效果 **NOT RUN**。

## 证据与修订边界

0.1.2 run8 只发送并完成前 6 条：5 条首次通过，c01 首次失败。c01 输入为“无品牌/销量/认证资料”，输出的用户事实表却填写“新品无销量”；资料缺失被转成确定经营事实。按原 rubric 保留严重事实错误 1 项，12/12 支持场景可定位不抵消该失败。7–17 步按用户收窄未执行，不记通过；旧题、旧答案和工具证据未改。

本次只对 ROLE 与 M03-01 做实质修订：事实表逐项对应用户原文或已授权记录，缺证据的字段填“待确认”；资料经验、计算和条件性推断另列，不填回已确认事实；店铺阶段不作为商品历史的证据。没有写入新的评测商品、数值或标准答案，没有扩充知识库、权限、工具或产品 profile。现有示例与检查表已有未知事实保留约束，本次复核后不重复增加同类条目。

14 模块/42 场景及原稿行号不变。正文、manifest、测试预期版本机械同步 0.1.3。原 12 条 Eval 的事实、问法、expected 和 rubric 阈值不改，仅将其中当前内容版本参数 0.1.2 同步为 0.1.3；逐字差异见 `dist/feat158-v013-eval-version-only-diff.json`。严重错误 0、引用可定位率 100%、全部所选用例通过的阈值保持；旧 run8 证据仍固定 0.1.2，不以新提示词或结构测试声称修复了模型效果。

## 来源与兼容

`contract-impact = semantic`：版本化专家行为指导改变，wire、归档布局、权限与执行链无变化。内容权威源仍为本仓专家目录和 `experts/bundle-source.json`；Contracts 新 schema 为 N/A，继续消费现有 canonical v3。Host/Desktop 由主任务统一更新单份当前候选摘要，不新增多版本产品 profile，不绕过既有 ResourceInUse 或旧引用保护。

0.1.2 修改前保存 40 个源及审阅文件到 `dist/feat158-v012-run8-source/`；41 个原候选文件仍在 `dist/skills-experts-candidate-v012/`。摘要记录为 `dist/feat158-v012-run8-preservation.json`，旧 manifest 为 `a176bfba892afbc4de8622ebde955a72aef240ab51a9256d7bfb6c5ec40c0936`。0.1.0/0.1.1 的证据和产物继续保留。本次不访问已安装包或 App/Host/Codex 历史目录。

新产物只通过既有确定性打包器生成到 `dist/skills-experts-candidate-v013/`：

```bash
node scripts/package-desktop-skills.mjs --source plugins/yijie-desktop-skills/experts/bundle-source.json --output dist/skills-experts-candidate-v013
```

本地正常检查与准确摘要见 `dist/feat158-v013-checks.json`。producer 检查通过后方可同步 consumer pin；未来使用或回退仍走原正常版本兼容路径，不能覆盖历史、改收据或宣称发布。未做模型/UI/官方政策联网核验，也不宣称完整产品验收已通过。

## 本地检查结果

`make lint`、`make test` 的 11 项正常测试及 16 条合成数据格式检查、Contracts canonical `--check`、新目录打包与 `git diff --check` 均通过。已核对旧 41 产物与 40 源快照文件摘要保留，原 38 普通 Skill 元信息/归档字节相同，新专家归档 26 文件与源一致。排除机械版本替换后，仅 ROLE.md 与 references/m03-listing.md 有内容差异。

| 0.1.3 候选 | SHA-256 |
|---|---|
| bundle-manifest.json | `46e3e5b9e101c252a4dcb0bc9d27c1da024ea6457be43e5be5736ccf047c6b58` |
| authority.json | `351327f5b93b60323fbe7833454c6e53f96f0bacef7da500c9db9c24a6311b53` |
| 专家 ZIP | `baa8c8550b8b82b5f1be7bcfc59693c8920ff438fa854e84450936685e3d3b80` |
| ROLE.md（3188 bytes） | `a644bf12c4573895d3e6edc7b7a619cc95cc429c910260a5ef16b5f2bce7b6f5` |
| knowledge manifest canonical digest | `b0718d43a248bdf4dbcebec5623932266a87e7e4f78aad3dbe01e250b6545d08` |

来源仍是 base revision `488714a8d96f40806a257aae097683815b1dd458` 的 working-tree；tree SHA-256 为 `e7521eabbef58a18cfeddaa04caba3acd1d3068b52f2d06beec804f3b05e8b6f`，source definition SHA-256 为 `464a498f10d6859afbfb4c2675dce4e2a202fd846031f4aab1cda2f3d73c1edf`。没有 commit/push 或发布行为。
