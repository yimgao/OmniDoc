# 质量改进问题解决方案 (Quality Improvement Solution)

## 问题总结

用户观察到第二次重写文档后，质量分数提升很小（例如：V1: 26.20/100 → V2: 27.70/100，仅提升1.50分）。

## 根本原因

### 1. ❌ DocumentImproverAgent Prompt 不够具体

**问题**：
- 原来的 prompt 只是要求"改进文档"，没有明确告诉模型要关注哪些质量指标
- 没有传递质量分数的详细信息（缺失的章节、字数不足等）
- 模型不知道具体要改进什么，只能做表面改进

**示例**：
- 如果文档缺少"Database Design"章节，模型可能不知道需要添加这个章节
- 如果字数不足，模型可能不知道需要扩展内容
- 如果可读性差，模型可能不知道如何改进

### 2. ❌ 质量信息没有传递给改进 Agent

**问题**：
- QualityChecker 检查出了具体问题（缺失章节、字数不足、可读性差）
- 但这些信息没有传递给 DocumentImproverAgent
- 改进 Agent 只能基于质量反馈（LLM生成的文本）来改进，不知道具体的质量指标

## 解决方案

### 1. ✅ 更新 DocumentImproverAgent Prompt

**改进内容**：
1. **添加质量分数和详细信息**：
   - 传递当前质量分数
   - 传递质量检查的详细信息（字数、章节、可读性）
   - 明确指出缺失的章节
   - 明确指出字数不足
   - 明确指出可读性问题

2. **提供具体的改进策略**：
   - 如果字数不足，明确告诉模型要扩展内容
   - 如果章节缺失，明确告诉模型要添加哪些章节
   - 如果可读性差，明确告诉模型如何改进

3. **强调实质性改进**：
   - 不是小修小补，而是实质性改进
   - 如果章节缺失，要添加完整的章节
   - 如果字数不足，要显著扩展内容

**改进后的 Prompt 结构**：
```
CURRENT QUALITY SCORE: {score}/100

QUALITY METRICS:
- Word Count: {word_count} (min: {min_threshold}, passed: {passed})
- Section Completeness: {completeness_score}% ({found_count}/{required_count} sections found)
  - MISSING SECTIONS: {missing_sections}
- Readability: {readability_score} ({level}, passed: {passed})

CRITICAL IMPROVEMENT PRIORITIES:
1. INCREASE WORD COUNT: Current {word_count} words, need at least {min_threshold} words
   - Expand existing sections with more detail
   - Add examples, explanations, and context
   - Include more comprehensive coverage of topics

2. ADD MISSING SECTIONS: Only {found_count}/{required_count} sections found
   - MUST ADD: {missing_sections}
   - Ensure all required sections are present with substantial content

3. IMPROVE READABILITY: Current score {readability_score}, need at least {min_threshold}
   - Use simpler sentence structures
   - Break up long paragraphs
   - Use clearer, more direct language
   - Add more examples and explanations

IMPORTANT: This is a COMPLETE REWRITE focused on quality improvement. 
Do not just make minor edits - make substantial improvements to address all quality issues.
```

### 2. ✅ 更新 Coordinator 传递质量信息

**改进内容**：
1. **在质量循环中传递质量信息**：
   - 将质量分数传递给改进 Agent
   - 将质量检查的详细信息传递给改进 Agent
   - 包括字数、章节、可读性等详细信息

2. **同步和异步版本都更新**：
   - 同步版本：`_run_agent_with_quality_loop`
   - 异步版本：`_async_run_agent_with_quality_loop`

**改进后的代码**：
```python
# 传递质量分数和详细信息
improved_doc = self.document_improver.improve_document(
    original_document=v1_content,
    document_type=agent_type.value,
    quality_feedback=feedback_report,
    quality_score=score,  # 传递质量分数
    quality_details={  # 传递质量详细信息
        "word_count": quality_result_v1.get("word_count", {}),
        "sections": quality_result_v1.get("sections", {}),
        "readability": quality_result_v1.get("readability", {})
    }
)
```

## 实施详情

### 1. ✅ DocumentImproverAgent 更新

**文件**：`src/agents/document_improver_agent.py`

**更改**：
- 添加 `quality_score` 和 `quality_details` 参数
- 更新 `improve_document()` 方法
- 在 prompt 中包含质量指标信息
- 提供具体的改进策略

### 2. ✅ Coordinator 更新

**文件**：`src/coordination/coordinator.py`

**更改**：
- 在 `_run_agent_with_quality_loop()` 中传递质量信息
- 在 `_async_run_agent_with_quality_loop()` 中传递质量信息
- 初始化 `quality_result_v1` 变量确保作用域正确

## 预期效果

### 改进前
- V1: 26.20/100
- V2: 27.70/100
- 提升: +1.50
- **问题**：改进不明显，模型不知道具体要改进什么

### 改进后（预期）
- V1: 26.20/100
- V2: 45-60/100 (预期)
- 提升: +20-35
- **原因**：
  1. 模型知道要添加哪些缺失的章节
  2. 模型知道要扩展多少字数
  3. 模型知道如何改进可读性
  4. 模型知道这是实质性改进，不是小修小补

### 具体改进示例

**Technical Documentation**：
- **改进前**：可能缺少"Database Design"章节，但模型不知道
- **改进后**：模型明确知道要添加"Database Design"章节，并生成完整内容

**Database Schema**：
- **改进前**：可能缺少"Schema/Table description"，但模型不知道
- **改进后**：模型明确知道要添加"Schema/Table description"章节

**Project Charter**：
- **改进前**：可能缺少"Executive Summary"，但模型不知道
- **改进后**：模型明确知道要添加"Executive Summary"章节

## 测试建议

### 1. 运行完整工作流
```bash
# 运行完整工作流生成文档
uv run python -m src.web.app
# 或
python -c "
from src.coordination.coordinator import WorkflowCoordinator
from src.context.context_manager import ContextManager

context_manager = ContextManager()
coordinator = WorkflowCoordinator(context_manager=context_manager)

results = coordinator.generate_all_docs(
    user_idea='Build a simple task management app',
    profile='team'
)

# 检查质量分数提升
print(f'Quality scores: {results.get(\"quality_scores\", {})}')
"
```

### 2. 检查改进效果
- 检查 V1 和 V2 的质量分数
- 检查 V2 是否添加了缺失的章节
- 检查 V2 是否扩展了内容
- 检查 V2 是否改进了可读性

### 3. 验证质量指标
- 检查字数是否增加
- 检查章节是否完整
- 检查可读性是否改善

## 如果改进仍然不够

### 1. 多次改进循环
- 考虑增加多次改进循环（V1 → V2 → V3）
- 每次改进都基于前一次的质量检查结果

### 2. 使用更强的模型
- 考虑使用 `gemini-2.5-pro` 而不是 `gemini-2.0-flash`
- 更强的模型可能有更好的改进能力

### 3. 优化质量检查器
- 考虑优化质量检查器的评分标准
- 考虑添加更多质量指标（内容深度、技术准确性等）

### 4. 优化改进 Prompt
- 根据测试结果进一步优化改进 prompt
- 添加更多具体的改进指导

## 总结

**问题根源**：
- DocumentImproverAgent 的 prompt 不够具体
- 质量信息没有传递给改进 Agent

**解决方案**：
- 更新 prompt 以包含质量指标信息
- 传递质量分数和详细信息给改进 Agent
- 提供具体的改进策略

**预期效果**：
- 质量分数提升从 +1-2 分提升到 +20-35 分
- 改进后的文档更符合质量检查器的标准
- 文档质量显著提升

---

**实施日期**：2024年
**状态**：✅ 已实施
**下一步**：测试和改进效果验证

