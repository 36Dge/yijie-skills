# FEAT-158 Git 交付与公开范围

2026-10-13，用户明确要求审计后提交并推送相关仓库。确认远端为公开仓库后，用户再次明确回复：“包含知识正文与脱敏评测记录，允许公开推送”。本记录授权本次源码、京东知识正文、脱敏工程与评测记录的公开 Git 上传；不将 Owner 的上传授权解释为独立的第三方许可证核验、官方政策背书或桌面正式发行批准。

Contracts `experts/1@0.1.0` 来源完整提交：`e35ae9a0711014e4774a1347413e9a343ce7ab2c`。同源生成锁 `compatibility/experts/source.lock.json` SHA-256：`a5056217e4d54310d451ba53c64504ef010e2c616108cf75b606b0de0e4d9033`。`contracts/experts.candidate.json` 保留原始 pre-change baseline 和逐文件摘要；Git 提交后的真实消费者来源由本记录及下游交付记录定位，不伪造自引用 SHA。

内容保持 `jd-ops-expert@0.1.3` / bundle `0.4.3`，不修改已验收归档、角色、知识与安装身份。提交后使用原 canonical 打包器从干净源码重建，manifest 来源变为实际 Git commit，下游同步审核后的目录摘要。`release=false`、`local-development`、既有权限边界及旧安装引用保护保持。

AC-007 内容质量验收已由用户从 FEAT-158 移除；历史 FAIL/未执行项原样保留，不转为 PASS。外观验收跳过。本次 Git 收口不追加真实模型调用。凭据、原始个人会话、数据库、受保护密钥和本机缓存不提交。
