# YiJie Desktop Skills 0.3.0

## Outcome

FEAT-129 的 38 项 Skill 已从 Catalog First 展示候选升级为本地与正式桌面渠道均可安装、
可发现、可调用的确定性资源包。分类数量保持 `5/9/7/9/8`，不存在
`catalog-only`、`blocked` 或 `skill_not_installable` 产品条目。

## Contract impact

`semantic`：Manifest 仍精确消费权威 Contracts 0.5.1 v2，但产品投影从 1 个 installable
条目变为 38 个 installable 条目。公共 Schema 没有变化。

- Contracts version：`0.5.1`
- immutable commit：`164b14f609537d727a52326832da04430aecc4ab`
- Manifest v2 SHA-256：`39a898111ba3dcae2f369fdcb571a2e892830d1d0a57c90ab6210a0ab897a649`
- Plugin/Bundle version：`0.3.0`

## Ownership and redistribution

FEAT-129 产品与仓库所有者提供了覆盖精确 38 个稳定 ID 的声明
`FEAT-129-DESKTOP-DISTRIBUTION-2026-08-25`，授权保存、修改、打包、安装、执行及随易界 AI
桌面客户端再分发，覆盖 `local-development` 和 `desktop-release`。

许可表达式统一为
`LicenseRef-YiJie-Desktop-Distribution-Owner-Attestation`，Manifest 授权范围为
`desktop-distribution`。原始缓存中的 `official` 字段没有被当作许可依据。

## Source and security review

- 37 项采用用户提供目录中的源码快照，并增加包内 Desktop 分发 NOTICE；
- `copywriting@0.1.0` 保留易界自研的较窄 model-only 实现；
- 共 258 个文件进入确定性打包；
- `.DS_Store` 和抓取调试页 `amz-hot-keywords/scripts/debug_page.html` 被排除；
- 逐项固定原始 `SKILL.md` 摘要、打包后 `SKILL.md` 摘要、完整包树摘要和 Archive 摘要；
- 安全门覆盖安全相对路径、常规文件、符号链接、秘密模式、Frontmatter 名称、Python 纯语法、
  网络/Shell/Cookie/文件系统及高影响经营能力分类；
- 审核不执行 Skill 脚本、不安装依赖、不访问真实账号或商家数据。

网络、Shell、文件写入和外部平台状态变更仍由 Agent Host 的权限、批准、路径隔离及审计机制
控制；这不会改变 Skill 的安装和 Runtime 可见状态。

## Build and rollback

- 本地：`pnpm package`
- 正式桌面：`pnpm package:desktop-release`
- 验证：`make lint && make test && make package && make package-desktop-release`

交付顺序保持 Skills → Agent Host 精确消费 → Tauri 资源打包 → Desktop UI。回滚时按相反顺序
停止下游消费并回退 Bundle 版本，Contracts 0.5.1 的不可变提交不删除、不改写。
