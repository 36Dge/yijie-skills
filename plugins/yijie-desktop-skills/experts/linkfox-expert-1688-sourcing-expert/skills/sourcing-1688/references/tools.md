# LinkFox工具参考
仅通过当前已选择LinkFox的proxy_call，将以下业务对象直接放arguments。不要传Authorization、HTTP地址或WorkBuddy认证信息。本地prepare不表示已提交/已验证当前schema。市场数据和检索也可能收费，继续走现有write风险/ApproveOnce，不降低门禁。MCP错误、非200业务码、未知结构、空结果、额度不足均停止并保留原回执。

| toolName | 本版本明确参数 |
| --- | --- |
| keepa/productRequest | asin单个目标、domain字符串"1"、history=0 |
| keepa/productSeries | asin、domain="1"、days显式1..365 |
| sif/asinKeywords | asin、country="US"、timePieceType="latelyDay"、timePieceValue="7"、pageNum/pageSize=20 |
| sif/asinSummary | searchValue单ASIN、country="US"、last7d=true、pageNum/pageSize=20 |
| sellersprite/trafficKeyword | asin、marketplace="US"、page/size=20 |
| alibaba1688/imageSearch | imageUrl公开PNG/JPEG直链、page/pageSize=20 |
| dld/productSearch | keyWord中文品类词≤50字符、cycle="30"、searchType=1、pageIndex/pageSize=20 |
| amazon/search | keyword、amazonDomain="amazon.com"、language="en_US"、page |
| jiimore/getNicheInfoByKeyword | keyword、countryCode="US"、page/pageSize=20 |
| aiMode/googleSearch | keyword |

page默认为初始第1页，范围1..20，不自动翻页。少量分页是调用预算，不是财务假设；每页独立审批。网络失败不自动重试。source package示例里的domain=amazon.com/site=US与字段表有差异，按字段表的domain="1"和country="US"构参，实际服务仍需当前schema核实。

回执支持structuredContent或唯一text块JSON一次解析；普通code="200"和errmsg="ok"不是错误。供应商报价CNY，Keepa US价格USD；fbaFees原文“元”单位有歧义，本版不自动拿作observed成本。只在用户确认当前单位与条件后作为显式情景录入。代理请求完整UTF-8限16KiB，结果64KiB，超限不截断原证据，重新向用户提议较小范围。
