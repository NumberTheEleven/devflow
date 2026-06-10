# DevFlow v2.1

AI 开发规范流程 — 单一入口，按阶段推进，闭环管理。

## 安装

/plugin install devflow@eleven-marketplace

## 用法

```
/devflow 我想加一个用户认证模块
```

一个命令，贯穿始终。无需记忆子命令。

## 工作流

```
/devflow 模糊需求
    ↓
Phase 1: 需求澄清 — 纯对话
    ↓
Phase 2: 需求拆解 → R-xxx 清单
    ↓ checkpoint
Phase 3: 方案蓝图 → 流程图 + 设计规格 + TC-xxx
    ↓ checkpoint
Phase 4: 编码实现 → T-xxx 任务 + 架构图 + 代码
    ↓ checkpoint
Phase 5: 测试验证 → 逐项核对 + 智能回退
    ↓
全部通过 → 流程完成
```

## 特性

- **单一入口：** 只需 `/devflow`，无子命令
- **自动推进：** 阶段间自动流转，checkpoint 提供继续/跳转控制
- **兜底提交：** 流程完成前自动检测未提交文件，防止数据丢失
- **暂停恢复：** 随时中断，下次自动从断点继续
- **中文输出：** 模板、状态、提示全部中文化

## 管理命令

| 输入 | 用途 |
|------|------|
| `/devflow list` | 列出所有 DevFlow 会话及当前阶段 |
| `/devflow cleanup` | 手动清理指定会话的跟踪文件（含确认） |

## Checkpoint 选项

每阶段结束时：

| 输入 | 行为 |
|------|------|
| Y / 回车 / 继续 | 进入下一阶段 |
| 跳转到 [阶段名] | 跳过中间阶段 |
| 不回复 | 自然暂停，下次自动恢复 |

## 版本变更

### v2.1
- 移除 git worktree 隔离机制，简化流程
- 新增预完成提交兜底保护
- `/devflow list` 和 `/devflow cleanup` 改为基于会话管理

### v2.0
- 合并 6 个子命令为单一 `/devflow` 入口
- 新增 git worktree 自动隔离
- 新增阶段自动推进 + checkpoint
- 新增流程完成自动清理
- 模板与输出全面中文化

### v1.0
- 初始版本，6 个独立子命令
- discover / clarify / breakdown / blueprint / implement / verify
