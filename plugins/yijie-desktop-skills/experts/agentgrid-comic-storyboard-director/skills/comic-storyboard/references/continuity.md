# 连续性、版本与交付

版本：0.1.0。

## 连续性台账

记录每镜的角色位置、服装/伤势、手持道具、光线/时间、进入与离开状态。跨镜差异要有可见动作或剧情解释。脚本只验证字段与引用，不判断“钥匙从左手跳到右手”等语义，必须人工核对并列未确定项。

## 局部修改

保留原文件，用新文件保存版本。指定镜头内容改变时 version 递增；未改镜头连同 version/status 保持不变。新增镜头用新 ID；删除镜头列原因。锁定镜头不得擅改；需要改动时先提交清楚的影响提案。已有 approved 不表示新版本自动 approved。

正常校验：`python3 <受管包根>/scripts/validate_storyboard.py --input <新分镜.json> --output <新验证.json>`。

对比此前版本：追加 `--baseline <此前分镜.json>`。结果列 changedShotIds、unchangedShotIds、addedShotIds、removedShotIds；会检查未变镜头版本和锁定镜头、已变镜头版本递增。目标范围仍需与用户要求人工比较，不能只凭脚本通过说全部要求满足。

## 本地文件

任务允许目录下建立 outputs/comic-storyboard/<run_id>/，按实际请求保存 manifest.json、01-story-brief.md、02-character-bible.md、03-episode-script.md、04-storyboard.json、05-storyboard.md、06-continuity-ledger.md、07-prompt-pack.md、08-validation.json。不是每次请求都强制写全套；用户只要一个分镜表时按范围交付。

只写任务内新产物，不写包目录，不自动覆盖已有文件。校验器使用 Python 3.10+ 标准库，无网络/子进程/依赖安装；输出使用 exclusive create，已有输出会拒绝覆盖，换新输出名称再由用户范围决定是否重新运行。找不到 Python/权限时给手工检查结果并标未自动校验，不修改系统运行时或环境。
