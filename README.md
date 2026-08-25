# yijie-skills

跨境电商 Codex Skills、Plugins、Prompt Packs 和 Evals 资产库。

## 本地开发

```bash
pnpm install
pnpm lint
pnpm test
pnpm package
```

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
