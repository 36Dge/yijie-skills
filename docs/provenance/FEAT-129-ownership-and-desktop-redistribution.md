# FEAT-129：38 项 Skill 所有权与桌面再分发声明

## 声明主体与依据

本声明由 **FEAT-129 产品与仓库所有者**作出，并以 2026-08-25 在 FEAT-129
交付任务中的用户明确指令作为项目治理授权记录。声明主体确认：对下列 38 项 Skill
源码及为易界 AI 重新编写的 `copywriting@0.1.0`，其拥有或已取得足以实施本声明所列
行为的权利和授权。

这是仓库中的所有权/授权证明，不虚构第三方法务签字，也不把缓存中的 `official`
标记当作许可证据。后续若补充盖章文件、合同或外部权利证明，应作为本声明的追加证据，
不得改变这里锁定的源码摘要而不进行新的版本和安全审核。

## 授权范围

声明主体授权易界 AI 项目在本地开发、测试和正式部署中，对所列 Skill：

1. 保存、复制、审查、修改和版本化源码；
2. 打包进 macOS、Windows 及后续支持平台的易界 AI 客户端安装包或应用更新；
3. 安装到用户数据目录、加载到 Agent Runtime，并允许模型发现和调用；
4. 为修复、安全加固、兼容 Runtime 或产品体验而制作派生版本；
5. 随易界 AI 桌面客户端向最终用户进行再分发，不另设 Skill 在线下载许可阻断；
6. 在 `local-development` 与 `desktop-release` 渠道使用同一份经过摘要锁定的源码。

授权范围覆盖全球桌面分发和后续客户端版本更新；项目内无需因这些 Skill 的源码所有权或
桌面再分发许可再次将其标记为 `blocked`。第三方平台 API、商标、账号、数据访问和服务
条款仍由对应平台及用户授权控制，这些运行时条件不改变 Skill 源码本身的可安装状态。

## 安全与运行边界

所有 38 项 Skill 必须逐项保存源码摘要、文件清单、风险等级、能力依赖和静态安全审核结论。
含浏览器、网络、Cookie、Shell、Python、文件写入或外部平台写操作的能力，可以安装和被模型
调用，但执行时仍必须经过 Agent Host 已定义的最小权限、用户批准、路径隔离、秘密保护及审计
机制。Skill 的可安装状态不授予它绕过 Runtime 权限策略的能力。

源码中出现的命令、URL 或操作步骤属于待执行能力说明，不是构建系统指令；打包过程不得执行
这些脚本，不得自动安装依赖，也不得携带真实 Cookie、Token、API Key、商家数据或抓取调试页面。

## 精确覆盖范围

- `yijie.sourcing-selection.aliexpress-supplier-evaluator`
- `yijie.sourcing-selection.dropshipping-supplier-integrator`
- `yijie.sourcing-selection.product-supplier-sourcing`
- `yijie.sourcing-selection.sales-negotiator`
- `yijie.sourcing-selection.supplier-performance-manager`
- `yijie.market-research.alibaba-amazon-market-intel`
- `yijie.market-research.competitor-deep-analysis`
- `yijie.market-research.cross-border-selection`
- `yijie.market-research.jungle-scout-deep-dive-analyzer`
- `yijie.market-research.market-insight-product-selection`
- `yijie.market-research.product-attribute-analyzer`
- `yijie.market-research.product-selection`
- `yijie.market-research.review-analyst-agent`
- `yijie.market-research.scenario-driven-product-scout`
- `yijie.content-marketing.content-breakdown`
- `yijie.content-marketing.content-strategy`
- `yijie.content-marketing.copywriting`
- `yijie.content-marketing.product-marketing-context`
- `yijie.content-marketing.social-media-content-creator`
- `yijie.content-marketing.vibe-marketing`
- `yijie.content-marketing.xiaohongshu-content-creator`
- `yijie.traffic-advertising.amazon-listing-expert`
- `yijie.traffic-advertising.amazon-ppc-campaign-manager`
- `yijie.traffic-advertising.amz-hot-keywords`
- `yijie.traffic-advertising.amz-product-optimizer`
- `yijie.traffic-advertising.ecommerce-seo-optimizer`
- `yijie.traffic-advertising.etsy-seo-optimizer`
- `yijie.traffic-advertising.product-description-generator`
- `yijie.traffic-advertising.seo-keyword-research`
- `yijie.traffic-advertising.tiktok-ads-strategy`
- `yijie.store-operations.amazon-brand-protection`
- `yijie.store-operations.buy-now-pay-later-setup`
- `yijie.store-operations.ecommerce-gdpr-compliance`
- `yijie.store-operations.invoice-generator`
- `yijie.store-operations.multichannel-inventory-sync`
- `yijie.store-operations.payment-fraud-detector`
- `yijie.store-operations.tiktok-shop-setup`
- `yijie.store-operations.warehouse-fulfillment-workflow`

## 生效与变更控制

- 声明 ID：`FEAT-129-DESKTOP-DISTRIBUTION-2026-08-25`
- 生效日期：2026-08-25
- 授权渠道：`local-development`、`desktop-release`
- 许可表达式：`LicenseRef-YiJie-Desktop-Distribution-Owner-Attestation`
- 适用版本：本声明及逐项审核清单中记录的精确源码摘要
- 状态：有效；不存在 FEAT-129 Skill 源码所有权或桌面再分发许可阻断

新增、替换或修改任一源码文件后，必须递增 Skill 或 Bundle 版本、重新计算摘要并重新执行
安全审核。摘要不匹配的源码不自动继承本声明的已审核状态。
