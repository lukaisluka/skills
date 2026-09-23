# JSON Localization Reconciliation Skill — PRD

## 1. 产品目标

提供一个可安装、与宿主 Agent 无关的 Skill，以英文 locale JSON 为唯一事实来源，对中文 locale JSON 执行完整 reconciliation。

每次执行都比较两份文件的当前完整状态，而不是依赖 Git diff 或“上次同步版本”。完成条件是中文文件在以下维度与英文文件完全对齐：

- key 集合与 object 嵌套；
- value type；
- array 长度、顺序和元素结构；
- object key 顺序；
- placeholder、message syntax、markup 与 protected tokens；
- 每个字符串叶子的翻译覆盖状态；
- 当前语义。

中文字符串不要求逐字等于英文，而要求自然、准确地表达当前英文含义，并保持相同运行时契约。

## 2. 非目标

第一版不包含：

- 应用 i18n framework 接入；
- locale detection、selector 或 fallback 设计；
- JSONC、YAML、PO、ARB、XLIFF 或 JavaScript locale modules；
- 与英文 source 无配对关系的一次性翻译；
- 自动修改英文 source；
- 自动接受机器翻译结果；
- 翻译平台、供应商或人工审校工作流；
- 依赖特定 Agent、MCP、插件或代码托管平台。
- 创建或依赖项目内的 policy、glossary、manifest、cache 或 sidecar 配置。

## 3. Source of Truth

英文 JSON 是唯一事实来源：

- 中文缺少英文 key → 新增并翻译；
- 中文存在英文没有的 key → 删除，除非项目存在明确例外；
- 类型、数组和嵌套不同 → 按英文重建；
- 非字符串 scalar 不同 → 复制英文值；
- 中文含义落后或错误 → 更新；
- 中文已准确表达当前英文 → 保持不动。

Reconciliation 不需要历史 baseline。Git diff 可以辅助 review，但不能限制检查范围。

## 4. 工作流

```text
Resolve Files
    ↓
Scan English Source
    ↓
Discover Non-Translatable Content
    ↓
Audit Current Structure
    ↓
Reconcile JSON Shape
    ↓
Reconcile Message Contracts
    ↓
Reconcile Meaning
    ↓
Validate Again
    ↓
Report
```

机械检查与语义判断明确分层：

- bundled script 负责可确定的 JSON 事实；
- Agent 负责译文是否准确、是否过期、术语是否一致；
- 项目自己的 message compiler / tests 负责格式专用运行时契约。

任何一层失败都不能声明 `RECONCILED`。

### Source-First Non-Translation Discovery

每次运行必须先完整扫描英文 source，而不是等中文残留英文后再被动判断。Agent 自动建立仅存在于本次上下文中的 decision ledger，记录 exact term / path、reason code、出现位置和判断依据；不得要求用户提供术语表，也不得把 ledger 写入项目。

自动判断覆盖：品牌和官方名称、包和框架、语言和标准、协议、命令、标识符、外部精确字面量，以及中文专业用户通常直接使用英文、翻译后更生硬或更歧义的行业术语。大写、首字母大写或“看起来技术化”只能成为候选，不能直接成为保留依据。普通英文句子和有自然中文表达的通用概念仍须翻译。

脚本输出紧凑的 `sourceEnglishCandidates` 候选队列；Agent 必须逐项语义分类，并额外检查正则无法发现的 lowercase 行业术语。每个决定以 JSON Pointer path + exact span/value + reason 记录在本次上下文中，不通过 CLI 参数传递，不写入项目，也不要求用户提供。

### Translation Coverage Gate

key 存在不代表 value 已翻译。脚本必须枚举英文 source 的全部字符串叶子，在剔除 placeholder、URL、命令及本次运行明确允许的内容后，阻断以下情况：

- source 与 target 相同且仍包含英文自然语言；
- target 虽与 source 不同，但仍为全英文；
- target 已包含中文，但仍残留未保护英文；
- target 出现无法解释的其他语言文字。

每个 source string 必须且只能落入以下状态之一：valid Chinese、intentionally English with reason、non-linguistic 或 unresolved。只有 coverage 为 100%、unresolved 为 0 才能完成 reconciliation；不得抽样。

### Final English-Preservation Audit

翻译完成后必须针对 source-first decision ledger 进行独立复核，且是双向门禁：

- 未被分类为应保留的英文不得残留；
- 已分类为应保留的 term 必须在对应 path 保持相同拼写和出现次数；
- 已分类为整体保留的 value 必须与英文 source 完全相等；
- 所有 ledger decision 必须仍能指向当前英文 source 的对应 path 和内容，不允许 stale decision。

这一步同时防止漏译和过度翻译，失败时不得声明 `RECONCILED`。

### Scoped Chinese Punctuation Naturalization

中文标点不能由英文标点逐字符映射。英文以句号分开的短句，在中文语义中可能更适合用逗号、分号或其他连接方式。该判断必须基于完整中文含义。

但此规则只适用于本次运行开始时的两类 path：

- 中文 target 中缺失、需要新增的 key；
- key 已存在但初始 value 为空，或在扣除合法保留英文后仍被判定为 `untranslated_identical` / `english_only_target`。

Agent 必须在修改前把这些 path 记录为内存中的 `PUNCTUATION_ELIGIBLE` 集合。合法整体保留英文、无语言含义的 value、已有中文的 value 不进入该集合；中英混合的部分翻译也不自动进入。不得创建 baseline 或辅助文件。

最终 diff 必须检查标点修改范围。对既有中文译文，不得以“中文标点更自然”为理由做 punctuation-only churn；只有独立的语义修正、运行时契约修复或用户明确要求才能改变其标点。

## 5. Skill 内容结构

```text
skills/reconcile-json-localization/
├── SKILL.md
├── references/
│   ├── json-reconciliation.md
│   ├── message-contracts.md
│   ├── non-translatable-content.md
│   └── translation-judgment.md
└── scripts/
    └── audit_json_parity.py
```

内容全部使用英文，以保持跨宿主可移植性。用户交互和最终报告跟随会话语言。

`SKILL.md` 包含所有执行都需要的流程、硬规则、脚本入口和完成门。References 只在结构差异、消息契约或语义判断发生时加载。

## 6. 审计脚本

`scripts/audit_json_parity.py` 是无第三方依赖、只读、非交互脚本。

输入：

```text
English source JSON
Chinese target JSON
```

输出支持人类可读文本和 JSON。退出码：

- `0`：机械对账通过，且没有待语义判断的英文；
- `1`：存在 reconciliation differences；
- `2`：输入不可可靠审计，例如无效 JSON、重复 key、文件不可读或顶层不是 object；
- `3`：机械对账通过，但仍有英文 span 需要 Agent 做语义分类。

第一版检查：

- JSON 解析和重复 key；
- missing / extra key；
- object key order；
- value type；
- array length 与逐元素结构；
- 非字符串 scalar value；
- 空翻译；
- 常见 placeholder 的 source-target 精确对比，以及 URL、path、inline code、email、CLI flag、version、Markdown destination 的精确一致性；
- HTML tag 顺序、自闭合形态与全部非翻译属性的 name=value 对比；
- ICU 消息结构对比：参数名、selector 类型（plural/select/selectordinal）、自定义选项集合、`other` fallback 存在性与 plural `#` 占位存在性；CLDR 分支类别（one/two/few/…）允许 locale 合法差异；
- 换行和 tab；
- source 与 target 相同且仍含英文自然语言；
- 与 source 不同但仍为全英文的 target；
- 中英文混合 value 中未保护的英文残留；
- source-side 英文候选的紧凑汇总；
- target-side 待语义复核英文的 path 与 fragments；相同 kind 且相同 detail 的 findings 聚合为单条多 path 输出，控制大文件的上下文占用；
- 每个 source string 的 coverage 分类和汇总。

合法英文例外由 Agent 自动判断并按 path 保存在本次上下文中。审计脚本不接受 term/path 例外参数，不读取或创建项目 policy 文件，也不使用全局词表放行同形词。最终双向门禁由 Agent 使用 path-scoped ledger 对照当前 source/target 完成。

脚本不自动修改文件，不判断翻译语义，也不假装完整解析所有 ICU 方言。项目存在专用 parser / compiler 时必须额外执行，但 Skill 本身不要求项目配置或第三方依赖。

## 7. 完成条件

状态分为：

- `RECONCILED`：机械检查无错误；translation coverage 为 100%；每个字符串完成语义检查；保留英文均有 reason code；项目专用检查通过或确认不存在。
- `PARTIAL`：已完成可确认修改，但仍有明确未决项或不可用验证。
- `BLOCKED`：输入无效、source 含义关键歧义或必要运行时契约无法确认。

禁止把 `audit_json_parity.py` 退出码 0 单独解释为翻译已完成。

## 7.1 大文件报告约束

完整扫描、语义检查、英文保留判断和未修改项验证属于内部流程，但用户侧报告不得枚举或统计未发生修改的 path。不得输出完整 candidate queue、decision ledger、已有正确译文清单或未变化的 preserved English 清单。

最终报告只包含：实际新增、更新、删除、重排或重建的 path；阻塞和未解决项；紧凑的验证结果。如果没有修改，只需说明没有实际变更，不得展开未变内容。

## 8. 评估

触发评估位于 `cases/reconcile-json-localization/trigger-queries.json`，包括 10 个正例和 10 个 near-miss 负例。重点区分：

- locale JSON 完整对账；
- 普通单句翻译；
- 应用 i18n 工程；
- 任意 JSON diff；
- 仅语法验证；
- Markdown 文档翻译。

输出质量 case 分两类：**合成 seed case**（确定性回归基线，prompt + fixtures + 断言的简化结构，如 `case-001`）与**真实回填 case**（真实 reconciliation 结案后按 `case-template.md` 完整记录）。第一批 seed case 应覆盖：

1. missing / extra key 与顺序差异；
2. nested type 和 array shape；
3. placeholder / ICU contract；
4. key 完全一致但中文语义过期；
5. 合法保留英文的产品名与真正漏译并存；
6. source 与 target 不同但 target 仍为全英文；
7. 中英文混合 value 中只翻译了一部分；
8. HTML 自然语言 attribute 遗漏翻译；
9. 无法从 source 可靠决定的歧义。
10. 中文技术语境中保留英文更自然的行业术语与应翻译的普通技术词并存。
11. 新增/全英文 value 需要按中文语义调整标点，同时既有中文译文不得发生标点清理。

每个 case 同时验证“应修改什么”和“哪些正确译文必须保持不动”，避免 Skill 退化成全文件重译器。

## 9. 第一版成功标准

- Agent 正确识别英文 source 与中文 target；
- 不修改英文文件；
- 不依赖 Git diff 限制审计范围；
- 修复所有结构、类型、数组和 scalar 差异；
- 不丢失 placeholder 或 protected token；
- 能发现相同英文、不同英文以及中英混合三类漏译；
- 每个保留英文片段都有可审计 reason code；
- 自动完成英文 source 的 non-translation discovery，不要求用户传参或维护配置；
- 最终 English-preservation audit 同时检查漏译与过度翻译；
- 中文标点自然化只作用于新增和初始全英文 value，不造成既有译文 churn；
- coverage 汇总等于英文 source 的全部字符串叶子；
- 能发现 key 相等但含义过期的中文；
- 保留仍然正确的既有译文；
- 删除无明确例外的 target-only 内容；
- 对歧义和无法验证的 message syntax 明确阻塞；
- 完成后给出可复查的 validator 与测试证据。
