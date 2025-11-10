# 测试 Prompt - 餐厅预订系统

## 🎯 高质量测试 Prompt

这个 Prompt 设计用于全面测试 OmniDoc 系统的所有 Agent 和文档类型。

### Prompt 内容

```
我想构建一个AI驱动的SaaS平台，帮助餐厅管理他们的在线预订和客户等候名单。

平台需要支持多个用户角色（例如：餐厅经理、前台服务员、顾客）。

核心功能必须包括：
1. 一个面向顾客的预订门户网站（Web端和移动端适配）
2. 一个内部的餐桌管理仪表盘（显示餐桌状态、合并/拆分餐桌）
3. 一个自动的等候名单系统，能通过短信（SMS）自动发送提醒
4. 一个简单的客户信息管理(CRM)功能，用于记录顾客的偏好（例如：靠窗、过敏信息）

我们的商业模式是按月订阅 (SaaS)。在技术上，我们需要考虑PCI-DSS合规性（因为未来可能处理预订押金）和数据隐私（GDPR/CCPA）。我们的目标是在6个月内获取100家付费餐厅客户。
```

## 📊 为什么这个 Prompt 很好？

### ✅ 触发 L1 (战略) Agents

- **ProjectCharterAgent**: 商业模式（SaaS）、目标（100家客户）、时间线（6个月）
- **BusinessModelAgent**: 订阅模式、目标客户、收入模型
- **LegalComplianceAgent**: PCI-DSS、GDPR/CCPA 合规性要求

### ✅ 触发 L2 (产品) Agents

- **RequirementsAnalyst**: 用户角色（经理、服务员、顾客）、功能需求
- **UserStoriesAgent**: 明确的用户角色和功能（预订、等候、CRM）
- **PMDocumentationAgent**: 项目管理、时间线、资源规划

### ✅ 触发 L3 (技术) Agents

- **TechnicalDocumentationAgent**: 技术架构、系统设计
- **APIDocumentationAgent**: API 设计、接口规范
- **DatabaseSchemaAgent**: 数据模型、数据库设计
- **SetupGuideAgent**: 部署指南、环境配置

### ✅ 触发 Cross-Level Agents

- **StakeholderCommunicationAgent**: 利益相关者沟通
- **UserDocumentationAgent**: 用户指南
- **DeveloperDocumentationAgent**: 开发者文档
- **SupportPlaybookAgent**: 支持文档

## 🧪 测试场景

### 场景 1: 完整团队模式
- **Profile**: `team`
- **预期输出**: 所有文档类型（20+ 文档）
- **验证点**: 
  - L1 文档（战略层）
  - L2 文档（产品层）
  - L3 文档（技术层）
  - Cross-Level 文档

### 场景 2: 个人模式
- **Profile**: `individual`
- **预期输出**: 核心文档（10+ 文档）
- **验证点**:
  - 核心需求文档
  - 技术文档
  - 用户文档

### 场景 3: 代码分析模式
- **Profile**: `team`
- **Codebase Path**: 指向一个实际的代码库
- **预期输出**: 包含代码分析的文档
- **验证点**:
  - `code_analysis.json`
  - 更新的 API 文档
  - 更新的开发者文档

## 📋 验证清单

### L1 (战略层) 文档
- [ ] Requirements Document
- [ ] Project Charter
- [ ] Business Model
- [ ] Legal Compliance

### L2 (产品层) 文档
- [ ] User Stories
- [ ] PM Documentation
- [ ] Stakeholder Communication

### L3 (技术层) 文档
- [ ] Technical Documentation
- [ ] API Documentation
- [ ] Database Schema
- [ ] Setup Guide
- [ ] Developer Documentation
- [ ] Test Plan

### Cross-Level 文档
- [ ] User Documentation
- [ ] Support Playbook
- [ ] Marketing Plan (if team mode)

## 🎯 预期结果

### 质量指标
- **平均质量分数**: > 70/100
- **文档完整性**: 所有必需章节都存在
- **内容相关性**: 文档内容与 Prompt 高度相关

### 性能指标
- **生成时间**: < 10 分钟（团队模式）
- **并行执行**: Phase 2 任务并行执行
- **错误率**: < 5%

### 功能指标
- **文档层级**: 正确组织到 L1/L2/L3/Cross-Level
- **交叉引用**: 文档间正确交叉引用
- **格式转换**: 支持 Markdown/PDF/DOCX

## 💡 使用建议

1. **第一次测试**: 使用 `team` 模式，完整测试所有功能
2. **性能测试**: 对比同步和异步版本的性能
3. **质量测试**: 检查文档质量和完整性
4. **UI 测试**: 测试 Web 界面和文档预览
5. **错误处理**: 测试错误场景和恢复能力

## 🔍 故障排除

### 如果文档质量低
- 检查 LLM Provider 配置
- 验证 API Key 是否正确
- 检查模型是否可用
- 调整 temperature 参数

### 如果生成失败
- 检查日志输出
- 验证依赖关系
- 检查数据库连接
- 验证文件权限

### 如果性能慢
- 检查并行执行是否启用
- 验证异步处理是否工作
- 检查网络连接
- 优化 LLM Provider 配置

