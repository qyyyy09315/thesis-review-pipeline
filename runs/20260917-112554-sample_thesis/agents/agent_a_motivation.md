# Agent A：动机与文献边界审查

填写同名 `agent_a_motivation.json`。只审第一章（绪论）与相关工作，禁止改论文。

## 必查

1. 工程背景与核心科学/算法问题是否分开陈述？
2. 是否指出近 2–3 年方法的**具体**痛点，而不是“仍有不足”？
3. 相关工作是批判性对比，还是文献罗列？
4. 本文工作与既有工作的边界是否可检验？

## JSON 合同

```json
{
  "status": "done",
  "agent": "A",
  "findings": [
    {
      "severity": "major",
      "location": "第一章第二节 / 原文摘引",
      "problem": "",
      "basis": "",
      "action": ""
    }
  ]
}
```

每条 finding 必须带原文摘引。找不到证据就不要写。
