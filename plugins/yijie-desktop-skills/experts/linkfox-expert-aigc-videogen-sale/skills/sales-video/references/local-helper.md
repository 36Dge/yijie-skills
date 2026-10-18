# 本地程序协议
Python >=3.10，仅标准库。先检查 python3 --version；缺失时报告，不自动安装。实际已安装本专家目录是调用源，勿引用其他专家目录。

1. 阅读 examples/plan.json 结构，基于用户资料创建 plan.json。不要把样例当真实事实。image_urls 可空用于本地规划；有值必须是用户明确授权的公共 HTTPS 媒体直链（本版不接受签名query），程序不证明可达性。
2. `python3 -B <本专家>/scripts/sales_video.py prepare --input plan.json --output-dir proposals-v1`。必须在用户授权工作目录执行，output-dir 为尚不存在的直接子目录。产物4文件，receipt仅登记另外3个文件。
3. 展示 review.md 的三套方案后停止。收到用户“选择方案2”等消息，读取 proposals-v1/input.json 和 inspection.json，创建 selection.json：`{"plan": <原input完整对象>, "selection": {"plan_sha256": <inspection原摘要>, "scheme_id": 2, "user_message": <用户原话>}}`。不可自行补造原话；JSON记录不构成宿主审批权威。
4. `python3 -B <本专家>/scripts/sales_video.py video --input selection.json --output-dir production-v1`。得到 inspection.request 是交给现有 proxy_call 的准确参数，request_sha256 标识该请求。不要再由模型拼第二份prompt或强行修改voice。未调用工具前必须标 video_prepared_not_submitted。

brief字段全部显式：product_name/source_reference/language/sales_region/target_audience/actor字符串；claims=[{id,source_text,spoken_text,source_reference}]；unknowns字符串数组；image_urls数组；video={videoType,videoTime,aspectRatio,resolution,voice}，仅SEED可选isPro布尔。
schemes恰好3个，按序id=1/2/3，title和shots数组；shot={seconds:正整数,framing,claim_ids:[已确认id]}。framing为presenter_hold/product_closeup/tabletop/packshot；不同方案至少镜头结构不同，每套总秒数等于videoTime。口播由claim_ids从原译句合成，不允许在shot另塞自由事实。

观察命令：`observe --input observation.json --output-dir status-v1`。输入stage=create/query、request_sha256、source_operation_id、mcp_result（当前真实MCP返回）。query另带原created inspection对象creation；必须与同一请求和原taskId对应，source_operation_id指本次查询。创建/查询先对照Native工具记录和当前会话；本地文件不证明账户/审批真实性，不接收来源不明任务替代原记录。
响应不明确/冲突/缺taskId保持unknown；FAILED失败；PROCESSING等待；SUCCESS且一条video公共URL为video_link_ready。local_file始终null，quality=not_verified；签名URL/多视频结果本版不自动处理。每次新目录保留所有阶段输入，原文件不改写。
