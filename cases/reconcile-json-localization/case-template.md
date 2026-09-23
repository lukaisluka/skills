# JSON localization reconciliation case template

复制本文件为 `case-<序号>-<短名>.md` 后填写，用于**真实使用后回填**的评估 case。合成的确定性回归 seed case（如 `case-001`）不套用本模板，采用 prompt + fixtures + 断言的简化结构。Case 记录真实的英文/中文 locale JSON 对账现场；源文件较大时可以保存最小但完整复现问题的 fixture，并链接原始版本。

## 元信息

- 记录日期：
- 项目：
- 英文源文件：
- 中文目标文件：
- 中文变体：
- 最终状态：`RECONCILED / PARTIAL / BLOCKED`
- 确认人：

## 当时的用户输入

原样记录用户请求、提供的文件路径和范围限制。

## 输入快照

- 英文 JSON revision / digest：
- 中文 JSON revision / digest：
- 项目使用的 message format：
- 本次运行确认的术语或英文例外：
- 英文 source 自动发现的候选及分类依据：
- 相关 formatter / validator / tests：

保留能复现以下问题的原始片段：缺失 key、多余 key、类型或数组差异、placeholder 差异、旧译文、未翻译值和歧义值。

## 预期 reconciliation

断言必须具体、可验证：

- 应新增的 JSON Pointer paths：
- 应更新的 paths 与正确语义：
- 应删除的 paths：
- 应重排或重建的 paths：
- 必须保持的 placeholders / markup：
- 应保留不动的既有正确译文：
- 应识别的全英文 / 部分英文残留：
- 初始 `PUNCTUATION_ELIGIBLE` paths（仅 missing / 全英文 value）：
- 这些 paths 按中文含义应采用的标点和断句：
- 必须避免标点 churn 的既有中文 paths：
- 允许保留英文的 path + exact span/value、reason code 与证据：
- 应报告而不能猜测的歧义：

## 验收

- [ ] 两个文件均为无重复 key 的合法 JSON
- [ ] key、嵌套、类型、数组和顺序一致
- [ ] 非字符串 scalar 一致
- [ ] placeholder 与受保护 token 一致
- [ ] 所有字符串已完成语义检查
- [ ] translation coverage 为 100%，unresolved 为 0
- [ ] 无过期中文内容
- [ ] 相同英文、不同英文和部分英文残留均已处理
- [ ] 所有保留英文均有 reason code
- [ ] 英文例外由 Skill 自动发现，未要求用户提供术语表或参数
- [ ] 最终检查确认应保留英文未被翻译、改写、删除或增加
- [ ] 最终检查确认其余英文自然语言均已翻译
- [ ] 新增和初始全英文 value 的标点按中文语义决定，而非机械替换
- [ ] 既有中文译文没有发生无独立理由的 punctuation-only 修改
- [ ] bundled auditor 退出码为 0；若为 3，每个 review path 均已按决策账本分类（保留英文含 reason code），exit 1 或 2 均不通过
- [ ] 项目自带 validator / tests 通过，或明确记录不可用

## 实际结果与差异

记录 Skill 的实际修改、未解决项、验证证据，以及无 Skill 对照运行最容易遗漏的内容。
不要在最终用户报告中枚举或统计未修改的 path；case 可以保留必要 fixture
用于评估，但应与用户侧精简报告区分。
