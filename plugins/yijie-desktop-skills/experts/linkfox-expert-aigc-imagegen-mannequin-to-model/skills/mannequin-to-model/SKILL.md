---
name: mannequin-to-model
description: 通过当前已选择并授权的LinkFox工具，为公开HTTPS人台图片创建提词与单图生成任务，按原taskId查询并核对结果；没有服务时明确保持未生成状态。
---
## 目标
单张人台服装图转真人模特展示，保留款式与材料细节；本地制作说明与真实生成结果分开。
## 输入
已获用户明确外传许可的公开HTTPS图片直链、图像角色、模型、比例、分辨率及补充要求。
## 工作流
阅读ROLE与references/index.md，核对实际连接器资格和schema；本地构参→提词创建/查询→生图创建/查询→结果链接与保真核对。
## 工具
使用会话现有文件工具与当前已选择的LinkFox MCP；scripts/prepare_mannequin.py只构参/检查结果，不联网、不授予权限。
## 输出
真实taskId和状态、成功图片链接或明确缺项；需要文件时输出新的参数/inspection文件，不承诺自动落盘图片。
## 禁止行为
不自动上传本地文件、不发送反馈、不切full、不用直连HTTP代替MCP、不自动重发或轮询、不伪造成功/本地路径。
## 审批要求
账号授权与每次工具操作审批独立；创建、查询与外传范围由用户明确，未批准不执行。
## 示例
examples/request.json与examples/observations.json均为普通合成数据，不代表真实服务响应。
## 评测标准
见checklists/quality-checklist.md和evals/rubric.md；结构/本地测试不替代真实生成或图像质量验收。
