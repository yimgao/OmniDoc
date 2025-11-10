# OmniDoc 改进路线图

## 🎯 目标

将 OmniDoc 升级为现代化的、高性能的文档生成平台，具备：
1. 完整的异步处理能力
2. 灵活的 DAG 工作流
3. 现代化的 Web UI（WebSockets + Tailwind CSS）
4. 实时进度更新和文档预览

## 📋 实施计划

### Phase 1: 后端核心改进 (高优先级)

#### ✅ 1.1 状态管理（已完成）
- [x] 迁移 `project_status` 从内存字典到 SQLite 数据库
- [x] 使用 `ContextManager` 管理项目状态
- [x] 支持无状态 Web 应用

#### 🔄 1.2 集成 AsyncParallelExecutor（进行中）
- [ ] 替换 Phase 2 中的 `ParallelExecutor` 为 `AsyncParallelExecutor`
- [ ] 更新所有 Phase 2 任务为异步函数
- [ ] 使用 `await` 执行异步任务
- [ ] 测试并行执行性能

#### 📝 1.3 完善 WorkflowDAG 集成（待实施）
- [ ] 将所有 Agent 依赖关系定义到 `WorkflowDAG`
- [ ] 移除硬编码的 Phase 逻辑
- [ ] 使用 DAG 来驱动工作流执行
- [ ] 支持动态工作流配置

#### ⚡ 1.4 全面异步化（待实施）
- [ ] 将所有 Agent 的 `generate` 方法改为 `async def`
- [ ] 更新 `BaseAgent._call_llm` 为异步
- [ ] 移除 `run_in_executor` 包装
- [ ] 测试异步性能提升

### Phase 2: WebSocket 和实时通信 (中优先级)

#### 🔌 2.1 WebSocket 支持
- [ ] 添加 FastAPI WebSocket 端点 `/ws/{project_id}`
- [ ] 在工作流中发送实时进度更新
- [ ] 前端连接 WebSocket 并接收消息
- [ ] 移除轮询逻辑

#### 📊 2.2 进度事件系统
- [ ] 定义进度事件类型（START, PROGRESS, COMPLETE, ERROR）
- [ ] 在 `WorkflowCoordinator` 中发送事件
- [ ] 前端处理事件并更新 UI

### Phase 3: 前端现代化 (中优先级)

#### 🎨 3.1 Tailwind CSS 集成
- [ ] 安装和配置 Tailwind CSS
- [ ] 重构现有 HTML 使用 Tailwind 类
- [ ] 创建可复用的组件样式
- [ ] 响应式设计优化

#### 📁 3.2 文档层级显示
- [ ] 添加 `/api/results/{project_id}` 端点
- [ ] 使用 `DocumentOrganizer` 组织文档
- [ ] 前端渲染树状视图
- [ ] 支持折叠/展开

#### 👁️ 3.3 Markdown 预览
- [ ] 集成 Marked.js 或 react-markdown
- [ ] 添加预览面板
- [ ] 支持点击文档预览
- [ ] 语法高亮和样式

### Phase 4: API 增强 (低优先级)

#### 🔍 4.1 结果 API
- [ ] 创建 `/api/results/{project_id}` 端点
- [ ] 返回按层级组织的文档 JSON
- [ ] 包含文档元数据（大小、生成时间等）

#### 📈 4.2 统计 API
- [ ] 添加 `/api/stats/{project_id}` 端点
- [ ] 返回生成统计信息
- [ ] 包含质量分数、执行时间等

## 🧪 测试 Prompt

### 高质量测试 Prompt（餐厅预订系统）

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

**为什么这个 Prompt 很好？**
- ✅ 触发 L1 (战略) Agents：商业模式、目标、合规性要求
- ✅ 触发 L2 (产品) Agents：用户角色、功能需求
- ✅ 触发 L3 (技术) Agents：技术架构、数据库、API 设计

## 📊 实施优先级

### 高优先级（立即实施）
1. ✅ 状态管理（已完成）
2. 🔄 集成 AsyncParallelExecutor
3. 📝 完善 WorkflowDAG 集成

### 中优先级（本周实施）
4. 🔌 WebSocket 支持
5. 🎨 Tailwind CSS 集成
6. 📁 文档层级显示

### 低优先级（后续实施）
7. 👁️ Markdown 预览
8. 📈 统计 API
9. ⚡ 全面异步化

## 🚀 快速开始

### 1. 后端改进
```bash
# 1. 集成 AsyncParallelExecutor
# 2. 完善 WorkflowDAG
# 3. 添加 WebSocket 支持
```

### 2. 前端改进
```bash
# 1. 安装 Tailwind CSS
# 2. 重构 HTML
# 3. 添加 WebSocket 客户端
# 4. 实现文档预览
```

### 3. 测试
```bash
# 使用测试 Prompt 运行完整工作流
# 验证异步性能
# 测试 WebSocket 连接
# 检查 UI 响应
```

## 📝 注意事项

1. **向后兼容性**：保持现有 API 兼容，逐步迁移
2. **错误处理**：确保异步错误正确传播
3. **性能测试**：对比同步和异步版本的性能
4. **用户体验**：确保 UI 响应迅速、直观
5. **文档更新**：更新 README 和 API 文档

## 🎯 成功指标

- [ ] Phase 2 使用 AsyncParallelExecutor，性能提升 30%+
- [ ] WebSocket 实时更新，延迟 < 100ms
- [ ] UI 使用 Tailwind CSS，响应式设计
- [ ] 文档层级清晰展示，支持预览
- [ ] 所有测试通过，无回归问题

