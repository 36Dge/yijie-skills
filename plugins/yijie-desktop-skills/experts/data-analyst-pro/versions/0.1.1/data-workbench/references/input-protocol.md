# 私有输入协议 v1
`python3 <本包>/scripts/analyze.py --input <工作区>/input.json --output <工作区>/新目录`
输入为 UTF-8 JSON。schema_version=1；title、question、source_label必填非空。source是相对input.json或绝对用户授权路径；只读取该文件，不扫描工作区。输出目录必须不存在。单源≤16MiB，表≤50000物理行/200列，JSON≤49999对象；XLSX≤512成员/32MiB展开，不解压执行，不算公式、不联网。
columns为非空字典数组，每项name（精确列名）、type（identifier/category/number/date）、unit（或“不适用”）、missing（明确字符串/null数组）。至少一列number。空串、NA、null只有被声明才算missing，否则算invalid；不隐式trim、类型推断或填零。number是有限普通十进制，禁止货币符号/千分位/百分号猜测，绝对值≤1e100且非零指数≥−100。需要单位换算先保留源、给出显式新数据/方法并获口径确认。
日期列format只能%Y-%m-%d，日粒度；XLSX值型日期只有零时分可转日，含时间不截断。百分比样式XLSX值不猜fraction/percent，需先明确口径转换为值型。公式和错误单元格记invalid，不使用缓存值。XLSX多表必须给sheet，CSV/JSON不能给sheet。
JSON输入是对象数组，必须json_columns明确所有源列；未声明额外字段拒绝，缺键映射null并按missing规则处理。空表仍需要列定义。CSV/XLSX首行为唯一非空标题，短行尾补空单元格，超宽行拒绝。未选字段在unused_columns列出，完整源快照保留。
duplicate_policy必填keep_all或deduplicate_exact：只按所有源单元格raw/kind完全一致判重；第二次及后续行记duplicate_of，后者才删除完全重复行。重复identifier单独记录行号，不作为删行依据。
可选group_by为category/identifier列；expected_groups是明确的空组名单，保留零样本、合计null，未知组自动保留。缺失/无效分组独立null组，不冒充真实类目。
可选trend={column,start,end}，ISO闭区间，最多3660天；日期缺失/无效/窗口外行逐一记excluded_rows，只在趋势排除，不影响整体统计，不补缺日。
可选histograms={数值列:[边界值,...]}，2–101个严格递增边界；左闭右开，最后一箱右闭。范围外与不可用数量分别报告。
输出analysis.json中的known_sum、mean、分位数、样本方差/标准差为十进制字符串/null；coverage=valid/rows。行账保留source_row/raw/state/retained/duplicate_of，cleaned.csv空白需结合行账区分missing和invalid。receipt记录源SHA、文件SHA、Python版本与浏览器NOT RUN。
