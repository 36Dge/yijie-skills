# 第四组实施后代码审查

2026-10-17；范围：口播0.1.0、精确包/来源、正常协议回归、consumer与旧资源保护。本审查在实现后单独执行，是Codex代码审查，不冒充Owner独立人工批准。

## 发现并处理

- `observe`对普通creation值类型缺少检查可能输出Python traceback：补dict检查并以受控输入错误退出；不生成成功产物。
- 增加64资源后，Native/启动器测试仍期望63/第三组路径：更新精确集合与路径。Host新增组的白名单、原安装保护及生命周期各自完整覆盖；发现旧coexistence测试只接受到第二组修订，第三组实际会跳过，本次同时补third/fourth条件，让该旧版本保护真实执行，不将skip算通过。
- 新完整63资源baseline固定为既有0.17.0manifest摘要；保留所有旧冻结文件。新增1专家而非替换0.1.0旧资源或缩减目录。

## 逐函数/边界结论

本地程序读取<=2MiB普通JSON，显式字段和类型、事实ID唯一、三个不同方案、已确认引用、正整数镜头秒数及总时长校验；缺值不补造。不可把这些检查当商品事实/翻译语义真伪判定，角色要求逐句复核并把unknown独立呈现。

video重算完整plan摘要，与用户选定原内容对照；仅从原claim译句组成口播，不另接受自由prompt。选择原话是审阅材料而非机器权威，收费仍走Native/Host/Worker原审批。输入假称用户选择的风险由实际会话和当前授权复核，不把JSON字段当鉴权。

本地支持严格参数子集、明确voice true，拒绝冲突与未审参数；无自动模型映射/降级/截断。prompt2000字符、UTF8请求16KiB保持。image URL只做保守语法范围校验，不声称远端可达或官方服务支持；账号实际资格与当前schema由原connector边界继续检查。

观察器不调用网络，对MCP isError、结构/文本冲突、非200、任务缺失/不匹配、未知/失败都不假成功。成功URL≠本地文件，质量状态不误报；原created记录与request摘要、当前操作引用和taskId对齐。多结果/带query签名URL未自动处理，明确不支持而非从URL截掉签名。没有本地上传/下载、后台轮询、反馈或第二业务数据库。

文件输出new directory，无覆盖原件/旧稿；回执是另外三文件的实际hash/bytes；sys.dont_write_bytecode及文档-B防安装包缓存漂移。磁盘不可写等真实异常只报告不假成功，未人为制造故障；未执行强杀、权限破坏、攻击fixture和运行时替换。

Connectors仅添加普通in-process测试和由helper生成的合成request fixture，不改生产执行协议、权限、OAuth、重试或风控。生产generic risk=write、exact ref/fresh decision既有正常回归复验。测试服务使用内存duplex正常close/join，未请求example.com或真实业务。当前provider onlinequalification维持原状态。

## 仍须真实验收

实际App prepare/绑定/等待选择/第二轮/文件读回、系统应用打开、旧记录保留与同构建重开；独立核对口播和制作参数。无账号线上生成、音轨/口型/费用继续NOT RUN。普通协议成功不能代替上述线上证据。

## 实际验收补记
后续两轮真实Kimi-K3/max会话及10份新文件通过；模型自写核验曾读错plan字段，同轮更正并重算成功，未修改正确产物。全工作区lint、标准App更新、旧20会话/53turn/全部旧安装内容保留和同构建重开通过。完整证据见元仓FEAT-158/33及Desktop本轮handoff-status.json。上述线上NOT RUN边界不变。
