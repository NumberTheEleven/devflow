# DevFlow 验证报告

**日期:** 2026-06-09
**应用:** n/a（skill 文档变更，无可运行 App）
**Feature:** verify-layered

---

## 验证计划

由于本次改动为 skill 文档本身，无明显可运行的应用程序，所有 23 条 TC 路由到 L3 结构化手工验证。

| TC | 路由 | 依据 |
|----|------|------|
| TC-001 ~ TC-023 | L3 | Playwright 无目标 URL，全部降级到 L3 手工验证 |

---

## L1: 烟雾扫描

> ⚠️ 跳过 — 无可扫描的应用程序（本次变更为 skill 文档）

---

## L2: 交互验证追踪

> ⚠️ 跳过 — 无可交互的应用程序（本次变更为 skill 文档）

---

## L3: 结构化手工验证

### TC-001: L1 烟雾扫描 4 类检查逐页执行
- **证据类型:** DOM snapshot（文档审查）
- **证据:** verify skill Steps 3-7 完整覆盖 Console Error (Step 4)、Network Health (Step 5)、Runtime Health (Step 6)、DOM Snapshot (Step 7)。Step 8 汇总所有路由的逐页结果。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-002: L1 通过时措辞不再暗示"验证完成"
- **证据类型:** 文档审查
- **证据:** Step 8 L1 聚合结果末尾包含："> ⚠️ L1 烟雾扫描仅检查页面基础设施是否正常（不报错、不崩溃、元素存在）。不代表业务功能验证通过。业务功能验证由 L2 和 L3 完成。"
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-003: L1 console error 仍触发 FAIL
- **证据类型:** 文档审查
- **证据:** Step 4 明确："Any console.error NOT in the allowlist → **FAIL**"。Allowlist 包含 favicon.ico 404、source map 404、Chrome extension errors。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-004: L1 allowlist 可配置
- **证据类型:** 文档审查
- **证据:** Step 4 包含："**To customize the allowlist:** Edit the allowlist items above in this skill file. Add project-specific patterns (e.g., third-party script errors you cannot fix) with a comment explaining why."
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-005: L2 识别需要交互验证的 TC
- **证据类型:** 文档审查
- **证据:** Step 2.1 关键词分层映射表包含 "点击、输入、填写、提交..." → L2。Step 2.2 路由优先级规则第一条：TC type=端到端 AND interaction keywords → L2。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-006: L2 Playwright 执行操作步骤
- **证据类型:** 文档审查
- **证据:** Step 9 解析操作步骤为 Playwright 工具调用（navigate→click→type→wait→snapshot）。Step 10 执行交互序列，包含 pre-action snapshot + action + wait + post-action snapshot 的完整流程。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-007: L2 用 DOM 结构变化判断操作是否生效
- **证据类型:** 文档审查
- **证据:** Step 11 明确规定："Do NOT rely on exact text content... Instead, judge based on semantic DOM structure changes"。附带 7 类预期行为与 DOM 变化判断的对照表（form submitted/validation error/navigation/modal/content loaded/button disabled）。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-008: L2 Playwright 不可用时降级为手工
- **证据类型:** 文档审查
- **证据:** Step 13 完整定义降级流程："Playwright MCP 不可用，L2 交互验证降级为手工引导模式。" 附带引导用户手工操作的步骤模板。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-009: L2 产生 Interaction Trace
- **证据类型:** 文档审查
- **证据:** Step 10 定义 Interaction Trace 格式：操作描述 + 操作前 DOM 摘要 + 操作后 DOM 摘要 + DOM 变化 + 结果。提供两个示例（页面加载 trace + 表单校验 trace）。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-010: L3 无证据 TC 标记为 unverified
- **证据类型:** 文档审查
- **证据:** Step 14:"🔴 No evidence: TC status must be unverified, not done"。Step 16:"No evidence → unverified: A TC with zero evidence cannot be marked done. It stays unverified and counts against the depth score."
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-011: L3 用户跳过的 TC 标记 skipped + 原因
- **证据类型:** 文档审查
- **证据:** Step 16:"User skipped → skipped with reason: If the user explicitly says 'skip this TC,' record it as skipped with the reason they give."
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-012: L3 证据要求矩阵可查
- **证据类型:** 文档审查
- **证据:** Step 14 包含完整的 Evidence Requirements Matrix 表格，覆盖所有 TC 类型（端到端/手工视觉/手工权限/手工业务逻辑/手工其他），每种标注最小证据和可接受证据。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-013: TC 路由引擎按关键词分类
- **证据类型:** 文档审查
- **证据:** Step 2.1 含完整关键词→层级映射表和 TC 类型→默认层级表。Step 2.2 定义路由优先级 4 条规则。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-014: 路由结果展示并允许用户调整
- **证据类型:** 文档审查
- **证据:** Step 2.3:"路由计划如上。是否需要调整？[Y] 确认执行 / [调整 TC-xxx 从 X 层到 Y 层]"
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-015: 路由决策记录到日志
- **证据类型:** 文档审查
- **证据:** Step 2.3:"Record any user adjustments. Once confirmed, write the final routing plan to devflow/verification-log.md as the first section." Step 19 报告模板包含"验证计划"表（TC/路由/依据列）和"路由调整"字段。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-016: 报告包含验证深度指标
- **证据类型:** 文档审查
- **证据:** Step 18 定义 Verification Depth Score 和 Evidence Coverage Score 的计算公式。Step 19 报告模板包含完整"深度评分"表格。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-017: 深度 < 100% 时明确警告
- **证据类型:** 文档审查
- **证据:** Step 21:"When depth < 100%: ⚠️ 验证未完全完成。验证深度 [X]%，[N] 条 TC 未执行或无证据。是否接受当前结果？..." 报告结论模板中有明确警告。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-018: 报告包含 TC 分层覆盖分布
- **证据类型:** 文档审查
- **证据:** Step 18:"Layer Distribution: L1 coverage: X TCs / L2 coverage: Y TCs (Z auto-executed, W degraded to manual) / L3 coverage: V TCs"。Step 19 报告模板包含"分层覆盖"条。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-019: verify skill 描述三层架构
- **证据类型:** 文档审查
- **证据:** Frontmatter description:"Uses a three-layer approach — L1 smoke scan... L2 interaction verification... L3 structured manual verification..."。When to Use 包含三层对比表。全文不再出现"Phase 1/Phase 2"二分法。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-020: devflow 主 skill Phase 5 引用更新
- **证据类型:** 文档审查
- **证据:** devflow SKILL.md 流程总览行："Phase 5: 测试验证 (verify) → L1烟雾 + L2交互 + L3手工，证据驱动 + 智能回退"。5.1 流程列出 8 步（含路由、L1/L2/L3、深度评分）。5.2 验证结果有三种分支（全通过/深度不足/有失败项）。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-021: 统一报告包含全部三层结果
- **证据类型:** 文档审查
- **证据:** Step 19 报告模板单一文件包含：L1 烟雾扫描表格 + L2 交互验证追踪列表 + L3 结构化手工验证记录。不再是两份分离的报告。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-022: FAIL 项包含完整调试信息
- **证据类型:** 文档审查
- **证据:** Step 19 失败项模板包含：操作描述 + 预期 vs 实际 + DOM 变化 + 严重性 + 根因分析 + 建议。TC-004 示例展示了完整的失败记录。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

### TC-023: 报告结论明确区分三种结果
- **证据类型:** 文档审查
- **证据:** Step 21 区分三种结论：(1) 全部通过→"✅ 全部验证通过（深度 100%，证据覆盖率 100%）"(2) 深度不足→"⚠️ 验证未完全完成..."(3) 有失败→Step 20 Smart Rollback 触发。
- **证据等级:** 🟢 Strong
- **结果:** ✅ done

---

## 深度评分

| 指标 | 值 | 状态 |
|------|-----|------|
| 总 TC 数 | 23 | — |
| 验证深度 | 23/23 (100%) | ✅ |
| 证据覆盖率 | 23/23 (100%) | ✅ |
| n/a (不适用) | 0 | — |

**分层覆盖:**
- L1 覆盖: 0 条（无 App 可扫描）
- L2 覆盖: 0 条（无 App 可交互）
- L3 覆盖: 23 条（全部手工验证，文档审查）

**注：** 本次变更为 skill 文档层面改动，所有 TC 通过 L3 文档审查完成验证。下次对实际应用的 verify 流程将完整走 L1+L2+L3 三层。

---

## 需求验收核对

| 需求 | 状态 | 证据 |
|------|------|------|
| R-001 L1 烟雾扫描层 | ✅ 已完成 | TC-001~TC-004 全部通过 |
| R-002 L2 交互验证层 | ✅ 已完成 | TC-005~TC-009 全部通过 |
| R-003 L3 结构化手工验证层 | ✅ 已完成 | TC-010~TC-012 全部通过 |
| R-004 TC 智能路由引擎 | ✅ 已完成 | TC-013~TC-015 全部通过 |
| R-005 验证深度评分体系 | ✅ 已完成 | TC-016~TC-018 全部通过 |
| R-006 verify skill 文档更新 | ✅ 已完成 | TC-019~TC-020 全部通过 |
| R-007 验证报告格式升级 | ✅ 已完成 | TC-021~TC-023 全部通过 |

---

## 结论

> ✅ **全部验证通过（深度 100%，证据覆盖率 100%）。** 23/23 TC 通过 L3 文档审查，7/7 需求验收标准全部满足。skills/verify/_SKILL.md 已从 two-phase pipeline 完整升级为 21-step L1+L2+L3 三层架构；skills/devflow/SKILL.md Phase 5 描述已同步更新。
