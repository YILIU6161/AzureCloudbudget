"""Configuration file management"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Azure configuration
    AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')
    AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
    AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
    
    # Email configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO')
    
    # Cost threshold (USD)
    COST_THRESHOLD = float(os.getenv('COST_THRESHOLD', '100.0'))
    
    @classmethod
    def validate(cls):
        """Validate required configuration items"""
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
            raise ValueError(f"Missing required configuration items: {', '.join(missing)}")
