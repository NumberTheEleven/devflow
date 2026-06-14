# DevFlow v2.3

AI 开发规范流程 — 单一入口，按阶段推进，闭环管理。支持多 worktree 会话隔离与强制合并验证，防止多 feature 并行开发时的冲突与语义回归。新增 AI 视觉审查能力，可自动发现 UI 重叠、遮挡、溢出、截断等前端展示问题。

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
Step 0: 入口检测 → worktree / 会话检测
    ↓
Phase 1: 需求澄清 — 纯对话
    ↓ checkpoint
Phase 2: 需求拆解 → R-xxx 清单
    ↓ checkpoint
Phase 3: 方案蓝图 → 流程图 + 设计规格 + TC-xxx
    ↓ checkpoint
Phase 4: 编码实现 → T-xxx 任务 + 架构图 + 代码
    ↓ checkpoint
Phase 5: 测试验证 → L1烟雾 + L2交互 + L3手工
    ↓ checkpoint
Phase 6: 流程完成 → 合并验证 + 提交 + worktree 清理
```

## 特性

- **单一入口：** 只需 `/devflow`，无子命令
- **worktree 隔离：** 每个 DevFlow 会话在独立 git worktree 中运行，多 feature 并行开发互不干扰
- **强制合并验证：** 完成前自动检测目标分支新变更，验证涉及 feat 并强制解决冲突，防止语义回归
- **自动推进：** 阶段间自动流转，checkpoint 提供继续控制
- **兜底提交：** 流程完成前自动检测未提交文件，防止数据丢失
- **暂停恢复：** 随时中断，下次自动从断点继续
- **中文输出：** 模板、状态、提示全部中文化

## 会话文件

每个 feature 的 DevFlow 文件隔离在 `devflow/<feature>/` 目录下：

```
devflow/
├── user-auth/
│   ├── state.json
│   ├── requirements.md
│   ├── design.md
│   ├── tasks.md
│   ├── test-cases.md
│   └── verification-log.md
└── payment/
    └── ...
```

所有文件随 feature 分支提交到远端，便于冲突验证时读取历史 feat 的测试用例。

## Checkpoint 选项

每阶段结束时：

| 输入 | 行为 |
|------|------|
| 确认 / Yes / Y | 进入下一阶段 |
| 其他回复 | 视为需要修改，修正后重新展示完整结果 |
| 不回复 | 自然暂停，下次自动恢复 |

## 版本变更

### v2.3
- 恢复 git worktree 会话隔离机制，支持同一用户同时推进多个 DevFlow
- 新增 `devflow/<feature>/` 文件结构，按 feature 隔离状态与文档
- 新增 Phase 6 强制合并验证：检测目标分支新 merge commit、验证涉及 feat、强制解决冲突
- 新增语义冲突捕获：时间窗口内所有涉及 feat 的测试用例重跑
- 新增会话完成后自动清理 worktree
- 移除 `/devflow list` 和 `/devflow cleanup` 管理命令，保持单一入口
- 自动识别目标分支 `master` 或 `main`

### v2.2
- 新增 AI 视觉审查机制：对涉及前端/视觉/布局的 TC 自动启用 Playwright 截图 + AI 视觉分析
- 新增 L1 视觉烟雾扫描：页面加载后截图检查重叠、遮挡、溢出、截断、错位等
- 新增 L2 交互截图分析：关键动作前后截图对比，捕获交互引发的视觉异常
- 新增程序化布局断言：可见元素重叠、元素超出 viewport、内容被容器截断
- 更新 TC 路由规则：视觉/前端类关键词优先进入 L1/L2，不再默认落入 L3
- verification-log 模板新增“视觉问题清单”章节
- test-cases 模板新增视觉相关 TC 示例

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
