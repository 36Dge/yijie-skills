# AGENTS.md

## 仓库职责

`yijie-skills` 负责跨境电商领域 Skills、Plugins、Prompt Packs、Evals、Rubrics 和 Marketplace 元信息。

## 禁止事项

- 不保存真实商家数据；
- 不保存平台 token；
- 不实现外部平台 API client；
- 不访问数据库；
- 不维护 Codex Runtime 源码；
- 不绕过审批执行高风险写操作。

## 开发命令

```bash
pnpm lint
pnpm test
pnpm package
```
