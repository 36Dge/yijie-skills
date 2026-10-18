# 小说文件协议 v1
读取examples/story.json作为字段说明；实例短文仅为合成结构样例，不代表合格正文。
首次：`python3 -B <本包>/scripts/story.py --input <story-input.json> --out <用户目录>/story-v1`
后续：`python3 -B <本包>/scripts/story.py --input <新输入.json> --previous <用户目录>/story-v1 --out <用户目录>/story-v2`
输出目录必须全新；任何失败保留旧文件。禁止编辑旧receipt以让检查通过。用户手工改过稿件时先说明与存档差异，把修改作为新输入，在未改变的原存档基线上创建新版本；没有未改存档则明确作为新项目导入，不能伪造旧hash。
根字段：schema_version=1, project_id, title, revision正整数, stage(brief/bible/draft/continuation/revision), brief六字段genre/length/protagonist/conflict/tone/pov, bible正文, bible_confirmed布尔, confirmation_source真实用户许可位置。第一版revision=1，有前版则+1且project_id一致。
characters每项{id,name,motivation,voice}。chapters每项{id,number,title,pov,goal,summary,text,fact_ids}；id为英文字母开头的字母数字下划线短横线≤64字符，编号从1连续；POV引用人物ID。正文实际写入text，不能用摘要代替。facts每项{id,text,character_id或null,established_chapter或null}；章节不能引用未来才确立的事实。
tracking必须恰好四键：plot-tracker、timeline、character-state、relationships，值均为列表。具体字段按样例。planned伏笔可未埋设；open需要埋设章；resolved必须有不早于埋设的回收章；due_chapter为计划章号或null。timeline每个事件sequence是唯一正整数，time_label由作者明确。每个人物必须有一条当前状态。
续写必须携带全部既有章节/事实/人物ID，增补内容；改稿允许更新内容但须change_reason。impact.json列出变更事实、修改章、影响章和仍需复核的章；还没修改的受影响旧章不会自动通过。别把更改摘要或fact_ids当正文已修复，要实际读正文。
产物：story.json完整快照、Brief/Bible/实际章节、四JSON台账、impact/review与各文件hash receipt。receipt只证明保存与结构校验，不是文学或事实验证；需读取实际文件完成质量复核。
