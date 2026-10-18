# 来源、修订和能力边界
用户本机原包linkfox-expert-aigc-videogen-viral-replicate 2.2.0共22文件，头像留原UI映射；4嵌套技能变成一个受管入口。本版0.1.0不是原包行为等价发布。

原编排默认GEM名称与MCP子技能LF_GEM冲突；当前公开HTTP仓库也与MCP安装包不同。只按实际schema确认，不自动映射。源SEED_FAST默认isPro=true与底层不支持冲突，改为显式拒绝，不静默改模型/画幅。原“保留全部原文”与压缩时长/2000字符冲突，改为有依据的替换草稿并人工核对，超过限制不截断。

原--query-task wrapper不存在，改为真实Native历史taskId与阶段恢复；不用工作目录JSON声称审批/服务状态。原本地MP4/临时URL规则互相冲突，统一为实际公开结果链接，未下载不报本地文件，未看视频不报质量通过。原任意媒体下载/ffmpeg抽帧脚本、公开PUT脚本、自动反馈排除。帧图由用户准备并授权提供，本版不实现下载、抽帧或上传；帧图不可推断口播。没有运营评分、剪辑拼接或BGM混音功能。

2026-10-17公开资料： https://github.com/linkfox-ai/linkfox-skills/tree/ea5581c8c727f259a4fa5ea3df00e7cec77bf5ce ； https://wiki.linkfox.com/features/skills 。仅用于协议对照，不运行其中脚本、不采纳HTTP密钥/轮询方案，不证明账号可用。用户无账号要求跳过真实验证；全部生成质量和线上参数仍待验证，仅本机使用、不作第三方再分发许可结论。
