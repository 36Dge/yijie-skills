# 用户报表的本地核对
仅使用用户主动提供的资料；不读取WorkBuddy会话、凭据或其他店铺私有文件。实际读入CSV/XLSX/JSON；无法解析时请求可读取格式，不声称已读。先展示原列到指标的映射，保留文件名、来源、期间、币种、时区与口径；未知指标用null，真实零用0，不替用户估数。

scripts/analyze_shop_report.py使用Python3.10+标准库，只读规范化JSON。输入形状见examples/report-input.json：shop_id/source、current，以及可选previous；每段含start/end/timezone/currency/basis/data_available_date、refund_basis（same_order_cohort/refund_event_date/unknown；缺省unknown）和metrics（gmv/orders/paying_buyers/visitors/refund_orders），计数为非负整数，GMV为最多6位小数，缺失为null。每个文件只分析同一店铺；多店分别核对，不自动把币种/口径合并。

执行：python3 -B <本包路径>/scripts/analyze_shop_report.py --input report-input.json --output-dir shop-report-v1
输出目录必须是当前任务工作目录下尚不存在的新目录。输出data.json完整留存输入，calculation.json给各指标/推导指标/缺失说明/可比性，包含原输入SHA256。不覆盖旧文件、无联网/安装/遥测。

GMV/订单为订单客单价，支付买家/访客为支付买家转化率；缺分母或零分母显示不可计算。仅refund_basis=same_order_cohort时计算退款订单率；按退款发生日或未知归属时不除以当前订单。脚本不证明业务口径真实性。两段期间长度、币种、时区或basis不一致、日期重叠时不产生增长比较；旧值0时只显示绝对差、不生成无穷增长率。输入end晚于data_available_date时停止并要求完整或明确收窄期间。

检查退出码及实际文件，独立核对关键数字、缺失、原输入未改；再用shop-diagnosis组织业务解读。不能把计算成功当店铺授权成功或因果验证。原始文件和规范化映射需在结果中说明；脚本未运行就写未自动核对。
