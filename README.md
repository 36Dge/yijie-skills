# yijie-skills

跨境电商 Codex Skills、Plugins、Prompt Packs 和 Evals 资产库。

## 本地开发

```bash
pnpm install
pnpm lint
pnpm test
pnpm package
```

`pnpm package` 当前生成 FEAT-129 的确定性 Desktop `local-development` Catalog First Bundle：

```text
dist/skill-packages/
├── bundle-manifest.json
└── packages/
    └── yijie.content-marketing.copywriting-0.1.0.zip
```

Manifest 精确消费 `yijie-contracts` 0.5.1 的 `skill-bundle-manifest-v2`，包含五个分类共
38 项 Catalog 元数据（`5/9/7/9/8`）。其中 37 项为不携带源码和压缩包的
`catalog-only + blocked` 条目；唯一可安装项是重新编写的 model-only `copywriting`
0.1.0，不依赖网络、文件系统或外部工具。

契约 pin 与来源/许可边界分别见 `contracts/lock.json`、
`docs/provenance/source-audits/FEAT-129-catalog-38-source-audit.json` 和
`docs/provenance/copywriting-0.1.0.md`。当前所有产物仅限本地开发，不得改为
`desktop-release`、上传或随客户端发布，直至产品/法务补齐 `copywriting@0.1.0` 的
`desktop-distribution` 授权，并对其他条目逐项完成来源、许可和安全审核。

## 安全要求

不得放入真实商家数据、平台 token、cookie、订单、买家 PII 或财务数据。
