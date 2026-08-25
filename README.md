# yijie-skills

跨境电商 Codex Skills、Plugins、Prompt Packs 和 Evals 资产库。

## 本地开发

```bash
pnpm install
pnpm lint
pnpm test
pnpm package
```

`pnpm package` 当前生成 FEAT-129 的确定性 Desktop `local-development` Skill Bundle：

```text
dist/skill-packages/
├── bundle-manifest.json
└── packages/yijie.content-marketing.copywriting-0.1.0.zip
```

首个代表 Skill 为重新编写的 model-only `copywriting` 0.1.0，不依赖网络、文件系统或
外部工具。契约 snapshot 与来源/许可边界分别见 `contracts/lock.json` 和
`docs/provenance/copywriting-0.1.0.md`。该候选仅获本地开发授权，不得改为
`desktop-release`、上传或随客户端发布，直至产品/法务补齐 Desktop 分发证据并完成不可变
Contracts pin。

## 安全要求

不得放入真实商家数据、平台 token、cookie、订单、买家 PII 或财务数据。
