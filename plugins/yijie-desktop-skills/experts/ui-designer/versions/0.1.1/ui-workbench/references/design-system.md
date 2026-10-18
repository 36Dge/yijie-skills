# 易界设计系统适配
现有易界工程的权威为活跃src/styles/variables.css、src/components/ui、图标registry和docs/design/docs/design。技术栈Vue3/Vite/Naive UI/Tauri；不能默认React、Tailwind或第二UI库。页面组合UI，domain放纯规则，api负责I/O，不把后端或数据库搬到前端。已有Yj组件实际存在才使用；exports目录是参考，不直接导入。
独立HTML原型使用普通语义元素，没有Vue环境不假装调用Yj组件。按字节复制templates/yijie-tokens.css到tokens.css（本次采自活跃工程），沿系统字体、body14/22、标题24/32、semibold600、白/石墨背景与青柠主操作、6/8/12/16圆角、4/8/12/16/24/32间距。所有视觉值用变量；页面布局宽度可定义语义局部token。document.documentElement.dataset.theme控制亮暗；不得只改body颜色造成控件不可读。
结构先确定信息主次、适当留白与对齐，避免无意义装饰/渐变/大量动画。图标用工程registry；独立原型没有registry可用清晰文字按钮，不从外站抄logo。图表用现有ECharts及主题，未提供库不添加CDN。用户未提供图片不强制生成。
完整状态为loading、empty、error（retry）、permission-denied、ready；独立原型允许明确的“演示状态”控件驱动，不让假数据看起来像联网结果。真实业务接入需要对应已有架构与授权，本专家资源不会自动提供。
