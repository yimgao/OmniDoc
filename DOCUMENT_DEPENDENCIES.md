# Document Dependencies Reference

This document provides a comprehensive overview of all document types in OmniDoc and their dependency relationships.

> **Note**: Dependencies are now loaded from both `document_definitions.json` and `quality_rules.json`.

## Summary

- **Total Documents**: 59
- **Documents with Dependencies**: 59

## Documents with Dependencies

### API Documentation

- **ID**: `api_documentation`
- **Category**: 技术 / 开发
- **Priority**: 高
- **Dependencies** (1):
  - `fsd` - FSD (Functional Spec Doc)

### API Versioning & Deprecation Policy

- **ID**: `api_versioning_policy`
- **Category**: 技术 / 开发
- **Priority**: 中
- **Dependencies** (1):
  - `api_documentation` - API Documentation

### Accessibility Plan / ADA Compliance

- **ID**: `accessibility_plan`
- **Category**: 安全 / 合规
- **Priority**: 中
- **Dependencies** (2):
  - `ui_style_guide` - UI Style Guide
  - `ui_mockups` - UI Mockups / Mockups Docs

### Backup & Recovery Plan

- **ID**: `backup_recovery_plan`
- **Category**: 运维 / 高级管理
- **Priority**: 高
- **Dependencies** (2):
  - `database_schema` - Database Schema
  - `configuration_management_plan` - Configuration Management Plan

### Business Continuity Plan (BCP)

- **ID**: `bcp`
- **Category**: 运维 / 高级管理
- **Priority**: 中
- **Dependencies** (2):
  - `risk_management_plan` - Risk Management / Mitigation Plan
  - `backup_recovery_plan` - Backup & Recovery Plan

### Business Model

- **ID**: `business_model`
- **Category**: 项目管理 / 规划
- **Priority**: 高
- **Dependencies** (1):
  - `market_research` - Market Research & Competitive Analysis

### CI/CD Pipeline Doc

- **ID**: `cicd_doc`
- **Category**: 技术 / 开发
- **Priority**: 中
- **Dependencies** (2):
  - `developer_guide` - Developer Guide / README
  - `tad` - TAD (Technical Architecture Doc)

### Change Management Plan

- **ID**: `change_management_plan`
- **Category**: 项目管理 / 规划
- **Priority**: 中
- **Dependencies** (2):
  - `pm_management_doc` - PM Management Doc
  - `feature_roadmap` - Feature Roadmap

### Cloud Infrastructure / Cost Management Doc

- **ID**: `cloud_infrastructure_doc`
- **Category**: 运维 / 高级管理
- **Priority**: 中
- **Dependencies** (2):
  - `tad` - TAD (Technical Architecture Doc)
  - `scalability_plan` - Scalability Plan

### Configuration Management Plan

- **ID**: `configuration_management_plan`
- **Category**: 技术 / 开发
- **Priority**: 中
- **Dependencies** (2):
  - `developer_guide` - Developer Guide / README
  - `cicd_doc` - CI/CD Pipeline Doc

### Dashboard Metrics Specification

- **ID**: `dashboard_metrics`
- **Category**: 用户 / 产品分析
- **Priority**: 高
- **Dependencies** (1):
  - `kpi_metrics_doc` - KPIs / Metrics Document

### Data Governance / Data Quality Policy

- **ID**: `data_governance_policy`
- **Category**: 高级 / 可选 / 补充
- **Priority**: 中
- **Dependencies** (2):
  - `database_schema` - Database Schema
  - `user_analytics` - User Analytics / Behavior Tracking Doc

### Data Retention & Archiving Policy

- **ID**: `data_retention_policy`
- **Category**: 安全 / 合规
- **Priority**: 高
- **Dependencies** (2):
  - `database_schema` - Database Schema
  - `privacy_policy` - Privacy Policy / GDPR Compliance

### Database Schema

- **ID**: `database_schema`
- **Category**: 技术 / 开发
- **Priority**: 高
- **Dependencies** (1):
  - `fsd` - FSD (Functional Spec Doc)

### Deployment Plan

- **ID**: `deployment_plan`
- **Category**: 技术 / 开发
- **Priority**: 中
- **Dependencies** (2):
  - `cicd_doc` - CI/CD Pipeline Doc
  - `tad` - TAD (Technical Architecture Doc)

### Developer Guide / README

- **ID**: `developer_guide`
- **Category**: 技术 / 开发
- **Priority**: 高
- **Dependencies** (2):
  - `api_documentation` - API Documentation
  - `database_schema` - Database Schema

### End-of-Life (EOL) Policy

- **ID**: `eol_policy`
- **Category**: 安全 / 合规
- **Priority**: 中
- **Dependencies** (2):
  - `feature_roadmap` - Feature Roadmap
  - `api_versioning_policy` - API Versioning & Deprecation Policy

### Experimentation / A/B Testing Docs

- **ID**: `ab_testing_docs`
- **Category**: 测试 / QA / 支持
- **Priority**: 中
- **Dependencies** (2):
  - `feature_roadmap` - Feature Roadmap
  - `prd` - PRD (Product Requirements Doc)

### Experimentation / Feature Flag Docs

- **ID**: `feature_flag_docs`
- **Category**: 高级 / 可选 / 补充
- **Priority**: 中
- **Dependencies** (2):
  - `prd` - PRD (Product Requirements Doc)
  - `ab_testing_docs` - Experimentation / A/B Testing Docs

### FSD (Functional Spec Doc)

- **ID**: `fsd`
- **Category**: 产品设计 / 功能
- **Priority**: 高
- **Dependencies** (2):
  - `prd` - PRD (Product Requirements Doc)
  - `tad` - TAD (Technical Architecture Doc)

### Feature Roadmap

- **ID**: `feature_roadmap`
- **Category**: 项目管理 / 规划
- **Priority**: 高
- **Dependencies** (3):
  - `requirements` - Requirements Document
  - `project_charter` - Project Charter
  - `business_model` - Business Model

### Go-To-Market (GTM) Strategy

- **ID**: `gtm_strategy`
- **Category**: 用户 / 产品分析
- **Priority**: 中
- **Dependencies** (2):
  - `feature_roadmap` - Feature Roadmap
  - `business_model` - Business Model

### Incident Response Plan

- **ID**: `incident_response_plan`
- **Category**: 安全 / 合规
- **Priority**: 高
- **Dependencies** (2):
  - `security_plan` - Security Plan
  - `monitoring_logging_plan` - Monitoring & Logging Plan

### Innovation / R&D Plan

- **ID**: `innovation_plan`
- **Category**: 高级 / 可选 / 补充
- **Priority**: 中
- **Dependencies** (2):
  - `feature_roadmap` - Feature Roadmap
  - `technical_audit` - Technical Audit / Compliance Audit Reports

### Interaction / Flow Diagrams

- **ID**: `interaction_flows`
- **Category**: 产品设计 / 功能
- **Priority**: 中
- **Dependencies** (2):
  - `ui_mockups` - UI Mockups / Mockups Docs
  - `fsd` - FSD (Functional Spec Doc)

### KPIs / Metrics Document

- **ID**: `kpi_metrics_doc`
- **Category**: 用户 / 产品分析
- **Priority**: 高
- **Dependencies** (2):
  - `feature_roadmap` - Feature Roadmap
  - `dashboard_metrics` - Dashboard Metrics Specification

### Knowledge Base

- **ID**: `knowledge_base`
- **Category**: 测试 / QA / 支持
- **Priority**: 中
- **Dependencies** (1):
  - `user_support_doc` - User Support Document

### Legal / Terms of Service (ToS)

- **ID**: `terms_of_service`
- **Category**: 安全 / 合规
- **Priority**: 高
- **Dependencies** (1):
  - `privacy_policy` - Privacy Policy / GDPR Compliance

### Localization / Internationalization Plan

- **ID**: `localization_plan`
- **Category**: 安全 / 合规
- **Priority**: 中
- **Dependencies** (2):
  - `ui_mockups` - UI Mockups / Mockups Docs
  - `prd` - PRD (Product Requirements Doc)

### Maintenance Plan

- **ID**: `maintenance_plan`
- **Category**: 运维 / 高级管理
- **Priority**: 高
- **Dependencies** (2):
  - `cicd_doc` - CI/CD Pipeline Doc
  - `monitoring_logging_plan` - Monitoring & Logging Plan

### Market Research & Competitive Analysis

- **ID**: `market_research`
- **Category**: 高级 / 可选 / 补充
- **Priority**: 中
- **Dependencies** (2):
  - `business_model` - Business Model
  - `gtm_strategy` - Go-To-Market (GTM) Strategy

### Monitoring & Logging Plan

- **ID**: `monitoring_logging_plan`
- **Category**: 技术 / 开发
- **Priority**: 高
- **Dependencies** (2):
  - `tad` - TAD (Technical Architecture Doc)
  - `cicd_doc` - CI/CD Pipeline Doc

### Onboarding Flow

- **ID**: `onboarding_flow`
- **Category**: 产品设计 / 功能
- **Priority**: 高
- **Dependencies** (2):
  - `prd` - PRD (Product Requirements Doc)
  - `ui_mockups` - UI Mockups / Mockups Docs

### PM Management Doc

- **ID**: `pm_management_doc`
- **Category**: 项目管理 / 规划
- **Priority**: 高
- **Dependencies** (2):
  - `project_charter` - Project Charter
  - `stakeholders_doc` - Stakeholders Document

### PRD (Product Requirements Doc)

- **ID**: `prd`
- **Category**: 产品设计 / 功能
- **Priority**: 高
- **Dependencies** (3):
  - `requirements` - Requirements Document
  - `feature_roadmap` - Feature Roadmap
  - `ui_mockups` - UI Mockups / Mockups Docs

### Performance Tuning & Optimization Doc

- **ID**: `performance_optimization_doc`
- **Category**: 运维 / 高级管理
- **Priority**: 中
- **Dependencies** (2):
  - `tad` - TAD (Technical Architecture Doc)
  - `monitoring_logging_plan` - Monitoring & Logging Plan

### Privacy Policy / GDPR Compliance

- **ID**: `privacy_policy`
- **Category**: 安全 / 合规
- **Priority**: 高
- **Dependencies** (2):
  - `security_plan` - Security Plan
  - `data_retention_policy` - Data Retention & Archiving Policy

### Project Charter

- **ID**: `project_charter`
- **Category**: 项目管理 / 规划
- **Priority**: 高
- **Dependencies** (3):
  - `stakeholders_doc` - Stakeholders Document
  - `market_research` - Market Research & Competitive Analysis
  - `business_model` - Business Model

### Release Notes / Version History

- **ID**: `release_notes`
- **Category**: 用户 / 产品分析
- **Priority**: 高
- **Dependencies** (2):
  - `prd` - PRD (Product Requirements Doc)
  - `fsd` - FSD (Functional Spec Doc)

### Requirements Document

- **ID**: `requirements`
- **Category**: 项目管理 / 规划
- **Priority**: 高
- **Dependencies** (3):
  - `business_model` - Business Model
  - `market_research` - Market Research & Competitive Analysis
  - `project_charter` - Project Charter

### Risk Management / Mitigation Plan

- **ID**: `risk_management_plan`
- **Category**: 项目管理 / 规划
- **Priority**: 中
- **Dependencies** (3):
  - `project_charter` - Project Charter
  - `requirements` - Requirements Document
  - `business_model` - Business Model

### SLA / Service Level Agreement

- **ID**: `sla`
- **Category**: 运维 / 高级管理
- **Priority**: 中
- **Dependencies** (2):
  - `business_model` - Business Model
  - `maintenance_plan` - Maintenance Plan

### Scalability Plan

- **ID**: `scalability_plan`
- **Category**: 技术 / 开发
- **Priority**: 中
- **Dependencies** (1):
  - `tad` - TAD (Technical Architecture Doc)

### Security Plan

- **ID**: `security_plan`
- **Category**: 安全 / 合规
- **Priority**: 高
- **Dependencies** (2):
  - `tad` - TAD (Technical Architecture Doc)
  - `cicd_doc` - CI/CD Pipeline Doc

### Stakeholders Document

- **ID**: `stakeholders_doc`
- **Category**: 项目管理 / 规划
- **Priority**: 中
- **Dependencies** (2):
  - `project_charter` - Project Charter
  - `business_model` - Business Model

### Support Playbook

- **ID**: `support_playbook`
- **Category**: 测试 / QA / 支持
- **Priority**: 高
- **Dependencies** (2):
  - `user_support_doc` - User Support Document
  - `test_plan` - Test Plan Document

### Support Team Training Document

- **ID**: `support_training_doc`
- **Category**: 测试 / QA / 支持
- **Priority**: 中
- **Dependencies** (2):
  - `support_playbook` - Support Playbook
  - `user_support_doc` - User Support Document

### TAD (Technical Architecture Doc)

- **ID**: `tad`
- **Category**: 产品设计 / 功能
- **Priority**: 高
- **Dependencies** (3):
  - `fsd` - FSD (Functional Spec Doc)
  - `database_schema` - Database Schema
  - `api_documentation` - API Documentation

### Technical Audit / Compliance Audit Reports

- **ID**: `technical_audit`
- **Category**: 高级 / 可选 / 补充
- **Priority**: 中
- **Dependencies** (2):
  - `security_plan` - Security Plan
  - `privacy_policy` - Privacy Policy / GDPR Compliance

### Technical Debt Log / Refactoring Plan

- **ID**: `technical_debt_log`
- **Category**: 技术 / 开发
- **Priority**: 中
- **Dependencies** (2):
  - `tad` - TAD (Technical Architecture Doc)
  - `fsd` - FSD (Functional Spec Doc)

### Test Plan Document

- **ID**: `test_plan`
- **Category**: 测试 / QA / 支持
- **Priority**: 高
- **Dependencies** (2):
  - `prd` - PRD (Product Requirements Doc)
  - `fsd` - FSD (Functional Spec Doc)

### Third-Party Integration Documentation

- **ID**: `third_party_integrations`
- **Category**: 用户 / 产品分析
- **Priority**: 高
- **Dependencies** (2):
  - `api_documentation` - API Documentation
  - `tad` - TAD (Technical Architecture Doc)

### UI Mockups / Mockups Docs

- **ID**: `ui_mockups`
- **Category**: 产品设计 / 功能
- **Priority**: 高
- **Dependencies** (1):
  - `prd` - PRD (Product Requirements Doc)

### UI Style Guide

- **ID**: `ui_style_guide`
- **Category**: 产品设计 / 功能
- **Priority**: 中
- **Dependencies** (1):
  - `ui_mockups` - UI Mockups / Mockups Docs

### User Analytics / Behavior Tracking Doc

- **ID**: `user_analytics`
- **Category**: 用户 / 产品分析
- **Priority**: 中
- **Dependencies** (2):
  - `prd` - PRD (Product Requirements Doc)
  - `dashboard_metrics` - Dashboard Metrics Specification

### User Feedback Plan

- **ID**: `user_feedback_plan`
- **Category**: 测试 / QA / 支持
- **Priority**: 高
- **Dependencies** (2):
  - `knowledge_base` - Knowledge Base
  - `test_plan` - Test Plan Document

### User Support Document

- **ID**: `user_support_doc`
- **Category**: 测试 / QA / 支持
- **Priority**: 高
- **Dependencies** (2):
  - `prd` - PRD (Product Requirements Doc)
  - `knowledge_base` - Knowledge Base

### Vendor / Supplier Management Docs

- **ID**: `vendor_management_docs`
- **Category**: 运维 / 高级管理
- **Priority**: 中
- **Dependencies** (2):
  - `sla` - SLA / Service Level Agreement
  - `bcp` - Business Continuity Plan (BCP)

### Work Breakdown Structure (WBS)

- **ID**: `wbs`
- **Category**: 项目管理 / 规划
- **Priority**: 高
- **Dependencies** (3):
  - `project_charter` - Project Charter
  - `feature_roadmap` - Feature Roadmap
  - `requirements` - Requirements Document

---

## Documents without Dependencies

The following 0 documents have no dependencies:
