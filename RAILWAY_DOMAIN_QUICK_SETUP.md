# Railway 自定义域名快速配置指南

## 🎯 配置步骤

### 第一步：在 Railway 添加自定义域名

1. **登录 Railway** → 进入你的项目 → 点击 `OmniDoc` 服务
2. **打开 Settings** → **Domains** 标签
3. **点击 "Custom Domain"** 或 "Add Custom Domain"
4. **输入域名**：`api.omnidoc.info`
5. **点击 "Add"** 或 "Save"
6. **Railway 会显示 DNS 配置信息**

### 第二步：复制 Railway 显示的 DNS 信息

Railway 会显示类似这样的信息：

**选项 1：使用 CNAME（推荐）**
```
Type: CNAME
Name: api
Value: omnidoc-production.up.railway.app
```
或
```
Type: CNAME  
Name: api
Value: [某个 .railway.app 的子域名]
```

**选项 2：使用 A 记录**
```
Type: A
Name: api
Value: [IP 地址]
```

### 第三步：在 Hostinger 配置 DNS

根据你在 Hostinger 看到的界面：

1. **Type（类型）**：
   - 如果 Railway 显示的是 **CNAME**，选择 **CNAME**
   - 如果 Railway 显示的是 **A 记录**，选择 **A**

2. **Name（名称）**：
   - 填写：`api`

3. **Points to（指向）**：
   - **如果是 CNAME**：复制 Railway 显示的完整值，例如 `omnidoc-production.up.railway.app`
   - **如果是 A 记录**：复制 Railway 显示的 IP 地址

4. **TTL**：
   - 使用默认值 `14400` 或 `3600` 都可以

5. **点击 "Add Record"（添加记录）**

### 第四步：等待 DNS 传播

- 通常需要 **1-24 小时**
- Railway 会显示域名状态（Pending → Active）
- 可以使用 https://dnschecker.org 检查 DNS 传播状态

## ⚠️ 重要提示

**不要直接填写 `api.omnidoc.info` 到 "Points to" 字段！**

"Points to" 字段应该填写：
- ✅ Railway 提供的 CNAME 目标（例如：`omnidoc-production.up.railway.app`）
- ✅ 或者 Railway 提供的 IP 地址（如果使用 A 记录）

## 🔍 如何确认配置正确？

1. **Railway 显示**：
   - 域名状态从 "Pending" 变为 "Active"
   - 显示绿色勾号 ✓

2. **测试域名**：
   ```bash
   # 应该返回 200 OK
   curl -I https://api.omnidoc.info/health
   ```

3. **DNS 检查**：
   ```bash
   dig api.omnidoc.info
   ```

## 📝 示例配置

假设 Railway 显示需要使用 CNAME：

**在 Hostinger 填写：**
```
Type: CNAME
Name: api
Points to: omnidoc-production.up.railway.app
TTL: 14400
```

然后点击 "Add Record"。

## 🆘 如果 Railway 没有显示 DNS 信息？

1. 确保你已经点击了 "Add" 保存了域名
2. 刷新页面
3. 等待几秒钟，Railway 可能需要时间生成 DNS 配置
4. 如果还是没有，检查域名格式是否正确（不能有 `https://` 前缀）

## ✅ 完成后

域名配置完成后：

1. **更新 Railway CORS 设置**：
   - Railway → Variables → `ALLOWED_ORIGINS`
   - 确保包含：`https://omnidoc.info,https://www.omnidoc.info`

2. **更新 Vercel 环境变量**：
   - Vercel → Settings → Environment Variables
   - `NEXT_PUBLIC_API_BASE=https://api.omnidoc.info`
   - **记得重新部署！**

