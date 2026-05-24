# DevFlow

AI 开发规范流程插件 — 结构化 AI 辅助开发工作流。

## 安装

/plugin install devflow@eleven-marketplace

## 命令

| 命令 | 用途 |
|------|------|
| /devflow:discover | 项目探索 — 无需求时扫描优化机会 |
| /devflow:clarify | 需求澄清 — 模糊需求展开对齐 |
| /devflow:breakdown | 需求拆解 — 产出编号需求清单 |
| /devflow:blueprint | 方案蓝图 — 业务流程图+规格+测试用例 |
| /devflow:implement | 编码实现 — 任务拆解+架构图+Sub-agent |
| /devflow:verify | 测试验证 — 逐项核对，智能回退 |

## 工作流

discover → clarify → breakdown → blueprint → implement → verify

任意阶段可直接跳入。每阶段完成时自动询问下一步。
