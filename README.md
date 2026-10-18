# yijie-skills

跨境电商 Codex Skills、Plugins、Prompt Packs 和 Evals 资产库。

## 本地开发

```bash
pnpm install
pnpm lint
pnpm test
pnpm package
```

完整测试需要相邻的 `yijie-connectors` 检出，其中
`worker/fixtures/linkfox-sale-request.json` 是口播专家请求对照的唯一 fixture；
本仓不保留副本，缺失时测试必须失败。CI 沿现有 Desktop 多仓目录布局将两个仓库放为兄弟目录，
只稀疏检出 Connectors 的这一个文件，并在
[CI workflow](.github/workflows/ci.yml) 固定完整提交
`e2792f9be5b52cc22d99788157855131224c80dc`。更新来源时修改该明确 pin 并重新运行完整检查，
不改为浮动分支、不复制 fixture、不跳过跨仓一致性断言。

`pnpm package` 生成 FEAT-129 的确定性 Desktop `local-development` Bundle；
`pnpm package:desktop-release` 生成内容相同、渠道标记为 `desktop-release` 的正式分发 Bundle：

```text
dist/skill-packages/
├── bundle-manifest.json
└── packages/
    └── *.zip  # 38 个 Skill 资源包
```

Manifest 精确消费 `yijie-contracts` 0.5.1 的 `skill-bundle-manifest-v2`，包含五个分类共
38 项 Skill（`5/9/7/9/8`）。全部条目均为 `bundled + installable`，具备确定性压缩包、
来源摘要、风险、能力依赖、`iconKey`、所有权/桌面再分发授权和逐项安全审核。
`copywriting@0.1.0` 继续使用较窄的易界自研 model-only 实现；其他 37 项使用经过审核的
原始源码快照，无需重新编写。

契约 pin 与来源/许可证据分别见 `contracts/lock.json`、
`docs/provenance/FEAT-129-ownership-and-desktop-redistribution.md`、
`docs/provenance/source-audits/FEAT-129-catalog-38-source-audit.json` 和
`docs/provenance/source-audits/FEAT-129-catalog-38-security-review.json`。所有 38 项均已获
`desktop-distribution` 授权，可用于本地启动和正式桌面分发；Agent Host 的最小权限、用户
批准、路径隔离和审计控制继续生效。

## 安全要求

不得放入真实商家数据、平台 token、cookie、订单、买家 PII 或财务数据。

## FEAT-158 本地专家候选

京东专向专家内容位于 `plugins/yijie-desktop-skills/experts/jd-ops-expert/skills/jd-ops-kb/`，
包含同包短角色、14模块42场景、来源行号和良性Eval。当前内容为0.1.3；0.1.0的事实边界/未授权搜索失败与0.1.1 run7未全部通过的内容评测均保留，0.1.2 run8前6题中1项事实保真失败、5项通过，其余依用户收窄未执行；0.1.3仅作本地逻辑修订，真实模型Eval未执行。政策联网核验未执行。

原 `pnpm package` 和 `package:desktop-release` 继续构建38项v2包。专家通过同一确定性打包器的
显式source/output生成独立本地v3候选，复用原38项资源并追加一个 `expert_resources` 条目：

```bash
node ../yijie-contracts/scripts/sync-experts.mjs --consumer=skills --check
node scripts/package-desktop-skills.mjs --source plugins/yijie-desktop-skills/experts/bundle-source.json --output dist/skills-experts-candidate-v013
```

候选输出含 `bundle-manifest.json`、39个普通归档和 `authority.json`。authority固定manifest、
来源树、角色、知识、内容审校和本地授权摘要，供Host/Desktop通过明确的开发同步固定来源；不能接受
renderer任意路径或manifest自证。它标记 `release=false`，不是已发布commit或桌面再分发授权。
旧 `contracts/lock.json` 不变；新v3源由Contracts canonical同步生成到 `contracts/experts.candidate.json`，
不得手写复制schema或把working-tree候选伪称不可变发布pin。

当前内容/授权记录见 `docs/provenance/FEAT-158-jd-ops-v0.1.3-content-review.md` 与
`docs/provenance/FEAT-158-local-use-authorization-v0.1.3.md`；原0.1.0/0.1.1/0.1.2文档、旧候选及对应源快照保留。专家不进入全局Runtime Skill投影；
本地安装不授予外部调用或额外文件权限。

本次源码与知识正文公开 Git 推送已由用户明确授权；范围、不可变 Contracts 来源与仍保留的本地产品边界见 [FEAT-158 Git 交付记录](docs/provenance/FEAT-158-git-publication.md)。

## FEAT-158 第一组三位专家本机接入

2026-10-16 新候选 bundle `0.5.0` 在原 38 普通包和未改动的
`jd-ops-expert@0.1.3` 之外，追加小红书、漫剧、跨境运营三个独立 `0.1.0`
专家资源，共 42 个归档。每位仍只有一个私有 SKILL 入口，沿现有安装、版本与会话选择机制；
普通 `pnpm package` 的 38 项 v2 输出保持不变。

```bash
node scripts/package-desktop-skills.mjs --source plugins/yijie-desktop-skills/experts/bundle-source.json --output dist/skills-experts-first-three-v010
```

漫剧含经审阅的 Python 3.10+ 标准库校验器，任务文件写出/校验只使用当前会话已有权限；
只读资源安装不授予执行权限。跨境运营完整离线策划不依赖轻流，轻流协作仍走现有资格与审批。
三位均不自动发布、启用外部服务或生成媒体成片。来源与边界见
[内容审校](docs/provenance/FEAT-158-first-three-v0.1.0-content-review.md) 和
[本机授权](docs/provenance/FEAT-158-first-three-local-use-authorization-v0.1.0.md)。
这些新增内容没有公开分发或 Git 提交/推送授权；前段历史授权仅适用于当时范围。
