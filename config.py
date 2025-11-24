"""配置文件管理"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置"""
    
    # Azure 配置
    AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')
    AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
    AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
    
    # 邮件配置
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO')
    
    # 成本阈值（美元）
    COST_THRESHOLD = float(os.getenv('COST_THRESHOLD', '100.0'))
    
    @classmethod
    def validate(cls):
        """验证必需的配置项"""
        required = [
            'AZURE_TENANT_ID',
            'AZURE_CLIENT_ID',
            'AZURE_CLIENT_SECRET',
            'AZURE_SUBSCRIPTION_ID',
            'SMTP_USERNAME',
            'SMTP_PASSWORD',
            'ALERT_EMAIL_TO'
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing)}")

