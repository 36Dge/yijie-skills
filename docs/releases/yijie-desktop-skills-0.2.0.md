# YiJie Desktop Skills 0.2.0 local candidate

## Contract impact

`semantic`：本仓从单项 Manifest v1 生产者升级为 Catalog First Manifest v2 生产者。公共
结构由权威仓 `yijie-contracts` 定义，本仓只精确消费，不另行定义跨仓接口。

- Contracts version: `0.5.1`
- immutable commit: `164b14f609537d727a52326832da04430aecc4ab`
- Manifest v2 SHA-256: `39a898111ba3dcae2f369fdcb571a2e892830d1d0a57c90ab6210a0ab897a649`
- legacy Manifest v1 SHA-256: `d86185a1d5f4d9a136c88b679d50ac3e83bcc2b722eee39cba674c5be3b88469`

## Candidate contents

- 38 个稳定 Catalog 条目，分类数量为 `5/9/7/9/8`；
- 1 个 `bundled + installable` 本地开发包：`copywriting@0.1.0`；
- 37 个 `catalog-only + blocked` 元数据条目，不含源码、入口或压缩包；
- 所有 blocked 条目均记录来源摘要、许可状态、风险、能力依赖与 `iconKey`；
- bundle 源摘要覆盖完整公共 Catalog 投影和唯一压缩包摘要。

本次只执行确定性结构测试与合成 eval 数据校验，不声称已完成真实模型质量评测、Agent Host
conformance、Marketplace 发布或客户端分发。

## Distribution blocker

`copywriting@0.1.0` 当前只有 `local-development` 授权。取得经产品/法务确认的
`desktop-distribution` 许可及可审计证据前，不得切换到 `desktop-release` 或随客户端安装包
分发。上游缓存中的 `official` 标记不构成许可证明。

## Delivery and rollback order

候选交付顺序为：不可变 Contracts 0.5.1 → Skills 0.2.0 → Agent Host 精确消费 → Tauri →
Desktop UI。回滚时按相反顺序停止下游消费，再回退 Skills 候选；不得删除或改写已被下游锁定
的 Contracts 提交。
