# FEAT-158 内容 0.1.1 修正审阅

2026-10-11。本地未发布候选，专家 `jd-ops-expert@0.1.1`，bundle `0.4.1`。本文件记录相对 0.1.0 的补强，不改写旧版来源或真实模型失败。

## 实际触发与修正范围

0.1.0 的 run5 真实合成验收发现：第三轮把“未提供品牌资料”推成“品牌=无品牌”，并把本会话以前读取的 M03/M12 标为“本次实际读取”；第四轮用户明确不联网时，Runtime 仍记录 completed web_search_call。主任务正常中断第四轮，保留实际失败与未完成回答。

本次仅在短 ROLE、SKILL、示例、检查表与原 12 条良性 Eval 中明确两项边界：

- 缺失的数值、类别和是非事实均是未知；未提供品牌资料须标“品牌待确认”，不等于无品牌商品或无品牌流程。
- 依据区分“本轮新读”与“沿用本会话此前已读”。历史读取须仍可核对相同内容版本；用户要求本轮读取时，重读相关片段或明示没有重读，不能虚报。

14 模块、42 场景、原稿行号和政策未知状态保持；各文件内容版本统一为 0.1.1，避免知识 manifest 与正文错配。没有增加网络/连接器能力，没有更改京东现行政策结论。实际 web_search 暴露由 Host/Runtime 工程边界收口，不能用本次提示词补强冒充已禁止工具。

## 来源与旧版保留

原用户资料、0.1.0 本地授权及 source audit 均保持原字节。旧候选完整 41 文件保留于 `dist/skills-experts-candidate-v010-run5/`，保留检查清单为 `dist/feat158-v010-run5-preservation.json`；旧 manifest SHA-256 为 `156fa3da100f82985087637ea3e94138d1f6ff813fedc8a4275b0dcad591e355`。现有 App 安装、SQLCipher、Host/Codex home 和 run5 rollout 未修改。

新源仍为 `plugins/yijie-desktop-skills/experts/bundle-source.json`；新输出为 `dist/skills-experts-candidate-v011/`。新审校文件是 `source-audits/FEAT-158-jd-ops-content-audit-v0.1.1.json`，新本地授权记录是 `FEAT-158-local-use-authorization-v0.1.1.md`，不复写旧文件以假装旧 authority 授权新内容。

## 验证状态

新版本真实模型 Eval：**NOT RUN**。0.1.0 已发生的失败不会因升版或结构检查而变为通过。本仓实际完成：`make lint`、`make test` 的 11 项正常测试与 16 条合成数据格式检查、Contracts Skills 消费同步 `--check`、原 canonical packager 显式新目录打包、`git diff --check`。原 38 个普通技能元信息及归档逐 SHA-256 相同，旧候选 41 文件及旧 source audit/授权文件原字节不变。未执行模型、服务、受管安装或产品 UI。

| 0.1.1 候选 | SHA-256 |
|---|---|
| bundle-manifest.json | `31e7f42193263356c1e4939600ebd95961e6eb682c96f53429b47417dc3d1b6d` |
| authority.json | `c23a7085504b78bf2a880c2804d6ed4d7c78ff82ed13a01473619cd9269e28aa` |
| 专家 ZIP | `5ca70d7417c30951f67ef8da32be37563afaaadf0756ff60f96d84471d9cd594` |
| ROLE.md（2156 bytes） | `cd30368006f57ab8c400182600a53019b960bb23e49395972ec782e5e37e43da` |
| knowledge manifest canonical digest | `767249e42b0d94f802b863875588ba78b30345f57f0a18eac075838e2e364b89` |

完整命令、输入及候选摘要保存在 `dist/feat158-v011-checks.json`。来源 base revision 为 `488714a8d96f40806a257aae097683815b1dd458` 的 working-tree，tree SHA-256 为 `6c2fecfa23999718c605af0d298c486cf45287b91b4330fbaaa6140c5cb6253e`，仍 `release=false`；不能将此描述成已提交的来源。

旧版 source definition 的原始字节另存 `dist/skills-experts-candidate-v010-run5-source-definition.json`，与旧 authority 中的 source_definition SHA-256 完全一致；旧包内 26 个源内容文件由原 ZIP 保留。跨仓当前 assets pin 与独立运行 profile 由主任务统一 canonical 同步，此处没有修改消费者或历史安装。

公开再分发、官方政策逐条核验和完整 D4 均未声明通过。
