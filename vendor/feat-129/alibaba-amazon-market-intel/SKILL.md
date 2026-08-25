---
name: alibaba-amazon-market-intel
description: >-
  Amazon market data toolkit powered by Jungle Scout MCP. 6 APIs, 42 sub-modules
  covering keyword search volume, reverse-ASIN, sales estimates, product database
  filtering, and brand share of voice.

  Use when the user asks for a SINGLE Amazon data point or one-dimensional analysis:
  - Keyword search volume / trend / seasonality
  - Reverse-ASIN keyword research, competitor gap analysis, listing/SEO audit
  - ASIN sales & revenue estimation, stock-out detection, promo impact
  - Keyword expansion, PPC bid analysis, cross-market comparison
  - Product database filtering: niche discovery, category sizing, brand intel
  - Share-of-voice on search results pages, ad effectiveness

  Do NOT use for:
  - Non-Amazon platforms; logistics / payment / legal questions
  - General knowledge questions that need no real data
  - Supply-chain / factory / 1688 / Alibaba.com sourcing
  - Tasks where the user already has data and just needs charts
  - End-to-end deep-dive product-selection reports → use `jungle-scout-deep-dive-analyzer`
workflow: |
  Pipeline:
    1. Read reference/help.md → pick API + sub-module
    2. Read the sub-module reference for full instructions
    3. Call the MCP tool (see Quick Reference) → save JSON
    4. Run the matching analysis script → CSV + insights
    5. Output results directly in the conversation
---

# Amazon Market Intel

Amazon 市场数据分析工具集，基于 Jungle Scout MCP 工具，包含 6 个 API、42 个子模块。

> ★★★ **ABSOLUTE RULE — RESULTS MUST BE OUTPUT DIRECTLY IN THE CONVERSATION** ★★★
>
> 1. Analysis results (tables, charts, insights) MUST be output as markdown directly in the chat — NOT only written to files
> 2. CSV files are saved as intermediate data for reference, but the key findings MUST appear in the conversation
> 3. Do NOT use `submit_result` — it does not exist in this framework

> ⛔ **禁止跳过 Step 1-2 直接写脚本。** 必须先读 `reference/help.md` 选择子模块，再读子模块 reference 文件获取已有脚本的调用方式。42 个子模块都有现成的分析脚本，禁止自己从头写分析脚本。
> ⛔ **禁止写 .py 文件来分析数据。** MCP 返回的 JSON 数据应通过已有脚本处理（见子模块 reference 的 Usage 节）。如果已有脚本因环境问题失败，Agent 应直接在内存中用 JSON 数据生成分析结果并输出到对话中，不要写中间 .py 文件。

---

## MCP 工具速查表

所有工具均通过 MCP 工具名直接调用，**工具名即为调用标识，无需额外指定 Server**。

> ⛔ **禁止通过搜索发现工具。** 所有工具名已在本文档中列出，禁止使用 `accio-mcp-cli search` 或任何搜索命令查找工具。

### 调用方式

通过 `accio-mcp-cli call <工具名>` 直接调用，入参用 `--json` 传递。具体参数见 `reference/setup.md` 和对应子模块 reference 文件。

| MCP 工具名（直接调用） | 用途 | 必填业务参数 |
|------------------------|------|------------|
| `js_keywords_by_keyword` | 关键词搜索量、竞争度、长尾拓展 | `search_terms`, `marketplace`, `page_size` |
| `js_keywords_by_asin` | 反查 ASIN 流量关键词 | `asins` (List), `marketplace`, `page_size` |
| `js_historical_search_volume` | 历史搜索趋势（周粒度） | `keyword`, `start_date`, `end_date`, `marketplace` |
| `js_sales_estimates` | ASIN 销量估算（日粒度） | `asin`, `marketplace` |
| `js_product_database_query` | 产品数据库筛选 | `include_keywords` (List), `categories` (List), `marketplace`, `page_size` |
| `js_share_of_voice` | 品牌声量份额 | `keyword`, `marketplace` |

### API → MCP 工具名映射

| API 组 | 对应 MCP 工具名 | 子模块数 |
|--------|----------------|---------|
| ① Historical Search Volume | `js_historical_search_volume` | 6 |
| ② Keywords by ASIN | `js_keywords_by_asin` | 8 |
| ③ Sales Estimates | `js_sales_estimates` | 5 |
| ④ Keywords by Keyword | `js_keywords_by_keyword` | 8 |
| ⑤ Product Database | `js_product_database_query` | 9 |
| ⑥ Share of Voice | `js_share_of_voice` | 6 |

---

## How to Use

### Step 1: Select API and Sub-Module (MANDATORY — DO NOT SKIP)

Read `read_file('reference/help.md')` — 根据用户意图选择 6 个 API 中最匹配的一个，再选择具体子模块。

> ⛔ 即使你认为已经知道该用哪个 API，也必须读 help.md 确认子模块选择。

### Step 2: Read Sub-Module Reference (MANDATORY — DO NOT SKIP)

Read 对应子模块的 reference 文件（路径见 help.md 中的表格），获取 When to Use、Usage 脚本调用方式、Output Files 定义。

> ⛔ 子模块 reference 文件包含已有脚本的 import 路径和调用方式。不读就不知道怎么调用已有脚本。

### Step 3: Fetch Data & Run Analysis

按子模块 reference 文件中的指引完成数据获取和脚本执行。工具调用方式、参数格式、import paths 等详见：
- **工具调用与参数格式** → `reference/setup.md`
- **具体脚本用法** → 对应子模块 reference 文件的 Usage 节

> ⚠️ **两层参数禁止混淆**：reference Usage 中 MCP 调用参数（`asins` 列表、`page_size`、`start_date`/`end_date`）与脚本分析参数（`mcp_data`、`output_dir`、标签字符串）是两层，详见 `reference/setup.md` "MCP 层参数 vs 脚本层参数" 节。

> ⚠️ **脚本失败 fallback**：如果分析脚本因 `ImportError`（pandas/numpy 不可用）失败，**不要写任何 .py 文件**。改为 `read_file` 读取 MCP 保存的 JSON，Agent 直接在回复中分析数据并输出结果。详见 `reference/setup.md` "Fallback" 节。

### Step 4: Output Results

将分析结果（表格、洞察、关键发现）直接输出在对话中。CSV 文件作为完整数据的参考。

---

## Examples

### 示例 1: 关键词拓展

用户问："Find all keywords related to excavator"

1. 匹配 API ④ Keywords by Keyword → 子模块 Keyword Expansion
2. `read_file('reference/keywords_by_keyword/keyword-expansion.md')`
3. 按 reference 文件指引获取数据、运行脚本
4. 输出关键词表格（搜索量、PPC 竞价、排名难度）到对话中

### 示例 2: ASIN 反查关键词

用户问："What keywords does B0XXXXXX rank for?"

1. 匹配 API ② Keywords by ASIN → 子模块 Reverse ASIN Research
2. `read_file('reference/keywords_by_asin/reverse-asin-research.md')`
3. 按 reference 文件指引获取数据、运行脚本
4. 输出 ASIN 的流量关键词排名表到对话中

### 示例 3: 品牌声量份额

用户问："Who dominates the search results for portable blender?"

1. 匹配 API ⑥ Share of Voice → 子模块 Brand Market Share
2. `read_file('reference/share_of_voice/brand-market-share.md')`
3. 按 reference 文件指引获取数据、运行脚本
4. 输出品牌 SOV 占比表到对话中

---

## Common Notes

- **Search Volume modules**: Max 5 keywords, date range up to 366 days, 7-day granularity
- **ASIN modules**: Max 10 ASINs (some modules limit to 5), page_size max 100
- **Sales Estimates modules**: Max 10 ASINs, date range up to 365 days, daily granularity, `end_date` ≤ yesterday
- **Keyword modules**: Max 10 seed keywords (some modules limit to 5), page_size max 100
- **Product Database modules**: Max 50 results per call; `categories` and `include_keywords` must be JSON arrays
- **Share of Voice modules**: Covers top 3 pages of Amazon search results

### 用户呈现原则

- 以 Amazon 市场分析师的口吻呈现洞察
- 不要向用户暴露内部工具名、API 参数结构、环境变量名等内部细节
- 数据来源表述为"Jungle Scout 市场数据"或"Amazon 平台数据"

---

## Next Steps

- **Module selection guide** → `reference/help.md`
- **Import paths & output conventions** → `reference/setup.md`
- **Sub-module reference files** → `reference/<api_name>/<module>.md`

## 错误处理与降级交付

当 Jungle Scout MCP 调用失败、分析脚本异常或额度受限时，**禁止只说"无法完成"**，必须按以下降级路径输出可用产物：

- **MCP 工具单点失败（任一 js_* 接口）：** 自动重试一次。仍失败时：
  - 告知用户具体接口名 + 错误码（如 `js_keywords_by_keyword: 503`）。
  - 若用户问题可由其他接口部分回答（如关键词扩展失败但 ASIN 反查可用），主动切换到可用接口给出"近似分析"，并标注"⚠️ 由于 X 接口不可用，本次分析基于 Y 接口的近似数据"。
  - 不要因单接口失败就放弃整次任务。

- **分析脚本失败（ImportError / 数据格式异常）：** 已在 SKILL.md 主流程定义"内存中分析"fallback。补充约束：
  - Agent 必须直接读取 MCP 保存的 JSON 文件（`read_file`），用 markdown 表格在对话中输出 Top N 关键发现，至少包含 3 行核心数据 + 1 段洞察。
  - 不要写任何 .py 中间文件，禁止只回复"脚本失败"。

- **数据为空/查询无结果（如某 ASIN 不存在、某关键词无搜索量数据）：**
  - 明确告知用户"该 query 在 Jungle Scout 数据库中无匹配记录"，并主动建议 2-3 个相近改写（同义词 / 上位类目 / 相关品牌）。
  - 输出"零结果场景的诊断建议"：是否拼写问题、是否需要扩大 marketplace、是否产品过新尚未被收录。

- **额度/权限不足（i-Coin 不足、Jungle Scout 未开通）：** Step 3 调用 MCP 前若检测到额度不足：
  - 立即告知具体限制 + 当次预估消耗。
  - 提供"轻量降级"：使用 `info_search(mode="shopping")` + `info_search(mode="web")` 替代部分 Jungle Scout 数据（仅适用于产品级搜索、关键词概念性查询，不适用于精确销量/搜索量分析），并明确标注数据精度差异。
  - 给出 Jungle Scout 开通入口 https://www.junglescout.com/ 作为长期方案。

- **能力边界前置告知：** 用户问题涉及非亚马逊平台、物流/支付/合同/法律、用户已有数据仅需绘图等场景时，按 description 中"禁止使用场景"立即告知"本 skill 不处理该类问题"，并引导用户切换到相应能力，禁止勉强调用 Jungle Scout 后无意义返回。

- **结果展示完整性兜底：** 即便走了任何降级路径，最终回复必须满足：(a) 包含至少 1 个数据表格或关键发现列表；(b) 标注数据来源与降级原因；(c) 给出 1 条可执行的下一步建议。禁止只回复"已尝试但失败"。

