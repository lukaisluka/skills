# skills

一组遵循通用 Agent Skills 标准的可安装 Skills,为已有 Coding Agent 增加工程能力。

本项目的核心资产不是新的 Agent Runtime,而是可移植、可安装、可持续改进的方法论:

> Teach existing AI agents how to investigate integration testing problems effectively.

## Skills

| Skill | 说明 |
| --- | --- |
| [investigate-integration-tests](skills/investigate-integration-tests/) | 端到端调查 Integration Test 失败:定位失败、按根因聚类、跨代码 / 运行时 / 历史取证、假设验证,输出带证据引用与置信度的调查报告(UNKNOWN 也是合法结论) |

## 安装

Skill 采用标准目录结构(`skills/<name>/SKILL.md` + 按需加载的 `references/`)。将需要的 skill 目录整体复制(或软链)到你所用 Coding Agent 的 skills 目录即可,常见位置如 `~/.agents/skills/`、`~/.zcode/skills/` 等,以你的 Agent 文档为准。

本项目不绑定任何宿主 Agent,也不实现 GitLab、Kubernetes 等访问能力——Skill 只描述能力语义与方法论,具体调用哪个 MCP / CLI / Tool 由宿主根据当前可用能力决定。

## 使用示例

安装后直接用自然语言:

```text
帮我调查 project foo/bar 的 pipeline 18372 为什么失败。
看一下 foo/bar 的 MR !873,Integration Test 为什么失败。
pipeline 18372 里面 test_cancel_order 为什么失败?
昨晚这批 Integration Test 大量 timeout,看看是不是测试环境的问题。
```

支持追问(如"为什么你觉得不是这次 MR 导致的?"):Skill 要求 Agent 维护紧凑的 Investigation State,基于已有调查上下文继续深入,而不是每次从头开始。

调查过程只读:Skill 不自动 rerun 测试、不改代码、不动环境,修复建议以具体可执行的 Recommended Next Step 输出。

## 仓库结构

```text
├── skills/          # 可安装的 Skills(每 skill 一个子目录)
├── cases/           # 评估材料:触发评估查询集 + 真实调查结案后回填的 case(不随 Skill 安装)
└── docs/
    ├── prd/         # 产品需求文档
    ├── adr/         # 架构决策记录
    └── agents/      # agent 配置(issue tracker / triage 标签 / 域文档规则)
```

## 评估

评估分两层(详见 PRD §29):

- **触发评估**:`cases/<skill-name>/trigger-queries.json` 存放人工构造的触发查询集(正例 + near-miss 负例,中英文混合),不需要真实事故;每条查询在装有 Skill 的宿主 agent 中多次运行,观察 Skill 是否被加载,得到触发率。
- **输出质量评估**:真实调查结案、根因确认后,按 [case 模板](cases/investigate-integration-tests/case-template.md) 回填 case(结案时证据还在,回填成本最低),逐步积累为后续迭代的回归基线。

## 文档

- 产品 PRD:[docs/prd/integration-test-investigation.md](docs/prd/integration-test-investigation.md)
