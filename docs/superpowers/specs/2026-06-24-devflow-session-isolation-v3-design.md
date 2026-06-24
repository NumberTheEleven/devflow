# DevFlow v3.0 — Session Isolation Redesign

**Date:** 2026-06-24
**Status:** Draft
**Context:** 替换 v2.4 的全量 rsync 复制方案，用 Claude Code 原生 worktree 机制 + 社区最佳实践

---

## 问题回顾

| # | 问题 | 根因 |
|---|------|------|
| 1 | worktree 不能运行代码（v2.3） | `git worktree add` 只有 git-tracked 文件，缺 node_modules、.env |
| 2 | 全量复制慢 + 递归爆炸 500GB（v2.4） | rsync/robocopy 复制整个 repo，排除规则不可靠 |
| 3 | AI 忘记在 worktree 工作 | 手动 `cd` 不可靠，后续 turn 容易丢失上下文 |

---

## 生态调研结论

调研了 Claude Code 官方文档、superpowers (6.0.3)、MoAI、Agent Workspace Fabric、dmux、Bernstein、社区博客等 10+ 方案后，关键发现：

1. **没人用全量复制。** 所有成熟方案都是 `git worktree add`（秒级）+ 选择性补充运行时文件
2. **Claude Code 官方已内置完整基础设施：** `EnterWorktree`（CWD 自动切换）、`.worktreeinclude`（gitignored 文件自动复制）、`worktree.symlinkDirectories`（node_modules symlink）
3. **devflow v2.4 的 rsync 方案在整个生态里是独一份** — 方向走偏了

---

## 设计目标

1. **创建速度从分钟级降到秒级** — 用 `git worktree add`，不做 bulk copy
2. **彻底杜绝递归复制** — 没有 bulk copy 就不可能有递归
3. **CWD 切换可靠** — 用 `EnterWorktree` 工具，session CWD 自动切换
4. **运行时环境完整** — 选择性补充 gitignored 文件，保证可启动服务
5. **向后兼容** — Step 0 检测逻辑兼容 v2.4 旧会话

---

## 方案概述

```
Phase 1.4 初始化会话（新流程）:

1. 识别目标分支（main/master）
2. 检查命名冲突
3. 创建 feature branch
4. 创建 worktree（git worktree add）         ← 秒级，只有 git-tracked 文件
5. EnterWorktree 切换 CWD                    ← 原生工具，不会忘
6. 运行时环境补充（策略菜单）                  ← AI 按项目实际情况选择
7. 初始化 state.json
```

---

## 详细设计

### 1. 会话创建（Phase 1.4 重写）

#### Step 1-3：分支准备（不变）

```
1. 自动识别目标分支（main/master）
2. git branch --list <feature> + 检查目录冲突
3. git checkout -b <feature>
```

#### Step 4：创建 Git Worktree

```bash
# 切回目标分支
git checkout <target-branch>

# 用 git worktree add 创建隔离环境（秒级）
git worktree add .claude/worktrees/devflow-<feature> <feature>
```

此时 worktree 只包含 git-tracked 文件。无 node_modules，无 .env，无本地数据。

#### Step 5：进入 Worktree（关键改进）

**方案 A（优先）：使用 EnterWorktree 原生工具**

```
EnterWorktree path=".claude/worktrees/devflow-<feature>"
```

工具调用成功后，session CWD 自动切换到 worktree 目录。后续所有操作都在 worktree 内。

**方案 B（fallback）：手动 cd**

如果 EnterWorktree 不可用（非 Claude Code 环境），使用 `cd`。

#### Step 6：运行时环境补充（策略菜单）

**核心原则：skill 中列举策略，AI 在具体项目中按实际情况选择。**

```
策略菜单：

A. 包管理器安装（推荐用于 node_modules）
   npm install / pnpm install / yarn install
   前提：lockfile 已提交，本地有缓存 → 通常十几秒

B. Symlink / Junction（推荐用于 node_modules，无需网络）
   Unix:  ln -s <main-repo>/node_modules node_modules
   Win:   mklink /J node_modules <main-repo>\node_modules
   前提：主仓库 node_modules 已安装

C. .worktreeinclude 文件（推荐用于 .env 等小文件）
   在仓库根目录创建 .worktreeinclude，列出需要复制的 gitignored 文件
   EnterWorktree 创建 worktree 时自动复制
   示例内容：
     .env
     .env.local
     config/secrets.json

D. 手动复制（fallback，用于小文件）
   cp <main-repo>/.env .env

E. 本地数据目录处理
   小数据（<10MB）：直接复制
   大数据：symlink / junction，或提示用户配置 .worktreeinclude
```

**AI 执行逻辑：**
1. 检查仓库是否有 `.worktreeinclude` → 有则 C 已生效
2. 检查 `package.json` → 有则按 A 或 B 处理 node_modules
3. 检查 `.env` 等配置文件是否存在 → 按 D 复制
4. 检查是否有本地数据目录 → 按 E 处理
5. 验证：尝试运行项目的启动命令，确认环境可用

#### Step 7：初始化状态文件（不变）

在 worktree 内创建 `devflow/<feature>/state.json`。

---

### 2. CWD 守卫（每个 Phase 开头）

在每个 Phase 开始时，增加轻量检测：

```
检查当前 CWD 是否在 .claude/worktrees/devflow-* 下
  → 是：正常继续
  → 否：警告 "当前不在开发环境副本中。是否要切换到 devflow/<feature> 的 worktree？"
         尝试 EnterWorktree path="..." 恢复
```

这解决了"AI 忘记自己在哪"的问题 — 不依赖 AI 记忆，而是**每次 phase 都检查**。

---

### 3. 会话检测（Step 0 升级）

#### 3.1 检测是否在 worktree 中

参考 superpowers 的 `GIT_DIR != GIT_COMMON` 方法：

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

| 条件 | 含义 | 行为 |
|------|------|------|
| `GIT_DIR == GIT_COMMON` | 在主仓库 | 启动新会话 |
| `GIT_DIR != GIT_COMMON` | 在 worktree 中 | 恢复会话 |

**向后兼容 v2.4：** 如果 git 检测认为在主仓库，但当前路径包含 `.claude/worktrees/devflow-*`，说明是 v2.4 的全量副本（非 git worktree，所以 GIT_DIR == GIT_COMMON），按 worktree 处理。

#### 3.2 恢复逻辑增强

恢复时不仅要读 `state.json`，还要验证当前 worktree 的 feature 分支和 state 中记录的一致。

---

### 4. 清理（Phase 6.5 升级）

**方案 A（优先）：使用 ExitWorktree**

```
ExitWorktree action="remove" discard_changes=false
```

ExitWorktree 自动处理：切回原始目录 + 删除 worktree + 清理分支。

**方案 B（fallback）：手动清理**

```bash
# 切回主仓库
cd <main-repo-root>
# 删除 worktree 目录
rm -rf .claude/worktrees/devflow-<feature>
# 清理 git worktree 注册
git worktree prune
# 删除 feature branch（如果已合并）
git branch -d <feature>
```

---

### 5. .worktreeinclude 引导

在 Phase 1.4 的环境补充步骤中，如果检测到仓库没有 `.worktreeinclude`，AI 提示用户：

> "检测到仓库中没有 `.worktreeinclude` 文件。建议创建此文件以自动同步 gitignored 的运行时文件到 worktree。我可以帮你创建一个，包含常见的配置文件和本地数据目录。是否需要？"

如果用户确认，AI 创建 `.worktreeinclude` 并提交。

---

### 6. settings.json 引导

如果检测到 `worktree.symlinkDirectories` 未配置，提示用户可在 `.claude/settings.json` 中添加：

```json
{
  "worktree": {
    "symlinkDirectories": ["node_modules"]
  }
}
```

这样后续创建 worktree 时，node_modules 自动 symlink，无需手动处理。

---

## 与 v2.4 的对比

| 维度 | v2.4 (rsync) | v3.0 (原生 worktree) |
|------|-------------|---------------------|
| 创建速度 | 分钟级（复制 node_modules） | 秒级（git worktree add） |
| 递归风险 | ⚠️ 有（排除规则不可靠） | ✅ 无（无 bulk copy） |
| CWD 切换 | 手动 cd → AI 常忘 | EnterWorktree 自动切换 |
| 磁盘占用 | 2x 完整仓库 | 共享 git objects + symlink node_modules |
| node_modules | 复制 | symlink 或 npm install（缓存秒级） |
| .env / 配置 | 复制 | .worktreeinclude 自动或手动复制 |
| 清理 | rm -rf | ExitWorktree（原生） |
| 向后兼容 | - | 检测逻辑兼容 v2.4 旧副本 |

---

## 需要修改的文件

| 文件 | 改动 |
|------|------|
| `skills/devflow/SKILL.md` | 主要改动：Phase 1.4 重写、Step 0 升级、Phase 6.5 升级、CWD 守卫 |
| `skills/devflow/_SKILL.md` | 同步（sync-skills.js） |

**不涉及：**
- 其他 6 个 skill 文件（clarify/breakdown/blueprint/implement/verify/discover）— 不直接涉及隔离逻辑
- `scripts/sync-skills.js` — 无需改动
- 插件 manifest — 版本号 bump 到 3.0.0

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| EnterWorktree 在非 Claude Code 环境不可用 | 保留 `cd` fallback + CWD 守卫检测 |
| symlink node_modules 在某些工具下不兼容 | 策略菜单提供 `npm install` 选项（安全但需要网络） |
| .worktreeinclude 需要用户手动创建 | AI 主动检测并引导创建 |
| v2.4 旧副本可能残留 | Step 0 检测兼容；提示用户手动清理 |

---

## 参考

- [Claude Code Worktree Docs](https://code.claude.com/docs/en/worktrees)
- [Superpowers using-git-worktrees (v6.0.3)](https://github.com/anthropics/claude-plugins-official)
- [Baljeet Singh: Automating Claude Code Worktree Setup](https://baljeetsingh.in/blog/automating-claude-code-worktree-setup-env-node-modules-and-ports/)
- [MoAI Worktree Management](https://github.com/modu-ai/moai-adk)
- [Agent Workspace Fabric](https://github.com/dimileeh/agent-workspace-fabric)
