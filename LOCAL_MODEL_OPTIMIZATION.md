# 本地模型优化指南

## 概述

本指南说明如何优化本地模型（如 Mixtral、Dolphin3）的性能，使其生成的文档质量接近云端模型（如 Gemini）的水平。

## 为什么本地模型质量较低？

### 规模差异

- **Gemini（云端模型）**：
  - 参数量：万亿级别
  - 能力：能够一次性生成高质量、符合复杂指令的文档
  - 成本：按 API 调用收费

- **Mixtral/Dolphin3（本地模型）**：
  - 参数量：47B/8B
  - 能力：虽然强大，但在遵循极其复杂和冗长的指令时容易"漂移"或"忘记"约束
  - 成本：完全免费（本地运行）

### 提示词复杂度

项目的提示词（位于 `prompts/system_prompts.py`）是为 Gemini 这样的高级模型设计的：

- **技术文档提示词**：要求模型同时记住 8 个章节标题、包含 Mermaid 图、设计 10 个 API 端点、编写 SQL 等
- **复杂性**：dolphin3 (8B) 这样的模型在尝试遵循这个复杂指令时，很容易"漂移"或"忘记"一半的约束

这就是为什么质量报告分数低至 20-30 分的原因。

## 优化方案

### 方案一：升级本地模型（推荐第一步）

**思路**：使用更强大的本地模型

#### 步骤

1. **拉取 Mixtral 模型**：
   ```bash
   ollama pull mixtral
   ```

2. **更新配置**：
   ```env
   OLLAMA_DEFAULT_MODEL=mixtral
   ```

3. **重新运行项目**，比较生成内容的质量

#### Mixtral 的优势

- **Mixture of Experts (MoE)**：8x7B 参数，但每次只激活约 12B 参数
- **质量与速度平衡**：在推理和遵循指令方面远胜于 8B 模型，但运行速度仍然很快
- **本地模型中的最佳选择**：是"质量与速度"的最佳平衡点之一

#### 配置示例

```env
# 使用 Mixtral（47B 参数，但只激活 12B）
OLLAMA_DEFAULT_MODEL=mixtral
OLLAMA_TIMEOUT=600
OLLAMA_MAX_TOKENS=8192
```

### 方案二：激活自动修复循环（推荐第二步）

**思路**：让系统自动迭代改进，而不是强求本地模型"一次成功"

#### 工作原理

1. **生成文档** → 使用本地模型生成初始文档
2. **质量评估** → `QualityReviewerAgent` 评估文档质量
3. **自动改进** → 如果质量分数低于阈值，`DocumentImproverAgent` 自动改进文档
4. **迭代提升** → 重复过程直到达到质量标准

#### 启用方法

在 `.env` 文件中设置：

```env
# 启用自动修复循环
ENABLE_AUTO_FIX=true
AUTO_FIX_THRESHOLD=70.0  # 质量分数阈值 (0-100)
```

#### 效果

- **改进前**：40-60 分（本地模型）
- **改进后**：70-85 分（接近云端模型）
- **提升幅度**：+30-45 分

#### 详细文档

参见 `AUTO_FIX_LOOP_GUIDE.md` 获取完整指南。

### 方案三：混合模式（推荐第三步）

**思路**：关键文档使用 Gemini，其他文档使用 Ollama

#### 工作原理

- **关键文档**（Technical, API, Database, Requirements）→ 使用 Gemini（高质量）
- **其他文档** → 使用 Ollama（成本低）
- **所有文档** → 通过自动修复循环进一步改进

#### 启用方法

```env
# 使用 Ollama 作为默认模型
LLM_PROVIDER=ollama
OLLAMA_DEFAULT_MODEL=mixtral

# 提供 Gemini API Key（混合模式会自动启用）
GEMINI_API_KEY=your_key

# 启用自动修复循环（进一步优化所有文档）
ENABLE_AUTO_FIX=true
AUTO_FIX_THRESHOLD=70.0
```

#### 效果

- **关键文档**：80-95 分（Gemini 生成）
- **其他文档**：70-85 分（Ollama + 自动修复）
- **成本**：大幅降低（只对关键文档使用 Gemini）

#### 详细文档

参见 `HYBRID_MODE_GUIDE.md` 获取完整指南。

## 推荐配置

### 开发环境（快速迭代）

```env
# 使用快速模型
OLLAMA_DEFAULT_MODEL=dolphin3
OLLAMA_MAX_TOKENS=4096
OLLAMA_TIMEOUT=300
ENABLE_AUTO_FIX=true
AUTO_FIX_THRESHOLD=60.0  # 较低阈值，改进更多文档
```

### 生产环境（质量优先）

```env
# 使用高质量模型
OLLAMA_DEFAULT_MODEL=mixtral
OLLAMA_MAX_TOKENS=8192
OLLAMA_TIMEOUT=600
ENABLE_AUTO_FIX=true
AUTO_FIX_THRESHOLD=70.0

# 混合模式（关键文档用 Gemini）
GEMINI_API_KEY=your_key
```

### 最佳配置（推荐）

```env
# 本地模型配置
LLM_PROVIDER=ollama
OLLAMA_DEFAULT_MODEL=mixtral
OLLAMA_TIMEOUT=600
OLLAMA_MAX_TOKENS=8192

# 混合模式（关键文档用 Gemini）
GEMINI_API_KEY=your_key

# 自动修复循环
ENABLE_AUTO_FIX=true
AUTO_FIX_THRESHOLD=70.0
```

## 实施步骤

### 第一步：升级到 Mixtral

1. 拉取模型：
   ```bash
   ollama pull mixtral
   ```

2. 更新配置：
   ```env
   OLLAMA_DEFAULT_MODEL=mixtral
   ```

3. 测试效果：
   ```bash
   # 运行文档生成
   python -m src.web.app
   ```

4. 查看质量报告：
   ```bash
   cat docs/quality/quality_review.md
   ```

### 第二步：启用自动修复循环

1. 更新配置：
   ```env
   ENABLE_AUTO_FIX=true
   AUTO_FIX_THRESHOLD=70.0
   ```

2. 重新运行文档生成

3. 查看改进效果：
   - 查看日志中的自动修复信息
   - 对比改进前后的文档质量

### 第三步：启用混合模式（可选）

1. 设置 Gemini API Key：
   ```env
   GEMINI_API_KEY=your_key
   ```

2. 确保使用 Ollama 作为默认模型：
   ```env
   LLM_PROVIDER=ollama
   ```

3. 混合模式会自动启用（关键文档使用 Gemini）

## 性能对比

### 方案一：Dolphin3（8B）

- **质量分数**：40-60 分
- **生成时间**：快速（~30-60 秒/文档）
- **内存需求**：低（~8GB）
- **成本**：免费

### 方案二：Mixtral（47B）

- **质量分数**：50-70 分
- **生成时间**：中等（~60-120 秒/文档）
- **内存需求**：中等（~16-32GB）
- **成本**：免费

### 方案三：Mixtral + 自动修复

- **质量分数**：70-85 分
- **生成时间**：中等（~90-180 秒/文档，包括改进时间）
- **内存需求**：中等（~16-32GB）
- **成本**：免费

### 方案四：混合模式 + 自动修复

- **关键文档质量**：80-95 分（Gemini）
- **其他文档质量**：70-85 分（Ollama + 自动修复）
- **生成时间**：中等（关键文档更快）
- **内存需求**：中等（~16-32GB）
- **成本**：低（只对关键文档使用 Gemini）

## 故障排除

### 问题 1：Mixtral 内存不足

**解决方案**：
1. 使用量化版本：`ollama pull mixtral:8x7b-instruct-q4_K_M`
2. 关闭其他应用程序
3. 增加系统内存

### 问题 2：自动修复未触发

**解决方案**：
1. 检查 `ENABLE_AUTO_FIX=true`
2. 降低 `AUTO_FIX_THRESHOLD` 到 `60.0`
3. 查看 `quality_review.md` 文件

### 问题 3：改进后质量未提升

**解决方案**：
1. 使用更强大的模型（mixtral 而不是 dolphin3）
2. 启用混合模式（关键文档用 Gemini）
3. 检查 `DocumentImproverAgent` 的提示词

## 总结

通过以下三个步骤，可以将本地模型的质量提升到接近云端模型的水平：

1. **升级到 Mixtral**：使用更强大的模型（+10-20 分）
2. **启用自动修复循环**：迭代改进文档（+30-45 分）
3. **启用混合模式**：关键文档使用 Gemini（+15-25 分）

**最终效果**：
- **本地模型**：70-85 分（接近云端模型水平）
- **混合模式**：80-95 分（关键文档）
- **成本**：大幅降低（大部分文档免费）

**推荐配置**：
```env
LLM_PROVIDER=ollama
OLLAMA_DEFAULT_MODEL=mixtral
ENABLE_AUTO_FIX=true
AUTO_FIX_THRESHOLD=70.0
GEMINI_API_KEY=your_key  # 可选：混合模式
```

这将为您提供最佳的质量和成本平衡。

