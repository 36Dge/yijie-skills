# LinkFox工具与异步流程
本包依赖单独连接的LinkFox服务。易界连接器负责OAuth、安全存储、完整工具发现及schema冻结。每轮显式选择服务并使用实际提供的工具名；服务的代理方法必须在当前schema/文档中确认，不能按旧WorkBuddy前缀猜调用。

来源对照的四个业务方法是aigc/textGenAsync、aigc/textTaskQuery、aigc/imageGenAsync、aigc/taskQuery。若当前工具提供proxy_call，其参数通常为toolName和arguments（不再套一层body/data）；这只是原包参考，真实schema不同就停止核对，不用HTTP回退。

提词参数参考prompt/imageUrls/model/thinkingLevel；生图参考prompt/imageUrls/provider/aspectRatio/resolution/outputNum=1/quality。模型使用用户明确同意且当前支持的值；本地助手只接受已审阅子集LF_GEM_1/2以及BANANA/BANANA_2/BANANA_PRO/GPT_2_IMAGE/AIDRAW_EDIT/WAN2_7/SEEDREAM5。旧GEM_3_1_PRO、LF_BN_3不自动转换。BANANA仅1K、SEEDREAM5仅2K、LF_GEM_2不接受minimal是原包已审阅约束，当前资格/官方说明优先；本包未在线证明这些模型可调用。比例只包含1:1、16:9、9:16；用户要其他参数先核实，不无声替换。quality参数按当前schema确认，不承诺其他模型实际支持质量档位。

每个创建只提交一次。返回taskId表示已创建，不表示生成完成。先核对MCP isError、代理/业务错误，再读取业务字段。PROCESSING没有生成结果；SUCCESS仍须核对taskId及content或resultList[].url；FAILED停止。任务返回缺失/状态未知/超时记未知，不用重建来“恢复”。每轮最多一次单任务查询，待用户明确继续后查询原taskId；没有服务端取消能力就如实说明，不把停止查询说成服务任务已取消或不会计费。

提词成功content保持真实换行作为生图prompt，不用stdout路径代替内容。单图成功返回image结果链接；URL不是本地文件，也不保证长期有效。只对实际结果做视觉检查，不用合成示例或请求草稿替代结果。现有Native工具历史保留调用/参数/结果，工作目录记录只是交付辅助，不作为批准、幂等或账户身份依据。

本地素材上传需要额外的受控文件外传实现，本版未提供。原包预签名PUT、public-read和反馈接口均不纳入；不索取签名URL或凭据，不自动调用上传/下载，不恢复WorkBuddy专属wrapper。
