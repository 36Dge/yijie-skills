# 工具与阶段
LinkFox沿易界现有OAuth、工具发现/完整schema冻结、会话选择与逐次审批；同一固定serviceId=linkfox，不注册第二个视频连接器。实际提供的工具名与参数才可调用，proxy_call及下列方法只作原资料对照：aigc/textGenAsync、aigc/textTaskQuery、aigc/multiImageVideoGenAsync、aigc/taskQuery。业务对象直接为arguments，不套body/data；若当前schema不同先核实，不能猜未声明字段。

原MCP textgen参考为LF_GEM_1/2，原编排和当前公开HTTP文档为GEM_3_FLASH/GEM_3_1_PRO。两种来源并非在线MCP资格证据。本地帮助器允许记录这四个明确值；不做别名映射/默认回退/探测性创建，调用前按当前工具确认。不支持的模型组合直接说明。高质量两值不使用minimal。业务创建/查询均可能计费，额度或401/402/403拒绝就停止。

本版采用明确的窄参数子集：SEED/SEED_FAST，1—9张同商品图，5/10/15秒，16:9/9:16；SEED 480p/720p/1080p，FAST 480p/720p且无Pro。voice必须显式布尔；SEED的isPro显式布尔，FAST为false且不发送isPro；promptOptimizer固定false。新公开模型更广不代表本专家已支持；不默默切到2.5/mini或其它模型。

四个异步任务：reference→product→prompt→video，每项分别创建一次并记录其原taskId/操作ID。每轮最多一次查询，PROCESSING等待用户继续，失败/unknown不重建。查询原任务时不重复发素材、分析、替换或生成；未提供原制作单摘要可从原工作产物/历史找回，缺失不猜。模型返回JSON先按MCP isError，再代理/业务码，最后taskId与状态；text JSON只解一次，冲突来源/空内容不视成功。

创建taskId仅表示created；SUCCESS文本方可进入下一草稿。SUCCESS视频还需同一taskId且实际resultList中单条type=video和真实URL。结果链接不保证长期有效；图片结果不能充当视频。未下载时local_file=null，未实际播放核对时visual_audio_quality=not_verified。没有服务端取消能力时停止查询不等于任务取消或费用退回。
