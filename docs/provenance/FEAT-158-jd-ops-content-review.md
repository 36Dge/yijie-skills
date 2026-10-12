# FEAT-158 京东专家内容审校记录

日期：2026-10-11。审阅方式：Codex 静态内容审阅与离线结构检查；Owner 人工最终审阅、当前政策核验、真实模型 Eval、Desktop/Host 运行验收均未以本报告宣称完成。

## 范围和来源

候选源根：`plugins/yijie-desktop-skills/experts/jd-ops-expert/skills/jd-ops-kb/`。产品名“资深电商运营操盘手”，副标题“京东专向”，内容版本0.1.0。

源资料为用户提供的专家配置和《jd_kb_京东运营知识库完整版.md》。知识原稿224337 bytes、2291实体行、SHA-256 `ce352f4f8ce2e21b5526ac5471104aff52802d5c36b099c0f6b425718f026d4e`，与只读观察到的WorkBuddy同名包内文件一致。文件有2290个LF且末尾无换行，表格179在2291行有完整结论。配置文件SHA-256 `8626d82c958bb2a0d4dd2af9e1179c4e32816dfc24c3869abba9af535c476a59`。

原文件未修改，也未复制进可分发资源；没有复制第三方头像、脚本、凭据或运行时设置。候选正文由易界重新编写，将通用运营方法转为“输入→检查步骤→输出→待核实项”，每个场景保留原稿line mapping。规范场景ID为本包新建，不冒称原稿已提供。

初始内容阶段只新增尚未进入现有发布包的内容源和离线检查，contract-impact=none；当时无公共输出schema、bundle格式、source pin或Runtime调用变化。后续FEAT-158 v3打包/消费属于主需求的跨仓契约影响，不以初始阶段分类替代。旧FEAT-129的38项分发授权不自动扩大到新增专家；本轮仅有本地实施授权，公开再分发保持未确认。

## 可用内容范围

14模块各3场景，共42个场景；包含基础设置、店型/资料准备、字段与标题核对、素材质量/测试、成本与优惠核算、冷启动测试、活动承接、广告口径/关键词诊断、服务质量/复购、客服方案、履约协商、商品信息核对、复盘漏斗和达人合作。

ROLE与SKILL同一归档根，ROLE保持短文本。reference均为本地普通Markdown/JSON，无脚本/外部URL。index先选模块再读片段；角色不挂60轮上限、不请求外部、不启用连接器、不启动独立进程。原则性数据缺口不造成42个场景都只说“待核实”：每个场景有明确的输入、正常检查步骤、输出表/清单和完成证据。

## 审校处置

| 原稿问题与位置 | 处置 |
|---|---|
| 无http(s)官方来源URL，1728–1754的high/medium自标 | 来源状态统一为未完成官方政策核验；不生成verified-policy |
| 33、171–173、207–211、582–583、609–611矩阵缺失；1725–1726残句 | M01-02/M02-01/M04-01/M14-04明确incomplete；提供核查问题与准备表，不恢复假数据 |
| 正文与1756–2291提示卡脱离，模块/场景编号不统一 | 建立42条scene-index与原稿range映射，保持最后表格真实内容，不按末尾模块自动归属全部提示 |
| 867、1090、1173、2135数字连接符损坏 | 不猜测恢复参数；换为用户设定、当前界面与可验证变量 |
| 788算式写95 | M05-01保留算术检查80，并说明不证明商业结算公式适用 |
| 947预算天数、1401比例边界 | 不采用错误预算示例；M11-04指出2/5恰为40%，不据此解读具体处罚 |
| 1124–1139/1176/1769/1805/2126同投冲突 | M08-05标conflicted，先确认SKU/产品线/实际条款，不确定双开或关闭 |
| 516/638/760/1546/1952/1985 AI素材范围混用 | M04-06标conflicted，按店型、素材用途和真实内容核实；不一刀切或承诺加标即合规 |
| 1354/1746全球购与POP差异；2225/2228期限冲突 | M10-04/M12-05保留范围差异，不给统一申诉天数 |
| 1535/1675星级边界、219/1838入驻通道差异 | M12-10/M02-03保留待核，避免猜测当前规则 |
| 1281/2111跨平台术语、2189骑手案例 | 不转写成京东商家操作；平台、角色和数据范围保持明确 |
| 95/911–916/1790交易评价操纵，382/1901虚构热销 | 不保留操作步骤；改为真实成交反馈、事实文案与正常售后 |
| 1018–1021绕活动等待，474–475/1931物流伪装，1212/1305防关联 | 不进入可执行参考内容，只保留正常官方流程、真实物流与如实说明 |
| 1240退货原因误导，1528/1586礼品单动销，447全部子账号权限 | 排除；以真实原因、真实经营和原有最小权限替代 |
| 1333–1335无条件库存/优惠话术 | M10-02要求真实事实，不编造稀缺性、发货或优惠到期 |

各模块所有当前政策阈值、费用、日期、处罚和强制资格均为verify_required。未进行全网政策检索，不能把结构检查当作业务规则正确性验证。精确源码文件与字节摘要见 `source-audits/FEAT-158-jd-ops-content-audit.json`。

## 离线验证

已先逐项检查测试源码：现有测试只生成正常确定性归档与校验元数据，在自身临时目录正常清理；新检查只读取普通文本与合成输入，不包含攻击/故障注入或权限破坏。vendor Python仅作AST解析，不执行其业务脚本。

- `make lint`：PASS，3个SKILL章节检查通过，旧38项/258文件来源与Contracts0.5.1 v2检查通过。
- `make test`：PASS，9项Node测试通过；其中新增3项检查14模块42场景、相对资源/短角色和良性Eval覆盖。
- 数据集格式：PASS，3套共16条合成数据；新增专家12条。
- 真实模型Eval：NOT RUN；当前官方政策核验：NOT RUN；本报告不证明Runtime可读、专家切换或D4。
- 攻击注入、危险fixture、强杀、替换运行时、权限故障：未执行，用户明确禁止；不得声明这些专项已覆盖。

上述内容阶段未修改旧bundle-source、契约pin或包版本；没有commit/push/上传/发布。不将本内容阶段结果冒充发布完成。

## 第二阶段：v3 本地候选打包

本轮后续实施授权已增加v3候选打包。FEAT-158整体contract-impact=breaking，按主需求的源契约与consumer兼容方案处理；本文初始内容阶段none不覆盖新边界。权威源是Contracts `jsonschema/skills/skill-bundle-manifest-v3.schema.json`，通过其 `scripts/sync-experts.mjs --consumer=skills` 同步；旧 `contracts/lock.json`、v1/v2快照、原38项bundle-source和分发声明保持原字节。

现有 `scripts/package-desktop-skills.mjs` 增加显式source选项与v3派生，不另建ZIP格式、安装器或摘要算法。新 `experts/bundle-source.json` 引用原v2源并只追加专家条目；默认v2本地/桌面分发命令行为继续保持，专家候选只允许local-development。

实际产物：`dist/skills-experts-candidate/`，含0.4.0候选manifest、39个归档（38旧+1专家）及 `authority.json`。专家26个普通文本资源共89320 bytes；ROLE为1730 bytes；manifest声明16个知识资源（索引、来源说明、14模块），包内还有私有场景JSON与良性评测材料。资源字节、归档、审校文件与本地授权均进入摘要核对；知识manifest摘要使用Contracts生成的canonical JavaScript。

authority用于主Agent/Host/Desktop显式开发同步固定来源，不是让renderer提供任意manifest的自证。来源诚实标为working-tree，base revision为 `488714a8d96f40806a257aae097683815b1dd458`，`release=false`。Contracts候选锁与authority随canonical源更新明确同步，不伪装成已发布commit或不可变tag；最终摘要以同目录authority为准。

检查结果：

- `make lint`：PASS，旧38项与0.5.1 pin检查继续通过。
- `make test`：PASS，11项Node测试、16条合成数据结构检查通过；新增正常v3包测试确认38个旧归档逐字一致、39项候选可重复、角色/知识文件sha和bytes一致、authority与manifest对应。
- 不支持的desktop-release请求在产生输出前正常拒绝；未造恶意包或篡改文件测试。
- Contracts同步检查曾因同轮并行源更新出现candidate漂移，采用canonical同步解决，不手改生成文件；每次最终源更新后重建候选并执行focused包校验，交接以最后一次结果为准。
- `git diff --check`：PASS。真实模型、当前政策核验、Host/Desktop E2E不由这些结果证明。

所有新增测试均已先检查源码，未包含用户禁止的攻击、强杀、权限破坏或运行时替换。公开分发仍未授权；没有commit、push、发布或外部业务请求。

阶段 1 候选交接历史（保留当时证据，当前消费请使用下方阶段 2 表）：

| 产物 | SHA-256 |
|---|---|
| Contracts source.lock | `6b5a8da6c749cad5a28e75ddf9432dbc50ddcdc984b595a31c5b24d2d7861d52` |
| Skills experts.candidate.json | `de93743e7cd092ec2392cdaea3d737f53bf58a7cdd01f3de7be3cc84656303f1` |
| authority.json | `acf0d2959e1b332d2050b3893eb4927af19b7adb2e73d5db492377df1763931d` |
| bundle-manifest.json | `156fa3da100f82985087637ea3e94138d1f6ff813fedc8a4275b0dcad591e355` |
| bundle source tree | `2fae182bcdbf41e2a6f7418fa1e64d94282a851c5cc0550feb213dac8ad4fef6` |
| 专家ZIP | `d56ce92e8b7559a5b5e04805c2b99c82dd770c3b70dc61169fd18f1700a04799` |
| ROLE.md | `7173636f07506ce525c15af7b6fc29b564536c3be41798ac614714a26b4c70f0` |
| canonical knowledge manifest | `a9a8b3fd47188e66e0d5489ccbdebd2e60c643f34fde92502eaa3a76958cb483` |

该次源同步后，`node --test tests/desktop-expert-bundle.test.mjs` 两项PASS，canonical `sync-experts.mjs --consumer=skills --check` PASS。这是上述阶段 1 字节的历史证据；阶段 2 源同步后，旧 candidate/authority 摘要不再作为当前交接依据。

## 阶段 2 接线后的当前来源核对

2026-10-11 对实际文件只读核对：Contracts 已增加资源 status/prepare/remove/read，合计 9 个既有 owned pipe 私有方法，Native 仍为 8 个安全命令；required `BindingView.managed` 明确表示已进入专家发送 family，即使 expert=null、revision=0 也不能回到旧 submit。以上是消费者契约和状态边界变化，不改变本包的角色、知识或评测正文。

通过 canonical 源同步及候选打包更新了 Contracts candidate 与 authority。bundle 版本仍为 `0.4.0`，专家为 `jd-ops-expert@0.1.0`，来源仍是 Skills base `488714a8d96f40806a257aae097683815b1dd458` 的 working-tree 候选；不是该 commit 已包含新内容，不是 tag，也不是可发布来源。`release=false` 与 `local-development` 保持。当前字节如下，后续源变化必须重新同步并核对：

| 当前产物 | SHA-256 |
|---|---|
| Contracts source.lock.json | `762fa86dedad71afef0c2a0e37d7945202ca961cdddb6e7c188aaa6c7d657259` |
| Skills contracts/experts.candidate.json | `0b0e102fca3c13f542cea88b2f19b288981139fc22f3042fe8c71e1437b87d95` |
| authority.json | `8cefd1e0fc0c80739018b37293e44550dd2b0c6a0fdb96f7ea08b28e7e356d3b` |
| bundle-manifest.json | `156fa3da100f82985087637ea3e94138d1f6ff813fedc8a4275b0dcad591e355` |
| bundle source tree | `2fae182bcdbf41e2a6f7418fa1e64d94282a851c5cc0550feb213dac8ad4fef6` |
| 专家 ZIP | `d56ce92e8b7559a5b5e04805c2b99c82dd770c3b70dc61169fd18f1700a04799` |
| ROLE.md | `7173636f07506ce525c15af7b6fc29b564536c3be41798ac614714a26b4c70f0` |
| canonical knowledge manifest | `a9a8b3fd47188e66e0d5489ccbdebd2e60c643f34fde92502eaa3a76958cb483` |
| 本地使用授权证据 | `36e27d998b37ae3dfff090387059b8ffee3591f4da910f1e1f82cc229f6b1454` |
| 内容 source audit JSON | `3701239c1ea1868eeea5bfcb607500d9da79fb9ba0ef4de42c1811c1dd70d675` |

授权依据仍为 [本轮本地使用授权记录](./FEAT-158-local-use-authorization.md)，机器可核对审校依据仍为 [source audit](./source-audits/FEAT-158-jd-ops-content-audit.json)。这两份已被 authority 固定的文件与包内正文在本次文档收口中未修改；本报告不是修改授权或审校摘要的替代途径。

本轮消费者已有实现：Host 沿用 managed Skills 的安装事务和 receipt，将专家排除于全局 Skill roots/enablement；组合完整普通 base、短 ROLE 与短索引，知识按需读本地 reference。Native 持久化资源原 intent/request/receipt，移除检查所有保留的绑定和提交引用，跨版本替换也检查保留历史；未知资源操作只查询原 ID。未新增独立专家进程、全量知识 prompt、另一套安装器或旧版本并存库。

验证边界：此前 Skills `make lint`、11 项正常包/结构测试、16 条合成 Eval 格式检查和两项专家包定向测试的证据保留如上。Host 当前 18 项 FEAT-158 正常测试通过，其中实际候选测试只将此包安装到临时目录，确认 ROLE 1730 bytes、索引 4420 bytes、全局投影为 0；Desktop canonical 资源 copy/check 已按本表 source/authority 通过。这些消费者检查不等于真实模型读取或业务正确性。固定 Runtime 对自建普通 reference 的 localhost synthetic 协议观察另见 Host 记录，不能推广为本专家实际安装目录与全部权限模式已通过。

主任务随后执行当前内容与包的正常定向检查：`node --test tests/desktop-expert-bundle.test.mjs tests/jd-expert-content.test.mjs` **5/5 PASS**；Contracts 三个消费者 canonical `--check` 及 Desktop assets `--check` PASS。文档任务本身仅核对来源，不另行重跑构建或模型 Eval。

真实 UI 与真实模型/Provider、本专家全部权限模式可读性、42 场景回答质量和当前政策核验仍 **NOT RUN**。无外部调用、commit、push、公开发布或再分发授权；不以结构或打包 PASS 冒充内容质量验收。
