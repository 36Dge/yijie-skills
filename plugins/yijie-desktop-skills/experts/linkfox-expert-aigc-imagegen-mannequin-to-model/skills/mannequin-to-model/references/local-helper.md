# 本地构参与回执检查
Python 3.10+标准库，无联网/服务API/凭据读取、没有依赖安装。执行使用当前会话原有工具与权限；找不到Python或执行工具时明确未运行。

将用户已授权直链与明确选项写成examples/request.json同形状的普通JSON，再在当前任务工作目录运行：
`python3 <本包绝对路径>/scripts/prepare_mannequin.py prepare --input request.json --output-dir prepared-01`
输出input.json保留原字节，inspection.json含提词请求草稿与生图选项。prepared_not_submitted及current_tool_schema_verified=false是准确状态，不能据文件存在宣称已发送。调用前核对当前服务schema并逐次审批。

将原生工具的实际MCP结果保存为observation.json。stage取create_text/query_text/create_image/query_image；source_operation_id来自该次实际工具调用；查询需expected_task_id来自原创建回执。query_text成功时还需同一制作单preparation对象：
`python3 <本包绝对路径>/scripts/prepare_mannequin.py observe --input observation.json --output-dir observed-01`

结果仅做格式/身份/状态核对，不证明数据的网络来源。isError/业务错误、冲突来源、缺taskId、taskId错配、未知状态或无单图结果均不得报成功。text_ready保留content全文和换行，给出待批准的生图请求；image_link_ready仅提供实际公开链接，local_file=null、visual_fidelity=not_verified。PROCESSING不触发查询或创建。临时签名URL拒绝写入此长期工作产物，保留原工具历史，勿删除query伪造永久URL。

只允许在当前工作目录下创建新输出子目录；不覆盖已有目录、输入、旧记录或历史版本。input_sha256用来定位原始材料，不是服务证明。URLs仅作语法检查，不探测可访问性、版权或公开状态。不得从input.json中复制任何凭据；正常MCP结果应已经沿产品边界过滤。
