# 确定性内容检查

仓库测试 `tests/jd-expert-content.test.mjs` 检查14模块/42场景索引、真实文件/标题对应、原稿行范围、包内相对引用、最小资源边界、合成Eval覆盖及未核政策状态。测试不读取用户源文件、不调用模型/外部服务、不执行reference内容。

运行：`node --test tests/jd-expert-content.test.mjs`（仓库根目录）；`make test`包含该检查。它证明内容可定位与结构一致，不证明模型质量、当前京东政策、Runtime可读性或正式分发许可。
