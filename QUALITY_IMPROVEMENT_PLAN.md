# 质量改进计划 (Quality Improvement Plan)

## 问题分析 (Problem Analysis)

### 核心问题

质量报告显示总体质量分数为 **54.8/100**，主要问题如下：

1. **依赖关系缺陷**：工作流编排导致Agent之间缺乏正确的信息传递
2. **缺失章节**：多个文档缺少关键章节（如 `technical_documentation` 缺少 "System Architecture" 和 "Database Design"）
3. **可读性差**：许多文档可读性评分很低（"Very Difficult" 或 "Difficult"）
4. **状态管理问题**：Web App 使用内存中的 `project_status` 字典，不够健壮

### 根本原因

#### 1. 工作流依赖关系问题

**当前问题**：
- `technical_documentation` 在 Phase 1 生成，但它需要包含 "Database Design"
- `database_schema` 在 Phase 2 生成，依赖 `technical_documentation`
- 但是 `technical_documentation` 在生成时不知道 `database_schema` 的详细内容
- 结果：`technical_documentation` 缺少详细的数据库设计部分

**当前工作流**：
```
Phase 1 (顺序执行):
  - requirements_analyst
  - project_charter (team only)
  - user_stories
  - technical_documentation  ← 需要包含数据库设计，但不知道详细SQL

Phase 2 (并行执行, DAG):
  - database_schema  ← 依赖 technical_documentation，但technical_doc已经生成了
  - api_documentation
  - setup_guide
  - ...
```

**问题根源**：
- `technical_documentation` 的提示词要求包含 "Database Design"（第135-140行），但它无法看到 `database_schema` 的详细SQL
- `database_schema` 依赖 `technical_documentation`，但两者在时间上是分离的
- 这导致了信息传递的断层

#### 2. 状态管理问题

**当前问题**：
- `src/web/app.py` 注释说状态已经转移到 ContextManager (SQLite)
- 但实际上可能还在使用内存字典（需要检查）

#### 3. 可读性问题

**当前问题**：
- 许多文档的句子过长、过于复杂
- 缺乏清晰的标题和子标题
- 未充分利用项目符号和编号列表
- 语言过于技术化和密集

## 解决方案 (Solutions)

### 方案1：修复工作流依赖关系（最高优先级）

#### 选项A：将 database_schema 移到 Phase 1（推荐）

**修改方案**：
1. 将 `database_schema` 移到 Phase 1，与 `technical_documentation` 并行生成
2. 两者都依赖 `user_stories`
3. `technical_documentation` 包含数据库设计概览（高级设计、架构决策）
4. `database_schema` 包含详细的SQL实现（CREATE TABLE语句、索引等）
5. Phase 2 的其他任务可以依赖这两个文档

**新的工作流**：
```
Phase 1 (部分并行):
  - requirements_analyst
  - project_charter (team only)
  - user_stories
  - technical_documentation  ← 包含数据库设计概览
  - database_schema          ← 并行生成，包含详细SQL

Phase 2 (并行执行, DAG):
  - api_documentation        ← 依赖 technical_documentation 和 database_schema
  - setup_guide              ← 依赖 api_documentation 和 technical_documentation
  - dev_doc                  ← 依赖 api_documentation 和 technical_documentation
  - ...
```

**实施步骤**：
1. 修改 `coordinator.py` 的 Phase 1 逻辑，将 `database_schema` 移到 Phase 1
2. 使用 `AsyncParallelExecutor` 让 `technical_documentation` 和 `database_schema` 并行生成
3. 修改 `workflow_dag.py`，将 `database_schema` 从 Phase 2 移到 Phase 1
4. 更新 `technical_documentation` 的提示词，明确它应该包含数据库设计概览，但不包含详细SQL
5. 更新 `database_schema` 的提示词，明确它应该基于 `technical_documentation` 的数据库设计概览生成详细SQL

#### 选项B：两阶段生成 technical_documentation

**修改方案**：
1. Phase 1：生成 `technical_documentation` 基础版本（不包含详细数据库设计）
2. Phase 2：生成 `database_schema`
3. Phase 2 后：更新 `technical_documentation`，添加数据库设计章节

**缺点**：
- 需要两阶段生成，复杂度高
- 需要文档更新机制

**不推荐此方案**

### 方案2：修复 Web App 状态管理（高优先级）

**修改方案**：
1. 确认 `app.py` 已经完全使用 `ContextManager` (SQLite)
2. 移除任何内存中的 `project_status` 字典
3. 所有状态操作都通过 `ContextManager` 进行

**实施步骤**：
1. 检查 `app.py` 是否还有内存字典
2. 确保所有状态读写都通过 `context_manager`
3. 添加状态持久化测试

### 方案3：改进提示词以提升可读性（中优先级）

**修改方案**：
1. 在所有提示词中添加可读性要求：
   - 使用短句（平均15-20个词）
   - 使用清晰的标题和子标题
   - 使用项目符号和编号列表
   - 避免过于技术化的语言（对于非技术文档）
2. 添加可读性检查到质量检查器

**实施步骤**：
1. 更新 `system_prompts.py` 中的提示词
2. 添加可读性评分到 `QualityChecker`
3. 在质量循环中检查可读性分数

### 方案4：改进 Phase 2 依赖关系（中优先级）

**修改方案**：
1. 确保 Phase 2 的依赖关系正确定义
2. 确保 `api_documentation` 可以访问 `database_schema` 的内容
3. 确保 `setup_guide` 可以访问 `api_documentation` 和 `database_schema`

**当前问题**：
- `api_documentation` 依赖 `technical_documentation`，但可能也需要 `database_schema`
- `setup_guide` 依赖 `api_documentation` 和 `technical_documentation`，但可能也需要 `database_schema`

**实施步骤**：
1. 更新 `workflow_dag.py` 中的依赖关系
2. 更新 `build_kwargs_for_task` 函数，确保传递正确的依赖内容
3. 测试依赖关系是否正确工作

## 实施优先级

### 最高优先级（立即执行）
1. ✅ **修复工作流依赖关系**：将 `database_schema` 移到 Phase 1
2. ✅ **修复 Web App 状态管理**：确保完全使用 ContextManager

### 高优先级（本周执行）
3. ✅ **改进 Phase 2 依赖关系**：确保所有依赖正确传递
4. ✅ **改进提示词**：添加可读性要求和数据库设计概览要求

### 中优先级（下周执行）
5. ✅ **添加可读性检查**：在质量检查器中添加可读性评分
6. ✅ **优化质量循环**：改进质量检查和改进流程

## 实施计划

### 阶段1：修复核心依赖关系（1-2天）

1. **修改 coordinator.py**
   - 将 `database_schema` 从 Phase 2 移到 Phase 1
   - 使用 `AsyncParallelExecutor` 让 `technical_documentation` 和 `database_schema` 并行生成
   - 确保两者都依赖 `user_stories`

2. **修改 workflow_dag.py**
   - 将 `database_schema` 从 `PHASE2_TASKS_CONFIG` 移除
   - 在 Phase 1 中添加 `database_schema` 任务
   - 更新 Phase 2 任务的依赖关系，让它们可以依赖 `database_schema`

3. **更新提示词**
   - 更新 `technical_documentation` 提示词：明确包含数据库设计概览，但不包含详细SQL
   - 更新 `database_schema` 提示词：明确基于 `technical_documentation` 生成详细SQL

### 阶段2：修复状态管理（1天）

1. **检查 app.py**
   - 确认是否还有内存字典
   - 确保所有状态操作都通过 `context_manager`

2. **测试状态持久化**
   - 添加测试确保状态正确保存和恢复
   - 测试多用户场景

### 阶段3：改进可读性（2-3天）

1. **更新提示词**
   - 添加可读性要求到所有提示词
   - 添加示例和要求

2. **添加可读性检查**
   - 在 `QualityChecker` 中添加可读性评分
   - 在质量循环中检查可读性分数

### 阶段4：测试和验证（1-2天）

1. **端到端测试**
   - 测试完整工作流
   - 验证依赖关系正确
   - 验证文档质量提升

2. **质量报告验证**
   - 重新运行质量检查
   - 验证分数提升到 70+ /100

## 预期结果

### 质量分数提升
- **当前**：54.8/100
- **目标**：70+/100（第一阶段）
- **最终目标**：80+/100

### 具体改进
1. ✅ `technical_documentation` 包含完整的 "System Architecture" 和 "Database Design" 章节
2. ✅ `database_schema` 包含详细的SQL实现，基于 `technical_documentation` 的设计
3. ✅ 所有文档的可读性提升（从 "Very Difficult" 到 "Fairly Difficult" 或更好）
4. ✅ 状态管理完全基于 ContextManager，支持多用户和持久化
5. ✅ 依赖关系正确，信息传递完整

## 风险评估

### 风险1：破坏现有功能
- **风险**：修改工作流可能破坏现有功能
- **缓解**：充分测试，保留旧代码作为备份

### 风险2：性能影响
- **风险**：并行生成可能增加资源使用
- **缓解**：使用 `AsyncParallelExecutor` 控制并发数

### 风险3：依赖关系复杂
- **风险**：修改依赖关系可能导致循环依赖
- **缓解**：仔细设计依赖关系，使用DAG确保无环

## 下一步行动

1. ✅ 立即开始实施阶段1：修复核心依赖关系
2. ✅ 同时检查状态管理问题
3. ✅ 在实施过程中持续测试
4. ✅ 完成后运行质量检查，验证改进

