# skills

一组遵循通用 Agent Skills 标准的可安装 Skills,为已有 Coding Agent 增加工程能力。

本项目的核心资产不是新的 Agent Runtime,而是可移植、可安装、可持续改进的工程方法论:

> Teach existing AI agents repeatable engineering workflows without tying them to a specific runtime.

## Skills

| Skill | 说明 |
| --- | --- |
| [investigate-integration-tests](skills/investigate-integration-tests/) | 端到端调查 Integration Test 失败:定位失败、按根因聚类、跨代码 / 运行时 / 历史取证、假设验证,输出带证据引用与置信度的调查报告(UNKNOWN 也是合法结论) |
| [reconcile-json-localization](skills/reconcile-json-localization/) | 以英文 locale JSON 为唯一事实来源,全量对账中文 JSON 的 key、结构、类型、数组、顺序、消息契约和当前语义,直到不存在未解释差异 |

## 安装

Skill 采用标准目录结构：`skills/<name>/SKILL.md` 为入口，按需携带 `references/`、`scripts/` 等资源。将需要的 skill 目录整体复制(或软链)到你所用 Coding Agent 的 skills 目录即可,常见位置如 `~/.agents/skills/`、`~/.zcode/skills/` 等,以你的 Agent 文档为准。

本项目不绑定任何宿主 Agent。Skill 描述能力语义与方法论，并可按需携带无宿主依赖的辅助脚本；具体调用哪个 MCP / CLI / Tool 由宿主根据当前可用能力决定。

## 使用示例

安装后直接用自然语言。Integration Test 调查示例:

```text
帮我调查 project foo/bar 的 pipeline 18372 为什么失败。
看一下 foo/bar 的 MR !873,Integration Test 为什么失败。
pipeline 18372 里面 test_cancel_order 为什么失败?
昨晚这批 Integration Test 大量 timeout,看看是不是测试环境的问题。
```

支持追问(如"为什么你觉得不是这次 MR 导致的?"):Skill 要求 Agent 维护紧凑的 Investigation State,基于已有调查上下文继续深入,而不是每次从头开始。

调查过程只读:Skill 不自动 rerun 测试、不改代码、不动环境,修复建议以具体可执行的 Recommended Next Step 输出。

JSON 本地化对账示例:

```text
对账 locales/en.json 和 locales/zh-CN.json,让中文版和英文版完全一致。
检查中文语言包有没有缺 key、旧翻译或者英文已经删除的字段。
不要依赖 git diff,全量核对中英文 JSON 的结构、placeholder 和语义。
```

## 仓库结构

```text
├── skills/          # 可安装的 Skills(每 skill 一个子目录)
├── cases/           # 评估材料:触发查询集 + 真实使用后回填的 case(不随 Skill 安装)
├── tests/           # Skill 内置脚本的确定性单元测试
└── docs/
    ├── prd/         # 产品需求文档
    ├── adr/         # 架构决策记录
    └── agents/      # agent 配置(issue tracker / triage 标签 / 域文档规则)
```

## 评估

评估分两层，具体方法和成功标准见各 Skill 的 PRD：

- **触发评估**:`cases/<skill-name>/trigger-queries.json` 存放人工构造的触发查询集(正例 + near-miss 负例,中英文混合),不需要真实事故;每条查询在装有 Skill 的宿主 agent 中多次运行,观察 Skill 是否被加载,得到触发率。
- **输出质量评估**:每个 Skill 按自己的 case 模板前向积累真实使用结果;断言聚焦可观察行为和产物,并在条件允许时与未安装 Skill 的运行对照。

## 文档

- Integration Test Investigation PRD:[docs/prd/integration-test-investigation.md](docs/prd/integration-test-investigation.md)
- JSON Localization Reconciliation PRD:[docs/prd/json-localization-reconciliation.md](docs/prd/json-localization-reconciliation.md)
