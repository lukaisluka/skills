# Integration Test Investigation Skills — PRD

> **Rev 5(2026-09-21)修订要点**
>
> - 评估脱敏:触发评估使用人工构造的 trigger 查询集,不依赖真实事故(§29);输出质量评估改为前向收集——真实调查结案后回填 case,不再要求预先存在历史 case(§26、§29)
>
> **Rev 4(2026-09-21)修订要点**
>
> - Skill 内容(`SKILL.md`、`references/`,含 frontmatter `description`)一律纯英文,不出现中文;用户用中文提问时的跨语言触发匹配交给宿主机制(§5.5、§9.2)
>
> **Rev 3(2026-09-21)修订要点**
>
> - 文档目录约定:PRD 移至 `docs/prd/`,ADR 位于 `docs/adr/`,agent 配置位于 `docs/agents/`,仓库根不再散落文档(§26)
>
> **Rev 2(2026-09-21)修订要点**
>
> - 渐进式加载(Progressive Disclosure)确定为 Day 1 结构:Skill 一律采用子目录形式,`SKILL.md` 为主入口,`references/` 承载重内容,按需加载;不再作为"后续再说"的演进项
> - 仓库定位明确为**多 Skill 仓库**,Phase 1 只包含第一个 Skill
> - 新增:触发 description 规划(§9.2)、失败数据获取策略(§12.1)、聚类前上下文管理(§13.3)、日志留存与时间精度约束(§14.3)、"同 commit 他处通过"优先历史信号(§14.4)、Anchor 补全启发式(§7)、语言规范(§5.5)、调查只读原则(§5.6)、轻量历史 case 对照(§26 / §29)

---

## 1. 背景

现有项目已经具备成熟的自动化 Integration Test Pipeline。

当前主要问题已经不再是"如何自动执行测试",而是 Pipeline 执行完成后,尤其是测试失败时,仍然需要工程师投入大量时间完成:

- 查看 Pipeline / Job 状态
- 分析失败 Test Case
- 阅读测试日志和应用日志
- 判断多个 Failure 是否属于同一个根因
- 分析相关 MR / Commit / Code Diff
- 检查 Kubernetes 测试环境状态
- 判断问题属于代码、测试、环境还是依赖
- 搜索历史 Pipeline、MR、Issue 中是否出现过类似问题
- 提出下一步验证或处理方案

这些工作具有较强的上下文理解、跨系统信息关联和工程推理特征,适合由 AI Agent 辅助完成。

当前常用 Coding Agent 已经具备较强的代码理解和工具调用能力,因此本项目不重新开发独立 AI Agent,而是通过标准化 Skills,为已有 Agent 增加 Integration Test Investigation 能力。

---

## 2. 产品定位

本项目提供一组遵循通用 Agent Skills 标准的可安装 Skills。

用户将 Skills 安装到已有的 Coding Agent 后,可以直接通过自然语言让 Agent 调查 Integration Test Pipeline、MR、Test Failure 和测试环境问题。

产品本身不提供独立 Agent Runtime,不提供独立聊天界面,也不负责 GitLab、Kubernetes 等基础访问能力。

宿主 Agent 负责:

- Conversation / Session
- LLM Runtime
- Tool Calling
- MCP 调用
- Shell / Code Search
- 文件访问
- 用户交互

本项目负责:

- Integration Test Investigation 方法论
- 标准调查 Workflow
- Failure 分析规则
- Hypothesis 验证方法
- 调查结果输出规范
- 项目知识使用方式

核心定位:

> Teach existing AI agents how to investigate integration testing problems effectively.

---

## 3. Phase 1 目标

第一阶段目标是快速实现一个可以实际使用的 Integration Test Investigation Skill 原型。

用户能够向已经安装 Skill 的 Agent 提供一个远程 GitLab 项目以及 MR、Pipeline、Job、Commit、Test Case 等任意已知线索。

Agent 利用用户已经配置好的 GitLab、Kubernetes、代码及其他环境访问能力,自主完成调查,并输出有证据支持的调查结论。

Phase 1 重点验证:

> 一套设计良好的 Integration Test Investigation 方法论,是否能够显著提升通用 Coding Agent 调查 Integration Test 问题的能力。

---

## 4. 非目标

Phase 1 不包含:

- 开发独立 AI Agent Runtime
- 开发独立 CLI 产品
- 开发 Web UI
- 开发 Workflow Engine
- Multi-Agent / Agent Team
- 自动修改业务代码
- 自动修改 Test Case
- 自动创建 Merge Request
- 自动 Merge
- 自动修复 Kubernetes 环境
- 自动执行 Release Decision
- GitLab Webhook 自动触发
- 复杂权限、安全和审计体系
- 跨 Investigation 的长期 Memory
- 自研 Skills 安装框架或脚手架
- 绑定某个具体 Coding Agent
- 绑定某个具体 GitLab MCP 或 Kubernetes MCP

---

## 5. 设计原则

### 5.1 基于通用 Agent Skills 标准,渐进式加载为 Day 1 结构

Skill 使用标准的 Skill 目录和 `SKILL.md` 形式实现。

渐进式加载不是后续优化,而是第一版的结构前提:

- `SKILL.md`:frontmatter 触发描述 + 调查工作流主干 + 核心判断规则,保持精简,是常驻上下文的入口
- `references/`:重内容(失败分类细则、报告模板、数据获取方法等),只在调查走到对应分支时按需加载

内容归属判断标准:

- 工作流每一步都需要遵守的规则 → `SKILL.md`
- 只有特定调查分支才需要的细则、模板、长清单 → `references/`

Phase 1 仍然只使用 Markdown instructions,不引入 scripts / assets。只有当后续明确发现确定性程序处理能够显著提升效果时,才考虑增加。

### 5.2 不依赖宿主 Agent 专有能力

核心 Skill 不依赖:

- Hooks
- Subagents
- Agent-specific Commands
- Agent-specific Plugins
- 特定 Todo 实现
- 特定 Context Fork 机制
- 特定 Tool Name

应尽可能运行于支持 Agent Skills 的不同 Coding Agent。

### 5.3 Skill 描述能力和方法,不描述具体工具实现

例如 Skill 应描述:

> Retrieve the relevant pipeline, jobs, merge request and commit information using the available Git hosting capabilities.

而不是:

> Call `gitlab_mcp.get_pipeline`.

Kubernetes 调查同理。

Skill 定义:

- 应该查什么
- 为什么查
- 如何判断结果
- 什么时候继续深入
- 什么时候停止

具体调用哪个 MCP、CLI 或 Tool,由宿主 Agent 根据当前可用能力决定。

### 5.4 Remote Repository First

主要工作对象为公司内部 Remote GitLab Project。

Agent 不应要求用户首先将仓库 Clone 到本地。

典型环境:

```text
Agent
├── GitLab access / MCP
├── Kubernetes access
└── other environment capabilities
```

如果 Agent 当前拥有 Local Checkout,则可将其作为增强能力使用。

Local Checkout 可用于:

- 更高效的全文代码搜索
- 跨文件导航
- Git history 搜索
- 调用关系分析
- 大范围源码探索

但 Local Checkout 不是启动 Investigation 的必要条件。

### 5.5 语言规范

- Skill 内容(`SKILL.md` 与 `references/`,含 frontmatter `description`)一律纯英文,不出现中文,遵循 Skills 生态惯例,保证指令跨宿主的稳定性
- 调查报告与用户交互跟随用户会话语言(如中文)——这是运行时输出行为,由 Skill 指令规定,不改变 Skill 文件本身的语言

### 5.6 调查动作只读原则

- Investigation 过程中的操作应倾向只读:查询、描述、日志读取等
- 避免在调查中即兴执行带副作用的命令(如 `kubectl exec` / `delete` / `edit`、写数据库、改配置)
- Phase 1 Skill 不执行任何修复动作,修复建议一律以 Recommended Next Step 形式输出(见 §21)

---

## 6. 用户场景

### 6.1 Pipeline Failure Investigation

用户:

> 帮我调查 project `foo/bar` 的 pipeline 18372 为什么失败。

Agent 应自主:

- 查 Pipeline
- 找 Failed Jobs
- 找 Failed Tests
- 分析日志
- 对 Failure 进行聚类
- 查 MR / Commit
- 查相关代码
- 查测试环境
- 查历史问题
- 形成 Hypothesis
- 验证 Hypothesis
- 输出 Investigation Report

### 6.2 MR Regression Investigation

用户:

> 看一下 `foo/bar` 的 MR !873,Integration Test 为什么失败。

Agent应从 MR 出发:

```text
MR
→ Pipeline
→ Failed Job
→ Failed Tests
→ Diff
→ Runtime
→ History
→ Conclusion
```

### 6.3 Test Case Investigation

用户:

> pipeline 18372 里面 `test_cancel_order` 为什么失败?

Agent可以只调查特定 Test Case 及其相关上下文。

### 6.4 Runtime Investigation

用户:

> 昨晚这批 Integration Test 大量 timeout,看看是不是测试环境的问题。

Agent可以重点使用 Kubernetes 和 Runtime Evidence。

### 6.5 Follow-up Investigation

第一次调查之后,用户可以继续:

> 为什么你觉得不是这次 MR 导致的?

或者:

> 再深入查一下 Redis 那个异常。

继续交互和 Session Context 由宿主 Agent负责。

Skill需要能够在已有调查上下文中继续工作,而不是每次从头开始。

---

## 7. 输入模型

Skill 不要求固定命令参数。

用户可以提供任意数量的 Investigation Anchor。

可能包括:

- GitLab Project
- MR
- Pipeline
- Job
- Commit SHA
- Test Case
- Test Suite
- Kubernetes Namespace
- Pod
- 时间范围
- Error Message
- Log Snippet
- 用户自然语言描述

最小输入通常可以只有:

```text
Project + Pipeline
```

例如:

> 调查 `group/order-engine` pipeline 12831。

Agent 应自行补全其他上下文。

Anchor 不完整时的常用补全启发式:

- 只有 MR → 取其 head pipeline
- 只有 Commit → 查找包含该 commit 的 pipeline(通常为 branch pipeline)
- 只有 Test Case 名 → 在相关时间范围的 pipeline 中搜索该测试的执行记录
- 只有时间范围 / 症状描述 → 从该时间窗内最近的 failed pipelines 入手
- 只有 Pod / Namespace → 反查该环境对应的 Project 与近期 pipeline

如果用户已经提供更多信息,应直接使用,不应重复询问已知信息。

---

## 8. 核心 Skill

Phase 1 只实现一个核心 Skill:

```text
investigate-integration-tests
```

Day 1 目录结构(渐进式加载):

```text
skills/
└── investigate-integration-tests/
    ├── SKILL.md
    └── references/
        ├── failure-data-sources.md
        ├── failure-classification.md
        └── investigation-report.md
```

内容分工:

- `SKILL.md`:frontmatter 触发描述 + 调查工作流主干(§10–§22 的核心规则)+ 各阶段判断标准
- `references/failure-data-sources.md`:失败测试结构化数据的获取优先级与退化路径(§12.1 的细则)
- `references/failure-classification.md`:失败分类定义与各类别的判别特征(§18 的细则)
- `references/investigation-report.md`:报告输出模板与 UNKNOWN 模板(§20 的细则)

后续允许按需增加 references(如 runtime-investigation.md、historical-investigation.md),但以"实际调查中发现 Agent 反复需要"为准,不提前堆料。

---

## 9. Skill Trigger Scope

### 9.1 触发场景

Skill 应适用于以下用户意图:

- Investigation of Integration Test failures
- CI / Pipeline failures related to integration testing
- MR / Commit suspected of causing Integration Test regression
- Runtime failures affecting tests
- Environment-related Integration Test failures
- Dependency-related failures
- Test-data-related failures
- Suspected flaky tests
- Multiple failed tests requiring root-cause clustering
- Follow-up questions about an ongoing Integration Test investigation

Skill 不应将自己限定为"Pipeline Failed 才能使用"。

### 9.2 触发描述(frontmatter description)

`description` 字段是宿主 Agent 决定是否加载本 Skill 的第一关口,必须专门设计,不能随手写:

- 覆盖用户真实说法对应的语义:调查 pipeline 失败、分析 MR 测试失败、查某个 test case 为什么挂、疑似测试环境问题、大量超时、flaky test、失败根因聚类等
- 不限定于"pipeline failed"一种措辞
- 避免过宽导致与通用 debugging / code review 场景抢触发
- description 保持纯英文;用户用中文提问时的跨语言匹配依赖宿主的触发机制,不在 description 中堆叠中文关键词

---

## 10. Investigation Workflow

Workflow 不由独立 Workflow Engine 实现。

Workflow 作为标准 Investigation Protocol 直接定义在 Skill 中,由宿主 Agent 执行。

固定的是 Investigation Methodology,不固定具体 Tool 调用路径。

整体流程:

```text
Establish Context
       ↓
Inspect Failures
       ↓
Cluster Failures
       ↓
Investigate
       ↓
Form Hypotheses
       ↓
Validate Hypotheses
       ↓
Report
```

---

## 11. Phase 1 — Establish Context

Agent 首先建立本次 Investigation Context。

应尽可能确认:

- Project
- MR,如存在
- Pipeline
- Failed Jobs
- Commit
- Test Suite
- Test Environment
- Approximate Failure Time
- Relevant Services
- Pipeline 类型(MR pipeline / branch pipeline / scheduled nightly)——不同类型的归因先验不同:MR pipeline 优先怀疑本 MR 变更;nightly 优先怀疑环境漂移与依赖变化

允许部分信息缺失。

原则:

> Do not block the investigation simply because some context is unavailable.

当 Agent 已经拥有足够信息定位相关 Pipeline、Job 或 Test Failure 时,即可进入下一阶段。

---

## 12. Phase 2 — Inspect Failures

### 12.1 失败数据获取

理解 Failure 的前提是先拿到结构化的失败数据。获取优先级:

1. Pipeline / Job 的 test report(如 GitLab JUnit report integration,可拿到 test case 级结构化结果)
2. Job artifacts 中的测试结果文件
3. 退化路径:解析 job trace 原始日志,提取失败摘要

各来源的判读方法与日志启发式见 `references/failure-data-sources.md`。

这一步的质量决定后续所有阶段。如果结构化数据不可得、日志不可得,应将"数据获取障碍"本身如实纳入调查结论,而不是基于残缺信息硬猜。

### 12.2 需要关注的 Failure 信号

Agent需要首先理解实际 Failure,而不是直接寻找 Root Cause。

至少关注:

- Failed Jobs
- Failed Test Cases
- Error Message
- Exception
- Stack Trace
- Failure Timestamp
- Setup / Fixture Failure
- Teardown Failure
- Timeout
- Dependency Failure
- Cascading Failure

重要原则:

> Do not assume every failed test represents an independent defect.

Agent应首先判断 Failure 是独立问题还是某个公共故障导致的大量级联失败。

---

## 13. Phase 3 — Cluster Failures

### 13.1 聚类前的上下文管理

禁止把全量失败清单原样倒入上下文后再聚类。应先做聚合与采样:

- 按 error message 签名 / exception / suite 预聚合,得到计数与分布
- 每个 cluster 选取 Representative Failure 进入深入调查
- 全量清单只在需要核对覆盖面时按需分页查看

目标是在聚类完成前,就把上下文占用控制在与判断直接相关的规模。

### 13.2 聚类维度

多个失败 Test Case 应优先尝试进行聚类。

可以考虑:

- 相同或高度相似的 Error Message
- 相同 Exception
- 相同 Stack Frame
- 相同 Dependency
- 相同 Endpoint
- 相同 Fixture
- 相同 Setup Failure
- 相近 Failure Timestamp
- 相同 Service
- 相同 Runtime Error

禁止仅因为多个 Test 出现在同一个 Pipeline 中就归为一类。

### 13.3 Representative Failure

对于每个 Cluster,应选取 Representative Failure 做深入调查。

目标是把:

```text
100 failed tests
```

转化为类似:

```text
Cluster A — 72 tests
Cluster B — 21 tests
Cluster C — 7 tests
```

而不是机械调查 100 次。

---

## 14. Phase 4 — Investigate

Investigation 阶段允许 Agent 根据当前证据自主选择调查路径。

主要包括四个方向。

### 14.1 Test Investigation

调查:

- Test implementation
- Fixture
- Setup
- Cleanup
- Test assumptions
- Test data
- Assertions
- Timing dependency

目标是判断失败是否可能来自 Test 本身。

### 14.2 Code Change Investigation

调查:

- MR Diff
- Commit Diff
- Changed Modules
- Relevant Source Files
- Configuration Changes
- Dependency Changes
- Execution Path

重点判断:

> 当前代码变化是否能够解释观察到的 Failure。

不要仅仅因为某段代码在本次 MR 中被修改,就认定它是 Root Cause。

### 14.3 Runtime Investigation

使用当前可用的环境能力调查:

- Kubernetes workload status
- Pod status
- Restarts
- Events
- Application logs
- Dependency logs
- Deployment status
- Version mismatch
- Database
- Cache
- Messaging infrastructure
- Network-related errors
- Resource-related anomalies

Runtime Investigation 应围绕 Failure Time Window 展开。

重点寻找:

```text
Failure
↕
Runtime Event
```

之间是否存在可靠的时间和因果关联。

日志留存与时间精度约束:

- 先确认失败时间窗内的日志是否仍可获得:Pod 重启后 `kubectl logs` 中旧日志可能已丢失;GitLab 长 job 的 trace 可能被截断。日志不可得时,转向集中式日志系统、artifacts 等替代来源;仍不可得,则将"日志缺失"如实记为 Missing Evidence,而不是假装已排除该方向
- 测试报告中的时间戳通常是测试**完成时间**而非失败发生时间;与 K8s event / 应用日志对时间轴时应保留分钟级余量,避免用秒级精确匹配制造虚假的关联或虚假的排除

### 14.4 Historical Investigation

首选动作(最便宜、单点信息量最大):

> 检查同一 commit 的同一测试在其他 pipeline 或 retry 中是否通过。

- 通过 → 强证据否定"本次代码变更导致回归",指向 flaky / 环境 / 依赖
- 失败且可追溯到更早的 commit → 说明问题先于本次变更存在

其次可以搜索:

- Previous Pipelines
- Historical Failures
- Merge Requests
- Issues
- Previous Commits
- Known Problems

用途包括:

- 判断 Failure 是否以前出现过
- 判断当前 MR 是否真正改变了 Failure 行为
- 识别 flaky 特征
- 找历史 Root Cause 和 Fix

---

## 15. Adaptive Investigation

Agent 不应该机械执行所有调查路径。

例如已经有明确证据表明数据库在 Failure Time Window 完全不可用时,不需要为了完成流程而遍历所有代码。

原则:

> Choose investigation paths based on available evidence. Do not mechanically execute every possible path.

同时,不应在看到第一个可疑信号后立即停止。

Agent需要判断当前证据是否足以支持 Root Cause。

---

## 16. Hypothesis Formation

Agent 在调查过程中应将:

- Observation
- Hypothesis
- Conclusion

明确区分。

对于一个 Failure Cluster,可以形成最多若干个主要 Hypothesis。

每个 Hypothesis 应至少考虑:

- Proposed Cause
- Supporting Evidence
- Missing Evidence
- Potential Contradiction
- Evidence that could disprove the hypothesis

示例:

```text
Hypothesis:
Redis restart caused order tests to timeout.

Supporting Evidence:
- 18 tests failed within the same five-second window.
- Redis pod restarted during that period.
- Application logs contain connection reset errors.

Missing Evidence:
- Confirmation that all affected execution paths require Redis.

Possible Contradiction:
- Some affected requests may not access Redis.
```

---

## 17. Hypothesis Validation

在输出 Root Cause 之前,Agent必须执行验证。

至少:

1. 寻找支持当前主要 Hypothesis 的证据
2. 主动寻找可能的反证
3. 与其他合理 Hypothesis 比较
4. 区分 Correlation 和 Causation
5. 判断现有 Evidence 是否足够

禁止:

> 发现一个可疑日志,然后直接宣布 Root Cause。

如果 Evidence 不充分,应明确保留不确定性。

---

## 18. Failure Classification

调查结果应尽可能归类到以下类型:

- Application Regression
- Test Defect
- Flaky Test
- Environment / Infrastructure Issue
- Dependency Failure
- Test Data / State Issue
- Configuration / Version Mismatch
- Unknown

允许多个 Failure Cluster 属于不同类别。

各类别的定义与判别特征见 `references/failure-classification.md`。

---

## 19. Confidence

结论使用离散 Confidence:

- HIGH
- MEDIUM
- LOW

不使用类似:

```text
87%
92%
```

这种模型无法可靠校准的伪精确概率。

建议:

### HIGH

存在直接证据,或者多个独立证据共同支持结论,且未发现明显反证。

### MEDIUM

现有 Evidence 与某个解释高度一致,但仍缺少关键验证信息。

### LOW

目前仅存在有限线索,结论主要是待验证 Hypothesis。

如果证据不足,可以直接输出:

```text
UNKNOWN
```

Unknown 是合法的 Investigation Result。

---

## 20. Investigation Output

默认输出应简洁、工程化,并优先突出 Root Cause 和 Evidence。

完整报告模板(含 UNKNOWN 模板)见 `references/investigation-report.md`,核心结构:

```text
## Summary

Project:
MR:
Pipeline:
Failed jobs:
Failed tests:
Failure clusters:

## Cluster 1

Affected tests:

Observed failure:

Classification:

Likely cause:

Supporting evidence:
- ...
- ...

Contradicting evidence:
- ...

Confidence:
HIGH / MEDIUM / LOW

Recommended next step:
...

## Cluster 2
...
```

如果无法确定 Root Cause:

```text
Conclusion:
UNKNOWN

What is known:
...

What has been ruled out:
...

Most likely remaining hypotheses:
...

Recommended next evidence:
...
```

---

## 21. Recommended Next Step

Phase 1 Agent 不负责自动执行有副作用的修复操作。

但应给出明确的下一步建议,例如:

- rerun 某个 Test Case
- rerun 某个 Test Cluster
- 检查某个特定时间段日志
- 验证某个 Dependency
- 检查某个 MR 代码路径
- 对比另一个成功 Pipeline
- 修复某个疑似 Test Fixture

建议应尽量具体,而不是:

> Check the logs.

更好的形式:

> Compare the `order-engine` logs between 10:31:10–10:31:20 with the PostgreSQL pod restart event, then rerun the affected cancel-order test group.

---

## 22. Follow-up Conversation

Skill 必须适合持续调查,而不是只生成一次 Report。

例如第一次输出:

> 最可能是 PostgreSQL Connection Exhaustion。

用户继续:

> 为什么你认为不是 MR !832 导致的?

Agent 应基于已有 Investigation Context 继续:

- 查看 MR
- 检查当前 Hypothesis
- 获取新的 Evidence
- 修正或确认原结论

Agent 应允许随着新证据出现更新结论。

---

## 23. 项目知识

Phase 1 不要求单独执行 Setup。

Agent 可以使用:

- Repository Documentation
- CI Configuration
- README
- Existing Troubleshooting Docs
- User-provided Project Knowledge
- Existing Agent Context

如果公司后续发现 Agent 每次重复理解项目成本较高,可以增加可选的 Project Context / Project Knowledge 机制。

该能力不属于 Phase 1 必要条件。

---

## 24. Local Checkout

Local Checkout 是增强能力,不是前置条件。

如果存在 Local Repository,Agent可优先使用其进行:

- Full-text Search
- Cross-file Navigation
- Git History Search
- Static Investigation
- Broad Code Exploration

如果不存在,则继续通过 GitLab Remote Capabilities 完成调查。

Skill 不应要求用户 Clone Repository 后才能运行。

---

## 25. Tool Capability Assumptions

Phase 1 假定用户自行提供适当的 Agent Tools。

典型环境可能包含:

```text
GitLab
Kubernetes
Source Code
Logs
Shell
Other internal systems
```

本项目不负责实现这些能力。

Skill只依赖"能力语义",不依赖具体 Tool Name。

---

## 26. Repository Structure

本仓库是**多 Skill 仓库**,Phase 1 只包含第一个 Skill。文档统一放在 `docs/` 下的专用目录:

```text
(仓库根)
├── README.md
├── LICENSE
├── AGENTS.md                                   # Agent skills 配置块
├── docs/
│   ├── prd/                                    # 产品需求文档,每个产品线 / Skill 一份
│   │   └── integration-test-investigation.md   # 本文档
│   ├── adr/                                    # 架构决策记录(懒创建,消费规则见 docs/agents/domain.md)
│   └── agents/                                 # agent 配置(issue tracker / triage 标签 / 域文档规则)
├── cases/
│   └── investigate-integration-tests/
│       ├── case-template.md                    # case 回填模板(§29)
│       ├── case-*.md                           # 真实调查结案后回填(§29)
│       └── trigger-queries.json                # 触发评估查询集(§29)
└── skills/
    └── investigate-integration-tests/
        ├── SKILL.md                            # 触发描述 + 工作流主干
        └── references/
            ├── failure-data-sources.md         # 失败数据获取(§12.1)
            ├── failure-classification.md       # 失败分类细则(§18)
            └── investigation-report.md         # 报告模板(§20)
```

说明:

- 每个 Skill 独占 `skills/<skill-name>/` 子目录,内部自带 `SKILL.md` 与 `references/`,新增 Skill 不影响既有结构
- 产品文档进 `docs/prd/`,架构决策进 `docs/adr/`,不在仓库根散落
- `cases/` 不随 Skill 安装到 Agent,仅用于人工对照评估与后续迭代的回归基线

---

## 27. Phase 1 Trigger

第一阶段暂不接入 GitLab Webhook。

主要使用方式是人工触发。

例如:

```text
帮我调查 project foo/bar pipeline 18372。
```

或者:

```text
分析一下 MR !873 的 Integration Test Failure。
```

未来可以在保持 Skill 不变的情况下增加:

```text
Pipeline Failed
→ Webhook
→ Agent Invocation
→ Same Skill
```

Webhook 属于后续集成能力,不进入 Phase 1。

---

## 28. Phase 1 Scope Summary

Phase 1 最终交付物:

```text
一个可安装的标准 Agent Skill:
investigate-integration-tests
(SKILL.md + references/ 渐进式结构)
```

它能够指导已有 Coding Agent:

```text
Understand
→ Cluster
→ Investigate
→ Hypothesize
→ Validate
→ Report
```

并能够利用宿主已经提供的:

```text
GitLab
Kubernetes
Code
History
Logs
```

完成远程 Integration Test Investigation。

---

## 29. Success Criteria

第一阶段不建设专门 Benchmark 系统。评估分两层,对真实事故的依赖不同:

### 29.1 触发评估(不依赖真实事故,先行执行)

用人工构造的 trigger 查询集(约 20 条:正例 + near-miss 负例,中英文混合)验证 description 的触发准确率,存于 `cases/investigate-integration-tests/trigger-queries.json`。方法遵循 agentskills.io 的 trigger eval 流程:每条查询在宿主 agent 中多次运行取触发率;进入 description 优化阶段时做 train / validation 分割防过拟合。

### 29.2 输出质量评估(依赖真实环境,前向收集)

不要求预先存在历史 case。每次用 Skill 完成真实调查、根因事后确认后,回填一份 case(模板见 `cases/investigate-integration-tests/case-template.md`);首批 3–5 个 case 来自最初的真实使用,作为后续迭代的回归基线。条件允许时,同一输入补一次未安装 Skill 的对照运行,差异即 Skill 价值的直接证据。

原型完成后通过真实内部 Case 人工测试,重点观察:

- Agent 是否能自主找到正确的 Pipeline / Job / Test Context
- 是否能够有效进行 Failure Clustering
- 是否能够合理使用 GitLab 和 Kubernetes 信息
- 是否能够把 Observation 与 Hypothesis 区分开
- 是否能够主动寻找反证
- Root Cause 判断是否基本可信
- 无法确认时是否愿意输出 UNKNOWN
- Recommended Next Step 是否具有工程可执行性
- Follow-up Question 是否能够基于之前 Investigation 继续深入
- 相比没有安装 Skill 的通用 Agent,调查质量是否明显提升

---

## 30. Future Directions

Phase 1 验证成功后,可根据实际需要逐步扩展:

### Phase 2

- Flaky Test 专用 Skill
- Test Impact Analysis
- MR Test Risk Analysis
- Project Context Cache
- Investigation Report Artifact
- GitLab Comment Integration
- Pipeline Webhook Integration

### Phase 3

- Automated Rerun
- Issue Creation
- Fix Suggestion
- Test Fix
- Code Fix
- Merge Request Creation

### Phase 4

- Multi-Agent Investigation
- Historical Knowledge Base
- Cross-project Investigation
- Autonomous Fix-and-Verify Loop

这些均不影响 Phase 1 核心 Skill 的设计。

---

## 31. 核心产品原则

本项目最终沉淀的核心资产不是一个新的 Agent Runtime,而是:

> 一套可移植、可安装、可持续改进的 Integration Test Investigation Methodology。

它应该能够在不同 Coding Agent、不同 GitLab 项目和不同测试环境中复用,同时充分利用用户已经提供给 Agent 的工具能力。
