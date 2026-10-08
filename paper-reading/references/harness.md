# harness 示例（可选链路）

本 skill 默认由 agent 直接按 `references/` 规则解析，不依赖任何 harness。此处说明一个**可选的自定义 harness 示例**及其定位。

## 何时使用

仅当满足以下**任一**条件时使用 harness：

1. 用户显式提供 API Key，并要求走 harness 解析；
2. 用户显式要求使用自定义 harness。

未满足上述条件时，一律走 agent 直接解析，不得主动引入 harness。

## 定位与现状

- harness（本项目内的 [harness](../harness/) 目录）目前**只是一个示例**，用于演示「用外部 API 分轮解析」的一种实现思路，不是本 skill 的组成部分，也不是默认路径。其脚本与代码均随 skill 存放于 `harness/`，不依赖任何开发临时目录。
- 该示例支持使用者**自定义或在此基础上优化调整**：更换 API、调整管线编排、改写 prompt、替换重试策略等，均可在 harness 自身副本内进行。

## 禁止事项

- **skill 中的示例（`references/` 下的规则文档）禁止被 harness 直接修改或覆盖。** 这些规则是本 skill 的权威目标规则，agent 直接解析时以其为准。
- harness 如需调整解析行为，应在 harness 自身副本内实现，不得反向改写或覆盖本 skill 的 `references/` 内容。