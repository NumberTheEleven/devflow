---
name: discover
description: 当没有特定需求时，扫描当前项目以寻找优化机会。发现性能、架构、可维护性或功能缺失方面的改进空间。
argument-hint: [项目路径]
---

# /devflow:discover — 项目发现

## 使用场景

你没有任何具体的需求或任务。你想了解当前项目有哪些可以改进的地方。该 skill 会扫描代码库并生成一份按优先级排序的优化机会列表。

**此 skill 由用户直接调用。** 请勿自动触发。

## 流程

### 步骤 1：了解项目

如果提供了 `[project-path]`，则将所有扫描范围限定在该目录下。否则使用当前工作目录。

阅读关键项目文件以了解结构：
- `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / `build.gradle`（存在哪个就读哪个）
- `README.md` 或 `CONTRIBUTING.md`
- 顶层目录结构

### 步骤 2：扫描机会

运行以下分析：

**代码质量：**
- 使用 Glob 查找源文件，然后检查行数，找出大文件（>500 行）
- 查找高复杂度文件：寻找深层嵌套的 `if`/`for`/`while` 块、超过约 50 行的函数、过度分支

**架构（Architecture）：**
- 识别循环依赖或紧耦合模块
- 检查是否缺少关注点分离（例如，业务逻辑写在 UI 文件中）
- 查找跨文件重复的代码模式

**可维护性（Maintainability）：**
- 缺失测试：将 `src/` 文件与 `test/` 或 `__tests__/` 文件进行对比
- 缺失或过时的文档
- TODO/FIXME/HACK 注释：使用 Grep 工具在源文件中搜索 `TODO|FIXME|HACK`
- 已弃用的 API 使用

**性能（Performance）：**
- N+1 查询模式
- 缺失缓存层
- 可并行化的同步操作

**安全（Security）：**
- 源代码文件中硬编码的密钥、令牌或凭证
- 存在已知 CVE 的过时依赖（检查依赖文件）
- 不安全的输入处理或缺失的清理

**功能缺失（Feature Gap）：**
- 缺失的错误处理或边界情况覆盖
- 缺失的输入校验
- 缺失的日志/可观测性

**演示代码异味（Demo Smells，表明代码处于演示级别而非生产级别）：**
- 硬编码的模拟数据或 API 响应，而非真实数据源
- 使用 console.log 而非 proper logging（ proper logging）
- UI 中缺失 loading、empty 和 error 状态
- 没有 error boundaries 或全局错误处理
- 点击处理函数没有 loading/disabled 状态（提交没有防抖）
- 源代码文件中硬编码的 URL、密钥或秘密
- 没有表单校验或清理
- 关键路径上有 "TODO: implement this later" 之类的注释
- 静态/只读 UI，没有用户交互流程
- 破坏性操作缺少确认对话框

### 步骤 3：生成优先级报告

将输出格式化为结构化报告：

```markdown
## 项目优化机会

### 紧急（P0）
- [ ] **[Category（分类）]** 问题描述。受影响文件：`path/file.ts`。建议修复：...

### 高优先级（P1）
- [ ] ...

### 中优先级（P2）
- [ ] ...

### 低优先级（P3）
- [ ] ...
```

每个条目必须包含：
- 优先级（P0-P3）
- 分类（Performance（性能）/ Architecture（架构）/ Maintainability（可维护性）/ Feature Gap（功能缺失）/ Security（安全））
- 问题清晰描述
- 受影响的具体文件路径
- 具体的修复建议

### 步骤 4：请用户选择

在展示报告后，请用户选择一个或多个项目来推进。然后建议：

> "选择一个项目来开始。我建议从 P0 项目开始。选定后，我们将使用 /devflow:clarify 来展开需求。"

## 交接

当用户选定某个项目时，建议：
- `/devflow:clarify` — 将选定的优化项展开为清晰的需求

不要自动调用 clarify。等待用户确认。
