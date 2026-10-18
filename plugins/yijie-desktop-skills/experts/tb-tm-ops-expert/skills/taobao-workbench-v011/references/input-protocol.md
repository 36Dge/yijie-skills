# 本地输入与交付协议 v1

命令（用实际已安装资源路径，不猜旧路径）：
`python3 -B <本包>/scripts/diagnose.py --input <用户工作区>/manifest.json --out <用户工作区>/新的报告目录`

Python3.10+标准库；没有安装则说明依赖缺口，不静默装包。输出目录必须不存在且不在资源包内，输入保留。输出包含独立HTML（无CDN）、JSON、输入清单原字节与文件收据。失败后若已产生部分文件，保留并选择新目录。

清单schema_version=1；platform为本包profile支持的一个值；store为用户确认的店铺，currency=CNY；window.start/end是YYYY-MM-DD。时间窗不是默认30天。datasets为1–32个条目：
- id唯一，path相对清单或绝对文件路径，kind明确，platform/store必须一致；source写导出来源/时间与确认依据，basis写归因/退款/时间/订单口径。
- grain为day（每日店铺一行）或day_entity（每天每对象一行）。products/ads/traffic/orders/scores必须day_entity；id映射分别为商品/计划/渠道/订单/评分对象。不同维度或退款口径需不同basis；不要凭文件名猜。程序不会证明用户声明为真。
- header_row显式正整数，sheet为XLSX工作表名（多表必填，CSV不填）。UTF-8/BOM CSV、标准xlsx值表；最大16MiB、50000行、200列。XLS/XLSM/公式计算、透视表刷新不支持，先导出值。
- columns为canonical字段→{header: 原精确唯一列名, unit: 单位}。date、id、platform、store、system是文字字段；金额CNY，计数count，比率percent或fraction，评分percent/fraction/points/stars。逗号数字、货币符号不猜；先由用户确认后另存规范值。百分号文本1.2%需percent；数字1.2+percent=0.012，数字0.012+fraction=0.012。XLSX百分比格式底层0.012已经是fraction，不再除100。

支持kind及数值字段：
- overview：visitors,buyers,orders,gmv,refund_amount；products另有cart_users。
- ads：spend,ad_gmv,impressions,clicks,ad_orders；不把普通gmv映射为广告归因成交额。
- traffic：visitors,buyers,orders,gmv；orders：gmv,refund_amount。
- after_sales：refund_amount,refund_orders,refund_rate；service：consultations,replied_3min,reply_rate,shipments,on_time_shipments,sign_rate。
- scores：score；额外system列写明具体体系，score_scales按体系提供{min:"0",max:"5",source:"用户提供的后台量表说明"}等。量表数值与score声明单位一致。不能假设量表或权重当前有效。

必须date映射；缺日期/异平台或店铺行隔离，日期在窗口外正常排除。日期格式YYYY-MM-DD或Excel日期值；不猜地区日期格式。非总览明细要求稳定id，不用行号代替实体。相同kind/basis/grain/日期/对象的完全相同值只计一次，重复来源保留；冲突值全部排除并补充核对。不同basis分组不能加总。不同粒度不能混加。字段缺失null，真实0保留；缺行、冲突或缺值时完整total=null，只展示known_subtotal及覆盖。rates和score保留行快照，不加总或简单平均；评分取每体系/对象窗口内最后观测日期，不能冒充窗口末日实测。

可选gross_margin={value:"40",unit:"percent",mode:"confirmed"或"scenario",basis:与ads完全相同,source:"毛利口径及确认依据"}。同一报告有多广告basis时不要套同一毛利率，分开报告。无毛利率不默认值。有广告成交额与消耗后毛利贡献=ad_gmv×margin-spend；保本ROI=1/margin（margin0时未知），每广告元毛利亏损=max(0,spend-ad_gmv×margin)/spend（spend0时未知）。不等于净利润，不默认运费、签收、退款、税费或佣金。情景结果不能变成实际经营结论或自动关停建议。

读回report.json中的inventory、groups.rows.evidence、aggregates.coverage、derived/finance.reason和issues。receipt只证明产物完整性，不能证明业务口径或模型分析正确。review.md须逐条引用数据集/行/字段和来源；先说明缺口，再给可验证动作，不写无依据预计提升百分比。

0.1.1显示修订：率/评分总额为不适用，正常计算原因显示无计算缺口，空issues明确无已检测缺口；服务比例单独列原始观测日期和值，不合成均值。JSON null和计算公式保持；成本含项未提供时既不宣称已含，也不宣称未含。
