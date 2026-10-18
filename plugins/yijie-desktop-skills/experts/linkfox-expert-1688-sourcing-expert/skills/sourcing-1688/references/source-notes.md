# 来源审阅
来源为用户本机WorkBuddy安装的linkfox-expert-1688-sourcing-expert@2.2.0，44文件/14子技能，与用户10专家导出逐项校验一致。完整摘要和裁剪决策见docs/provenance/source-audits/FEAT-158-1688-content-audit-v0.1.0.json。原文件不改写、不执行。头像继续使用原本地UI资源。

保留来源中的商品/关键词/市场/货源检索方法与参数证据；重写原step_4_calc_profit.py，去掉ASIN历史首条回退、按文件顺序配货源、缺失SP词数→无广告、隐式汇率/费用/退货率、ACoS替代TACoS和竞品销量预计收益。标题筛选只能提示相关性，不能证明同款。原报告模板包含可注入脚本/CDN，不导入；新静态报告转义文本、无网络资源。原file-upload及自动反馈/JungleScout/skill-creator未接入。

公开官方LinkFox仓库树ea5581c8c727f259a4fa5ea3df00e7cec77bf5ce的6份API参考仅作字段交叉核对；HTTP参考不证明当前MCP账户/工具资格。Amazon官方https://sell.amazon.com/pricing说明费用取决于类目、履约与可选服务，本版不硬编码其当前费率。费率更新需引用实际适用时期资料。

许可证/桌面再分发范围未核实，仅当前用户授权的本机local-development，release=false。没有LinkFox账号，真实认证、当前schema、实际收费/数据/供应商/模型效果及App端到端验证NOT RUN。单元测试使用普通合成数据，不伪造真实验收。
