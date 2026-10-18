# 来源与适配决定
原report-viz-expert@1.0.0，Tand。Agent、chartjs-report、antv-infographic的方法转为本包ROLE和参考；保留全部数据、图表选择、真实数值与验证要求。原CDN模板与AntV脚本不打包：无锁定依赖，要求临时安装和内部SSR路径。改为本工程已用的ECharts6.1.0离线分发库，正常Node SSR导SVG，独立HTML内联同库，不引入第二套图表机制。
ECharts UMD原字节来自当前Desktop精确依赖；Apache-2.0 LICENSE/NOTICE随包与HTML保留。Desktop补丁只影响lib/core/Scheduler.js，未改变所取UMD分发文件；此处不宣称把该补丁应用到UMD。本离线文件不在冻结Object.prototype的应用WebView内执行。图表色取易界light语义token，系统字体回退；不加载远端字体。
原包未声明公开分发许可，本次为用户授权本机适配。未提供PNG栅格化器/在线BI/自动外部取数。第三方图标不进入可执行包；前端沿用本地ID映射。逐文件来源、库摘要与取舍见仓库provenance审计。
