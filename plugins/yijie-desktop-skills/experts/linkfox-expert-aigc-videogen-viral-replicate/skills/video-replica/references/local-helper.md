# 无网络构参与核对
Python 3.10+标准库，无依赖安装/网关HTTP/凭据读取/下载器。通过本轮已有会话工具执行；没有Python或权限时说明未运行。

统一命令：`python3 <资源绝对路径>/scripts/prepare_video.py <action> --input <输入.json> --output-dir <新的工作子目录>`。每次input.json保留原输入字节，inspection.json记录状态与input_sha256；不能覆盖旧目录，不能输出到任务目录之外。

1. prepare：输入examples/request.json形状，得到brief_sha256、reference_request、product_request及显式视频选项。两个请求是待逐次批准的草稿，不是已提交。
2. observe：输入stage（create/query_reference/product/prompt/video之一）、source_operation_id、brief_sha256、实际mcp_result；查询另需expected_task_id来自原创建回执。输出created/processing/failed/unknown/text_ready/video_link_ready，绝不自动调用服务。text_ready的content原样保留。
3. compose：输入brief、reference_receipt、product_receipt；两个receipt均为observe的原始输入（实际MCP结果），不是助手自拟输出。核对独立任务、阶段、制作单摘要，再把分析原文及市场/时长放入替换提示词请求。
4. video：输入brief和prompt_receipt（原query_prompt输入）；只接受已完成文本内明确的JSON对象video_prompt/replacements，保留其prompt实际换行、主商品图顺序，形成视频创建草稿。超长/主体缺失/不支持参数停止，展示替换计划并等待实际调用审批。

本地摘要用于避免混用制作单，不是服务签名；source_operation_id/expected_task_id必须由Native工具历史核对，脚本不能证明网络来源、许可或审批。重开会话恢复原taskId，只查询。URL仅语法检查，不验证可访问性；临时签名URL不删query冒充永久链接，也不持久化到此辅助产物，改从原工具回执说明限制。本包没有上传、抽帧、下载或媒体验证。

构成proxy参数的完整JSON按UTF-8字节受现有16 KiB审批容量约束；中文字符与JSON转义均计入。超限时保留原分析/回执并停止，须明确精简草稿和复核，不自动截断、不换HTTP、不放宽Broker门禁。
