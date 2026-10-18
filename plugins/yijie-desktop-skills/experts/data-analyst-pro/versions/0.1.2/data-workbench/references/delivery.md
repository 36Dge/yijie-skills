# 交付与打开
先读取实际输出并复算，确认可读且摘要与源一致。analysis.json/CSV可用现有文件打开能力；HTML是独立网页产物，不是Native Artifact。报告包含本地ECharts、亮暗切换、图表选择和同源表。
本机已有浏览器能力且用户要求打开时，可使用 scripts/preview.py --project <报告目录>，仅回环只读预览收据列出的报告文件；前台运行，输入stop或Ctrl-C正常结束。不得上传数据、建立隧道或读浏览器配置。没有工具权限如实标为NOT RUN；不通过改协议/代理绕过工具明确拒绝。
预览启动读取稳定快照；文件修改后正常停服、重新启动。真实浏览器记录URL、尺寸、亮暗状态、选择图表结果、控制台异常与截图。静态文件/脚本成功不代表浏览器成功。不要改写原receipt的NOT RUN；另写实际browser-verification.md证据。
复算命令见summary.md，使用另一全新目录；源快照名不同造成source.filename变化是预期，其SHA及其余结果必须一致。
