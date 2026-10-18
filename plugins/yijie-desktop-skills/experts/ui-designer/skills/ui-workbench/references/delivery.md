# 私有交付协议 v1
新目录保存brief.md（用户任务与明确假设）、index.html、styles.css、app.js、tokens.css、README.md和project.json。源文件只保存实际代码，不嵌入外部SDK/服务地址/密钥。所有执行JS放.js，禁止内联script/onclick；CSS可外部文件；资源链接为项目相对路径，使用本地普通文件，不使用symlink、远程字体/CDN或外部嵌入。
project.json字段：schema_version=1；mode="local-prototype"；title；brief="brief.md"；entry="index.html"；readme="README.md"；tokens="tokens.css"；brief_sha256、tokens_sha256（对实际原字节算SHA256）；files列明全部交付资产（无需列project.json自身）；asset_sources用每个files路径为key写真实来源；interactions为待验证的具体动作数组；states包含loading/empty/error/permission-denied/ready。README写每个状态的到达方式、真实/演示边界、操作说明、组件/token映射、依赖、限制。
`python3 <本包>/scripts/validate_project.py --project <页面目录> --output <页面之外的新回执目录>`。输出静态PASS与浏览器NOT RUN，不是安全沙箱或JS行为证明。不覆盖原receipt。所有文件引用检查、sourcehash齐全才可开始预览。
`python3 <本包>/scripts/preview.py --project <页面目录>`启动前台回环127.0.0.1随机端口服务，只提供manifest声明的快照文件，无列表，无写入/网络接口。标准输出给URL；在同一进程stdin输入stop或Ctrl-C正常退出。不要后台孤儿进程。文件修改后正常停服重启，不能以旧快照验收新文件。已有浏览器工具可用才打开该URL，不能用改协议/隧道绕过工具明确拒绝。
浏览器测试实际主流程、搜索无结果/清除、错误重试、表单校验与成功/取消、键盘Tab/Escape/焦点恢复、亮暗与宽窄屏，读取console并截图。浏览器工具不可用则交付静态部分并明确NOT RUN，不编造。另写browser-verification.md（在页面目录之外）记录实际URL/尺寸/操作/观测/问题修复，不能将脚本自报PASS当实际浏览器证据。
