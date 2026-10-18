# 产物与依赖
生产资源仅Python3标准库，不新增pip/npm/浏览器/Office依赖；不执行NeoData脚本、WeStock打包器或原pptx-author资源。
实际生成report.html（完整研究稿、所有公司表、离线SVG收入对比、证据/缺项）与comps.xlsx（Comps、Evidence、Sources、Method四页，真实公式和缓存结果）。Office写出机制复用易界自有local-quotation的标准OOXML结构，独立打包，不依赖另一专家是否安装。原数值/scale/来源/口径与问题保留，长源正文分段不丢弃；输入原字节另存。
XLSX输入值保留Decimal规范化精度，公式引用对应行；N/A/NM不会伪装成零或空盈利。打开Excel/Numbers后可编辑重算；报告与表格都是研究草稿，不自动发布。初始计算不调用外部Office引擎，需有对应软件才能交互重算。
本版未实现DOCX/PPTX/机构模板导出；原PPT工具限制性来源与LD_PRELOAD机制均排除。用户明确要这些格式时说明当前缺能力，不重命名HTML冒充Office，不自动下载或安装工具。HTML可独立阅读，原研究内容与表格仍可实际交付。
