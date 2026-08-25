# Common Prerequisites — Setup Guide

> ⚠️ Read this before executing any sub-module.

---

## Data Fetching via MCP

所有工具均通过 MCP 工具名直接调用，**工具名即为调用标识，无需额外指定 Server**。

> ⛔ **禁止通过搜索发现工具。** 所有工具名已在本文档中列出，通过 `accio-mcp-cli call <工具名>` 直接调用。禁止使用 `accio-mcp-cli search` 或任何搜索命令查找工具。

### Available MCP Tools

| MCP 工具名（直接调用） | 用途 | 必填业务参数 |
|------------------------|------|------------|
| `js_keywords_by_keyword` | 关键词搜索量、竞争度 | `search_terms`, `marketplace`, `page_size` |
| `js_keywords_by_asin` | 反查 ASIN 流量关键词 | `asins` (List), `marketplace`, `page_size` |
| `js_historical_search_volume` | 历史搜索趋势 | `keyword`, `start_date`, `end_date`, `marketplace` |
| `js_sales_estimates` | ASIN 销量估算 | `asin`, `marketplace` |
| `js_product_database_query` | 产品数据库筛选 | `include_keywords` (List), `categories` (List), `marketplace`, `page_size` |
| `js_share_of_voice` | 品牌声量份额 | `keyword`, `marketplace` |

### Passing Data to Scripts

MCP returns a JSON string. Save it to a file, then pass to the script:

```python
import json
# mcp_result is the raw JSON string from the MCP tool call
data = json.loads(mcp_result) if isinstance(mcp_result, str) else mcp_result

# Pass to analysis function
from <module> import <function>
result = <function>(mcp_data=data, output_dir="/round-{N}/data")
```

### ⚠️ MCP 层参数 vs 脚本层参数（禁止混淆）

两层参数**职责完全不同**，禁止混入对方的调用中：

| 层 | 参数举例 | 传给谁 | 作用 |
|---|---|---|---|
| **MCP 调用层** | `asins`(列表), `page_size`, `start_date`, `end_date`, `marketplace`, `search_terms`, `categories` | `accio-mcp-cli call js_*` | 控制 API 请求范围和返回量 |
| **脚本分析层** | `mcp_data`, `output_dir`, `asin`(单字符串), `keyword`, `seed_keyword` | Python 分析函数 | 处理返回数据 + 输出标签 |

- 脚本中的 `asin`/`keyword`/`seed_keyword` 等字符串参数**仅作为 CSV 标签列**，不会发起 API 请求
- `page_size`、`asins`(列表)、`start_date`/`end_date` 属于 MCP 层，**不传给分析脚本**
- 特殊情况：`keyword_gap_analysis` 和 `listing_quality_auditing` 需要**两次 MCP 调用**的结果作为两个独立参数

### ⚠️ Fallback: 脚本因 pandas/numpy 不可用而失败时

运行环境可能缺少 pandas 或 numpy（签名问题、未安装等）。如果脚本报 `ImportError: Unable to import required dependency numpy` 或类似错误：

1. **不要再写任何 .py 文件** — 不要写依赖 pandas 的脚本，也不要写"纯标准库版"的 .py 文件
2. **直接在内存中处理数据**：用 `read_file` 读取 MCP 保存的 JSON，在 Agent 回复中直接分析并输出结果
3. 参考子模块 reference 文件中 "Execution Steps" 的计算逻辑，Agent 自己做计算
4. MCP 响应结构：`{"data": [{"id": "us/B0XX", "type": "...", "attributes": {...}}, ...]}` — 遍历 `data` 数组，取 `item["attributes"]` 中的字段

正确做法示例：
```
1. accio-mcp-cli call js_product_database_query → 结果自动保存到文件
2. read_file 读取自动保存的结果文件
3. Agent 在回复中直接分析数据（排序、统计、生成表格）并输出到对话
```

错误做法：
```
❌ write_file 保存 MCP 结果（框架已自动保存）
❌ 写任何 .py 文件来处理数据
```

---

## Import Paths

Sub-module reference snippets use `{SKILL_DIR}` as a placeholder. Before running, the
agent MUST substitute it with the actual install path — typically:

```
${account_skills}/alibaba-amazon-market-intel
```

(`${account_skills}` is defined in the agent system prompt; it expands to
`~/.accio/accounts/<account-id>/skills/`. If installed as an agent-level skill,
use `${agent_skills}/alibaba-amazon-market-intel` instead.)

Template form found in every sub-module reference:

```python
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/<api_name>')
# api_name: historical_search_volume | keywords_by_asin | sales_estimates
#           | keywords_by_keyword | product_database | share_of_voice
```

---

## Round Directory

> All output paths use `round-{N}`, where `{N}` is the current round number.
> Do not hardcode `round-1`.

---

## Common Notes

- **Search Volume modules**: Max 5 keywords, date range up to 366 days, 7-day granularity
- **ASIN modules**: Max 10 ASINs (some modules limit to 5), page_size max 100
- **Sales Estimates modules**: Max 10 ASINs, date range up to 365 days, daily granularity, `end_date` ≤ yesterday
- **Keyword modules**: Max 10 seed keywords (some modules limit to 5), page_size max 100
- **Product Database modules**: Max 50 results per call; `categories` and `include_keywords` must be JSON arrays
- **Share of Voice modules**: Covers top 3 pages of Amazon search results; returns both basic and weighted SOV metrics
- **Supported marketplaces**: us, uk, ca, de, fr, it, es, mx, jp, in
- **MCP authentication**: Handled server-side, no credentials needed
- **Parameter format**: `include_keywords` and `categories` MUST be JSON arrays (e.g., `["yoga mat"]`), not strings
- **ASIN format**: ASIN关键词工具 takes `asins` as a list (e.g., `["B0XXXXXX"]`)
- **Date format**: `start_date` and `end_date` must be YYYY-MM-DD strings

