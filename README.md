# Azure Cost Monitoring and Alerting System

This is an automated Azure subscription cost monitoring program that sends email alerts when costs exceed a set threshold and displays the top 5 resources in the email. It also supports generating monthly cost reports aggregated by creator.

## Features

- ✅ Automatically checks the previous day's Azure subscription cost daily
- ✅ Sends email alerts when cost exceeds threshold
- ✅ Displays top 5 resources in email
- ✅ **Automatically generates monthly cost reports on the 1st of each month**, aggregated and sorted by creator
- ✅ Supports scheduled tasks and manual execution

## Requirements

- Python 3.7+
- Azure subscription
- Azure Service Principal (for API access)
- SMTP email server (e.g., Gmail, Outlook, etc.)

## Installation

### 1. Clone or download the project

```bash
cd /Users/liuyi/Cursortest
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Azure Service Principal

Create a Service Principal in Azure Portal:

1. Go to Azure Active Directory > App registrations
2. Click "New registration"
3. After creating the app, go to "Certificates & secrets"
4. Create a new client secret
5. Record the following information:
   - Tenant ID
   - Application (client) ID
   - Client secret value

### 4. Grant permissions

The Service Principal needs the following permissions:
- **Cost Management Reader** role (at subscription level)
- **Reader** role (for reading resource tags)

In Azure Portal:
1. Go to Subscriptions > Your subscription > Access control (IAM)
2. Add role assignment, select your Service Principal
3. Assign "Cost Management Reader" and "Reader" roles

### 5. Configure environment variables

Create a `.env` file (refer to the configuration example below):

```bash
# Azure configuration
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_SUBSCRIPTION_ID=your_subscription_id

# Email configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL_TO=alert@example.com

# Cost threshold configuration (USD)
COST_THRESHOLD=100.0
```

#### Gmail configuration

If using Gmail:
1. Enable two-factor authentication
2. Generate app password: Google Account > Security > App passwords
3. Use the app password as `SMTP_PASSWORD`

#### Other email providers

- **Outlook/Hotmail**: `smtp-mail.outlook.com`, port 587
- **QQ Mail**: `smtp.qq.com`, port 587
- **163 Mail**: `smtp.163.com`, port 25 or 465

## Usage

### Test run

#### Run daily check immediately

```bash
python main.py --once
```

This will immediately check the previous day's cost and send an alert (if threshold is exceeded).

#### Generate monthly report immediately

```bash
python main.py --monthly
```

This will immediately generate the previous month's monthly cost report and send an email.

### Scheduled run (automatic execution)

```bash
python main.py
```

The program will automatically execute on schedule:
- **Daily at 09:00**: Execute daily cost check
- **1st of each month at 10:00**: Generate previous month's monthly cost report

Press `Ctrl+C` to stop the service.

### Using system scheduled tasks (recommended)

For production environments, it's recommended to use system cron (Linux/Mac) or Task Scheduler (Windows):

#### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Add the following lines (daily check at 9 AM, monthly report on 1st at 10 AM)
0 9 * * * cd /Users/liuyi/Cursortest && /usr/bin/python3 main.py --once
0 10 1 * * cd /Users/liuyi/Cursortest && /usr/bin/python3 main.py --monthly
```

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create basic task
3. Set trigger to daily at 09:00
4. Action: Start program
   - Program: `python.exe`
   - Arguments: `main.py --once`
   - Start in: Project directory path

## Alert Format

### Email format

### Daily alert email

Alert emails contain the following information:

- **Cost summary**: Total cost, threshold, exceeded amount
- **Top 5 resources**:
  - Resource name
  - Resource type
  - Cost (USD)

### Monthly cost report

Monthly reports (sent on the 1st of each month) contain the following information:

- **Cost summary**: Previous month's total cost, number of creators
- **Cost details sorted by creator**:
  - Rank
  - Creator
  - Total cost (USD)
  - Number of resources
  - Percentage
  - Main resource list
- **Detailed resource list**: All resource details for each creator

## Resource creator tags

**Note**: Monthly reports need to aggregate costs by creator, so creator tags need to be added to resources.

The program retrieves creator information from Azure resource tags for monthly report aggregation. Supported tag keys:

- `CreatedBy`
- `createdBy`
- `Owner`
- `owner`
- `Creator`
- `creator`

It's recommended to add these tags when creating resources, for example:

```bash
az resource tag --tags CreatedBy=john.doe@example.com --ids /subscriptions/.../resourceGroups/.../providers/...
```

## Troubleshooting

### 1. Authentication failure

- Check if Service Principal credentials are correct
- Verify Service Principal has sufficient permissions

### 2. Unable to retrieve cost data

- Verify subscription ID is correct
- Check if "Cost Management Reader" role is assigned
- Note: Cost data may have delays (usually a few hours)

### 3. Email sending failure

- Check if SMTP configuration is correct
- For Gmail, ensure app password is used
- Check if firewall is blocking SMTP port

### 4. Monthly report unable to aggregate by creator

- Verify Service Principal has "Reader" role
- Check if resources have corresponding creator tags
- Some resource types may not support tags
- Resources without tags will be categorized as "Unknown"

## Project structure

```
.
├── main.py                  # Main program entry
├── config.py                # Configuration management
├── azure_cost_client.py     # Azure cost query client
├── email_sender.py          # Email sending module
├── report_generator.py       # Monthly report generator
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (needs to be created)
├── env.example              # Environment variable configuration example
├── .gitignore              # Git ignore file
└── README.md               # This document
```

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

# AzureCloudbudget
