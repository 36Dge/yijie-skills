# 来源审阅
market-researcher原版0.1.0共84文件/7技能，重新与WorkBuddy缓存比对一致。来源摘要及每类适配决定见docs/provenance/source-audits/FEAT-158-research-content-audit-v0.1.0.json。适配版0.1.0是易界独立内容版本，不与原版行为等同。
行业/竞争/同业/观察清单方法改写成短参考，统一中文与发行人披露优先。NeoData原token迁移/保存、自动pip和WorkBuddy专属HTTP不导入；WeStock混淆文件不执行、不声称逐行解混淆已审核；原Office整个子树不复制，排除受限模板、shim和缺失依赖。自有HTML/XLSX产物替代缺失note-writer/comps示例工作簿，DOCX/PPTX未实现。
使用现有金融/搜索连接器，不假称NeoData/WeStock等价覆盖。当前Tushare仅daily受限适配，其他财务查询必须当前金融MCP资格和schema；无账号真实数据/搜索/模型验证NOT RUN。
仅用户授权本机local-development，release=false；原角色资料再分发许可未核实。所有示例合成，无真实商家/证券账户/凭据，源码摘要不构成发布授权。
