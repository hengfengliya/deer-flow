# 2026-03-29

## ✨ 本地启动准备
> 18:50 | 为 DeerFlow 补齐本地运行前置环境，并生成首份可启动配置

- **变更文件**:
  - `A` CHANGE.md
  - `M` config.yaml
- **细节**:
  - 生成项目本地 `config.yaml`，避免启动脚本因缺少配置文件直接失败
  - 补充基于 Codex CLI 的默认模型配置，优先复用本机已存在的 CLI 认证能力

## ✨ 项目经理智能体与技能安装
> 19:05 | 为 DeerFlow 增加项目经理专用 agent，并显式启用项目管理相关技能组合

- **变更文件**:
  - `A` backend/.deer-flow/agents/project-manager/config.yaml
  - `A` backend/.deer-flow/agents/project-manager/SOUL.md
  - `A` skills/custom/project-management-workflow/SKILL.md
  - `A` extensions_config.json
  - `M` CHANGE.md
- **细节**:
  - 新增 `project-manager` 自定义 agent，聚焦需求澄清、排期拆解、风险管理和项目推进
  - 新增 `project-management-workflow` 自定义技能，覆盖项目计划、周报、会议纪要与复盘等核心场景
  - 显式启用适合项目管理的公共技能，包括调研、报告、数据分析、GitHub 研究和 PPT 输出能力
