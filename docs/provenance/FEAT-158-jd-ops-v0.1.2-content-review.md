# FEAT-158 内容 0.1.2 修正审阅

2026-10-11。本地未发布候选，专家 `jd-ops-expert@0.1.2`，bundle `0.4.2`。真实模型 Eval：**NOT RUN for 0.1.2**。本地结构和打包检查不能证明模型行为已通过。

## 实际发现与修订

0.1.1 run7 固定 Kimi 内容评测未全部通过：6 项首次完整通过，5 项首次 partial，1 项仅覆盖取消变体；3 项经明确追问补齐。严重错误 0、支持场景引用 23/23 可定位仍不足以达到“全部所选用例通过”。MiniMax 重开后的资料读取属于独立生命周期证据，不混入固定 Kimi 内容评分。旧答案、工具摘要与失败记录保持。

本次修订使用通用判断规则，不嵌入针对某条评测的标准答案：

| 实际问题 | 内容修正 |
|---|---|
| 合并问题只完成商品检查，遗漏新店基础设置 | ROLE 与索引要求逐项交付；M01 明确店铺级地址、配送、客服与支付，M03 明确商品级字段，不相互替代 |
| 正确算出差异，但无中间步骤便断言唯一错误原因 | M05 区分可证实算术差异与待验证成因假设 |
| 没有点击次数，仍把访客/曝光命名为点击率 | M13 要求名称、分子分母与单位对应，缺关键量不套指标名或定位缺失层 |
| 只检查当前目录便断言全历史不存在 | ROLE 与来源说明限定观察范围，未知历史存在性保持未知，不扩大搜索证明不存在 |
| 把申请库存与实盘不相等一概判虚高 | M03 对申请量与已确认可交付量的小于、等于、大于分别判断，未知量不推定，数值关系不授予写权限 |
| 标题计数与列项不一致 | 输出检查明确核对列项数量与编号 |

示例、检查表、12 条稳定 Eval ID 的 expected 与 rubric 同步澄清；输入保持原有案例，除当前可用内容版本改为 0.1.2，不修改合成问题以回避旧失败。阈值仍为严重错误 0、引用可定位率 100%、全部所选用例通过。首次结果、明确追问后的纠正、实际不可用状态与取消变体分别记载，不降低判定标准。

14 模块、42 场景和原稿行号保持；所有内容版本同步为 0.1.2。没有改用户源文件、引入新政策结论、扩大工具或网络权限。提示词修正只提供更清楚的行为指导，不保证模型无误，仍须独立真实评测。

## 影响、兼容与使用顺序

`contract-impact = semantic`：专家行为内容和版本改变；公共 wire、归档布局、权限和运行时投影不变。权威源为本仓专家目录与 `experts/bundle-source.json`，消费方为 Agent Host 和 Desktop。Contracts schema 修改为 N/A；继续使用当前 canonical 生成的 v3 格式与专家摘要算法。原 `contracts/lock.json` 及 38 个普通 Skill 源不改。

仅生成 `local-development` / `release=false` 候选。使用顺序为内容审校及正常检查 → canonical 新目录打包 → 主任务确认 consumer 摘要与隔离安装资格 → 真实固定模型评测。consumer 不得自动将旧历史引用换成 0.1.2；旧版继续可用或明确不可用，不覆盖有引用的安装。回退也应通过既有版本和引用保护路径，不能改写数据库、回执或历史。

## 旧版保留与新产物

0.1.1 源文件修改前已保存到 `dist/feat158-v011-run7-source/`，37 个源及审阅文件逐字复制；其完整 41 个候选文件仍位于 `dist/skills-experts-candidate-v011/`，不重新生成。摘要清单为 `dist/feat158-v011-run7-preservation.json`。旧 manifest 为 `31e7f42193263356c1e4939600ebd95961e6eb682c96f53429b47417dc3d1b6d`；旧授权、source audit 与 0.1.0 保留文件不复写。本次不触碰任何 installed/history/App 数据目录。

新输出目录为 `dist/skills-experts-candidate-v012/`，使用同一确定性打包器：

```bash
node ../yijie-contracts/scripts/sync-experts.mjs --consumer=skills --check
node scripts/package-desktop-skills.mjs --source plugins/yijie-desktop-skills/experts/bundle-source.json --output dist/skills-experts-candidate-v012
```

检查结果和精确产物摘要写入 `dist/feat158-v012-checks.json`。本次安全范围仅包括正常源码/格式/确定性归档检查；不执行模型、UI、服务、安装、官方政策联网核验或禁止的故障注入。真实模型、consumer pin 激活、完整产品验收与公开发布不由此文宣称完成。

## 本地检查结果

`make lint`、`make test` 的 11 项正常测试及 16 条合成数据格式检查、Contracts Skills canonical `--check`、上述新目录打包、`git diff --check` 均通过。38 个普通 Skill 的元信息与归档逐字节不变；0.1.1 的 41 个产物和 37 个源快照文件逐 SHA-256 验证保留。新专家 ZIP 的 26 文件与源一致，14 模块/42 场景索引除内容版本外不变；原 12 条评测输入只变更可用内容版本，原阈值保持。

skill-creator 附加的 `quick_validate.py` 分别在系统与已有 bundled Python 下尝试，均因缺少 PyYAML 未执行成功，未安装新依赖，不记 PASS；已读脚本并核对本 Skill 未改变的两项 frontmatter 字段、命名、长度与占位规则。仓库规定的 lint/test 不依赖该 Python 库，均已实际通过。

| 0.1.2 候选 | SHA-256 |
|---|---|
| bundle-manifest.json | `a176bfba892afbc4de8622ebde955a72aef240ab51a9256d7bfb6c5ec40c0936` |
| authority.json | `9c6f384b6f95eb6579c9f26177e229d8646986db44a10220aa119a6f0dc015b8` |
| 专家 ZIP | `8fea62005795175ef9b649d0320ab9049ba2165b734ebd887a911536dc4b9cc7` |
| ROLE.md（2928 bytes） | `fcf23ad407cfe0df4f43c6167855d30edcdee9d8194b37d30df2c59136fa8838` |
| knowledge manifest canonical digest | `424896b2c8366fa2f658b66c4b8eeb8f01e69399b34c01824cc5c558ac3db8c4` |

来源 base revision 为 `488714a8d96f40806a257aae097683815b1dd458` 的 working-tree，tree SHA-256 为 `357ca50ee8c9b602eccb0393a56c103491d1474d0fd56012cddd88378d19c4ab`；source definition SHA-256 为 `d9aa94e28e14dc6f86ace2f72b60c1884eb2f2604ec5b2ac6f3d080edabaa166`。仍为 `release=false` 的本地候选，不伪称已提交或发布来源。
