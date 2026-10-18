# 输入与执行协议
Python3.10+，全部普通文件；运行`python3 -B`禁止在受管资源生成缓存。路径以当前实际安装目录为准，不硬编码另一专家路径。

读取 examples/input.json 了解完整形状。research_id/revision明确；mode为offline或connector-evidence；scope固定industry/geography/boundary/currency/year/as_of。plan含decision/depth/questions/steps。sources保留id/kind/title/locator/published_on/retrieved_on/content；资料正文每条最长4000字符，可按页/段拆来源。facts逐条id/source_id/quote/value/unit/year/geography/boundary/status/limitation，value数字字符串或null；无凭空0。calculations只接受market-size/growth/concentration/weighted-score及示例所列确切字段；所有引用事实需口径匹配。findings有id/kind/text/fact_ids/limitations/next_action；数值使用{{calc:size:TAM}}这类已存在指标模板，并引用计算所用全部事实。gaps明确缺口，formats按实际需求从html/xlsx/docx/pdf/pptx选择，默认html。

```text
python3 -B <安装目录>/scripts/research.py freeze --state <工作区>/research-state.json --out <工作区>/frozen-v1
python3 -B <安装目录>/scripts/research.py deliver --frozen <工作区>/frozen-v1/frozen.json --out <工作区>/delivery-v1
python3 -B <安装目录>/scripts/research.py verify --delivery <工作区>/delivery-v1 --state <工作区>/research-state.json
```
PDF时deliver追加`--soffice <已明确的现有正常LibreOffice soffice绝对路径>`。不自动寻找/安装/联网下载，不用源包soffice.py或shim。所有out必须是已存在工作区下的全新目录；不写安装资源，不覆盖输出。

研究更新：读取原状态与来源，保存research-state-v2.json并更新revision，修改假设时也修改source.content/quote等真实证据记录；只有用户确实改变的假设可变。另存frozen-v2/delivery-v2，verify当前状态。旧state/frozen/receipt不改。用v2校验v1应报告过期，这是正常业务校验而不是破坏文件。
