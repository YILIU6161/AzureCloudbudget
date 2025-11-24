"""邮件发送模块"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict
import config


class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.smtp_server = config.Config.SMTP_SERVER
        self.smtp_port = config.Config.SMTP_PORT
        self.username = config.Config.SMTP_USERNAME
        self.password = config.Config.SMTP_PASSWORD
        self.to_email = config.Config.ALERT_EMAIL_TO
    
    def send_cost_alert(self, total_cost: float, threshold: float, top_resources: List[Dict]):
        """发送成本告警邮件"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        subject = f"Azure 成本告警 - {yesterday} 成本超过阈值"
        
        # 构建邮件正文
        html_body = self._build_email_body(total_cost, threshold, top_resources, yesterday)
        text_body = self._build_text_body(total_cost, threshold, top_resources, yesterday)
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = self.to_email
        
        # 添加文本和HTML版本
        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # 发送邮件
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            print(f"告警邮件已成功发送到 {self.to_email}")
            return True
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False
    
    def _build_email_body(self, total_cost: float, threshold: float, top_resources: List[Dict], date: str) -> str:
        """构建HTML格式的邮件正文"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .alert-box {{
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
                .cost-summary {{
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
                .cost-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #dc3545;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #007bff;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .resource-name {{
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Azure 成本告警</h2>
                
                <div class="alert-box">
                    <h3>⚠️ 成本超过阈值</h3>
                    <p>日期: <strong>{date}</strong></p>
                </div>
                
                <div class="cost-summary">
                    <h3>成本摘要</h3>
                    <p>总成本: <span class="cost-value">${total_cost:.2f}</span></p>
                    <p>阈值: <strong>${threshold:.2f}</strong></p>
                    <p>超出金额: <span class="cost-value">${total_cost - threshold:.2f}</span></p>
                </div>
                
                <h3>花费前5的资源</h3>
                <table>
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>资源名称</th>
                            <th>资源类型</th>
                            <th>成本 (USD)</th>
                            <th>创建者</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for idx, resource in enumerate(top_resources, 1):
            html += f"""
                        <tr>
                            <td>{idx}</td>
                            <td class="resource-name">{resource.get('resource_name', 'N/A')}</td>
                            <td>{resource.get('resource_type', 'N/A')}</td>
                            <td>${resource.get('cost', 0):.2f}</td>
                            <td>{resource.get('creator', 'Unknown')}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
                
                <p style="margin-top: 20px; color: #666; font-size: 12px;">
                    此邮件由 Azure 成本监控系统自动发送
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _build_text_body(self, total_cost: float, threshold: float, top_resources: List[Dict], date: str) -> str:
        """构建纯文本格式的邮件正文"""
        text = f"""
Azure 成本告警
==============

⚠️ 成本超过阈值

日期: {date}
总成本: ${total_cost:.2f}
阈值: ${threshold:.2f}
超出金额: ${total_cost - threshold:.2f}

花费前5的资源:
"""
        
        for idx, resource in enumerate(top_resources, 1):
            text += f"""
{idx}. {resource.get('resource_name', 'N/A')}
   资源类型: {resource.get('resource_type', 'N/A')}
   成本: ${resource.get('cost', 0):.2f}
   创建者: {resource.get('creator', 'Unknown')}
"""
        
        text += "\n此邮件由 Azure 成本监控系统自动发送"
        
        return text

