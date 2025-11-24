# Azure 成本监控告警系统

这是一个自动监控 Azure 订阅成本的程序，当成本超过设定阈值时，会自动发送邮件告警，并在邮件中展示花费前5的资源及其创建者信息。同时支持每月生成按创建者汇总的月度成本报告。

## 功能特性

- ✅ 每天自动检查前一天的 Azure 订阅成本
- ✅ 当成本超过阈值时发送邮件告警
- ✅ 在邮件中展示花费前5的资源
- ✅ 显示每个资源的创建者信息（从资源标签获取）
- ✅ **每月1号自动生成月度成本报告**，按创建者汇总并排序
- ✅ 支持定时任务和手动执行

## 环境要求

- Python 3.7+
- Azure 订阅
- Azure Service Principal（用于 API 访问）
- SMTP 邮件服务器（如 Gmail、Outlook 等）

## 安装步骤

### 1. 克隆或下载项目

```bash
cd /Users/liuyi/Cursortest
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 Azure Service Principal

在 Azure Portal 中创建 Service Principal：

1. 进入 Azure Active Directory > App registrations
2. 点击 "New registration"
3. 创建应用后，进入 "Certificates & secrets"
4. 创建新的客户端密钥
5. 记录以下信息：
   - Tenant ID
   - Application (client) ID
   - Client secret value

### 4. 授予权限

Service Principal 需要以下权限：
- **Cost Management Reader** 角色（在订阅级别）
- **Reader** 角色（用于读取资源标签）

在 Azure Portal 中：
1. 进入 Subscriptions > 你的订阅 > Access control (IAM)
2. 添加角色分配，选择你的 Service Principal
3. 分配 "Cost Management Reader" 和 "Reader" 角色

### 5. 配置环境变量

创建 `.env` 文件（参考下面的配置示例）：

```bash
# Azure 配置
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_SUBSCRIPTION_ID=your_subscription_id

# 邮件配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL_TO=alert@example.com

# 成本阈值配置（美元）
COST_THRESHOLD=100.0
```

#### Gmail 配置说明

如果使用 Gmail：
1. 启用两步验证
2. 生成应用专用密码：Google Account > Security > App passwords
3. 使用应用专用密码作为 `SMTP_PASSWORD`

#### 其他邮件服务商

- **Outlook/Hotmail**: `smtp-mail.outlook.com`, 端口 587
- **QQ邮箱**: `smtp.qq.com`, 端口 587
- **163邮箱**: `smtp.163.com`, 端口 25 或 465

## 使用方法

### 测试运行

#### 立即执行一次日常检查

```bash
python main.py --once
```

这将立即检查前一天的成本并发送告警（如果超过阈值）。

#### 立即生成月度报告

```bash
python main.py --monthly
```

这将立即生成上个月的月度成本报告并发送邮件。

### 定时运行（自动执行）

```bash
python main.py
```

程序将按计划自动执行：
- **每天 09:00**：执行日常成本检查
- **每月 1号 10:00**：生成上个月的月度成本报告

按 `Ctrl+C` 停止服务。

### 使用系统定时任务（推荐）

对于生产环境，建议使用系统的 cron（Linux/Mac）或任务计划程序（Windows）：

#### Linux/Mac (cron)

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天上午9点执行日常检查，每月1号10点执行月度报告）
0 9 * * * cd /Users/liuyi/Cursortest && /usr/bin/python3 main.py --once
0 10 1 * * cd /Users/liuyi/Cursortest && /usr/bin/python3 main.py --monthly
```

#### Windows (任务计划程序)

1. 打开任务计划程序
2. 创建基本任务
3. 设置触发器为每天 09:00
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`main.py --once`
   - 起始于：项目目录路径

## 告警格式

### 邮件格式

### 日常告警邮件

告警邮件包含以下信息：

- **成本摘要**：总成本、阈值、超出金额
- **花费前5的资源**：
  - 资源名称
  - 资源类型
  - 成本（USD）
  - 创建者（从资源标签获取）

### 月度成本报告

月度报告（每月1号发送）包含以下信息：

- **成本摘要**：上个月总成本、创建者数量
- **按创建者排序的成本明细表**：
  - 排名
  - 创建者
  - 总成本（USD）
  - 资源数量
  - 占比
  - 主要资源列表
- **详细资源列表**：每个创建者的所有资源明细

## 资源创建者标签

程序会从 Azure 资源的标签中查找创建者信息。支持的标签键：

- `CreatedBy`
- `createdBy`
- `Owner`
- `owner`
- `Creator`
- `creator`

建议在创建资源时添加这些标签，例如：

```bash
az resource tag --tags CreatedBy=john.doe@example.com --ids /subscriptions/.../resourceGroups/.../providers/...
```

## 故障排除

### 1. 认证失败

- 检查 Service Principal 的凭据是否正确
- 确认 Service Principal 有足够的权限

### 2. 无法获取成本数据

- 确认订阅 ID 正确
- 检查是否有 "Cost Management Reader" 角色
- 注意：成本数据可能有延迟（通常几小时）

### 3. 邮件发送失败

- 检查 SMTP 配置是否正确
- 对于 Gmail，确保使用应用专用密码
- 检查防火墙是否阻止 SMTP 端口

### 4. 无法获取资源创建者

- 确认 Service Principal 有 "Reader" 角色
- 检查资源是否有相应的标签
- 某些资源类型可能不支持标签

## 项目结构

```
.
├── main.py                  # 主程序入口
├── config.py                # 配置管理
├── azure_cost_client.py     # Azure 成本查询客户端
├── email_sender.py          # 邮件发送模块
├── report_generator.py      # 月度报告生成器
├── requirements.txt         # Python 依赖
├── .env                     # 环境变量（需要创建）
├── env.example              # 环境变量配置示例
├── .gitignore              # Git 忽略文件
└── README.md               # 本文档
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

# AzureCloudbudget
