# Case 模板

复制本文件为 `case-<序号>-<短名>.md` 后填写。

Case 的用途是给 Skill 评估提供真实输入与"标准答案"。调查刚结案、证据还在时回填成本最低;现场信息部分尽量保留当时的原貌(原始失败列表、带时间戳的日志摘录),不要事后补写推理,推理属于"实际根因"部分。

## 元信息

- 记录日期:
- 项目 / Pipeline / MR / Commit:
- 状态:已破案
- 最终根因(一句话):
- 最终分类(事后确认):<Application Regression / Test Defect / Flaky Test / Environment or Infrastructure Issue / Dependency Failure / Test Data or State Issue / Configuration or Version Mismatch>
- 破案人 / 最终确认手段:

## 当时的用户输入

(原样保留 anchor 现场:用户当时对 Agent 说了什么、提供了哪些线索)

## 现场证据快照

- Pipeline / Job 概况:(哪些 job 失败;job 级失败还是 test 级失败)
- 失败测试原始状态:(聚类前的失败列表或摘要:数量、suite 分布、错误信息签名)
- 关键日志 / 事件摘录:(带时间戳;注明来源与所属时钟——CI runner / 集中日志 / kubectl)
- 运行时状态:(pod 状态、restart、events、部署记录,如相关)
- 历史信号:(同 commit 其他 pipeline / retry 的结果,如当时已知)

## 实际根因与确认过程

(事后:真正的根因是什么;靠什么证据或操作最终确认;中途走过什么弯路)

## 对 Skill 的期望输出

断言要具体可判定(✓ "分出 ≥2 个 cluster 且各给出反证项";✗ "报告质量好"):

- 期望聚类:
- 期望分类与 confidence:
- 期望 recommended next step:
- 其他可判定断言:
- 陷阱:(一个没有方法论的通用 agent 在这个 case 上最可能犯什么错、得出什么错误结论——这是 case 最有评估价值的部分)

## 对照运行(可选)

(条件允许时,同一输入在未安装 Skill 的 agent 上跑一遍,记录差异:聚类、证据引用、是否过早下结论——这是 Skill 价值的最直接证据)
