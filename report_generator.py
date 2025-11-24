"""月度成本报告生成器"""
from datetime import datetime
from typing import Dict, List
from email_sender import EmailSender
import config


class ReportGenerator:
    """月度成本报告生成器"""
    
    def __init__(self):
        self.email_sender = EmailSender()
    
    def generate_monthly_report(self, creator_summary: Dict[str, Dict], month: str) -> bool:
        """生成并发送月度成本报告
        
        Args:
            creator_summary: 按创建者汇总的成本数据
            month: 月份字符串，如 "2024-01"
        
        Returns:
            bool: 是否发送成功
        """
        if not creator_summary:
            print("没有成本数据，跳过报告生成")
            return False
        
        # 按总成本排序
        sorted_creators = sorted(
            creator_summary.items(),
            key=lambda x: x[1]['total_cost'],
            reverse=True
        )
        
        # 计算总成本
        total_monthly_cost = sum(data['total_cost'] for data in creator_summary.values())
        
        # 生成报告
        html_report = self._build_html_report(sorted_creators, month, total_monthly_cost)
        text_report = self._build_text_report(sorted_creators, month, total_monthly_cost)
        
        # 发送邮件
        subject = f"Azure 月度成本报告 - {month}"
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import smtplib
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config.Config.SMTP_USERNAME
            msg['To'] = config.Config.ALERT_EMAIL_TO
            
            part1 = MIMEText(text_report, 'plain', 'utf-8')
            part2 = MIMEText(html_report, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(config.Config.SMTP_SERVER, config.Config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.Config.SMTP_USERNAME, config.Config.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ 月度报告已成功发送到 {config.Config.ALERT_EMAIL_TO}")
            return True
        except Exception as e:
            print(f"❌ 发送月度报告失败: {e}")
            return False
    
    def _build_html_report(self, sorted_creators: List, month: str, total_cost: float) -> str:
        """构建 HTML 格式的报告"""
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
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #007bff;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .summary-box {{
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
                .total-cost {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #007bff;
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
                .creator-name {{
                    font-weight: bold;
                    color: #007bff;
                }}
                .cost-value {{
                    font-weight: bold;
                    color: #28a745;
                }}
                .resource-list {{
                    font-size: 12px;
                    color: #666;
                    margin-top: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Azure 月度成本报告</h1>
                    <p>报告月份: <strong>{month}</strong></p>
                </div>
                
                <div class="summary-box">
                    <h2>成本摘要</h2>
                    <p>总成本: <span class="total-cost">${total_cost:.2f}</span></p>
                    <p>创建者数量: <strong>{len(sorted_creators)}</strong></p>
                </div>
                
                <h2>按创建者排序的成本明细</h2>
                <table>
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>创建者</th>
                            <th>总成本 (USD)</th>
                            <th>资源数量</th>
                            <th>占比</th>
                            <th>主要资源</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for idx, (creator, data) in enumerate(sorted_creators, 1):
            percentage = (data['total_cost'] / total_cost * 100) if total_cost > 0 else 0
            top_resources = data['resources'][:5]  # 显示前5个资源
            resource_list = ", ".join([f"{r['resource_name']} (${r['cost']:.2f})" for r in top_resources])
            if len(data['resources']) > 5:
                resource_list += f" ... 等共 {data['resource_count']} 个资源"
            
            html += f"""
                        <tr>
                            <td>{idx}</td>
                            <td class="creator-name">{creator}</td>
                            <td class="cost-value">${data['total_cost']:.2f}</td>
                            <td>{data['resource_count']}</td>
                            <td>{percentage:.1f}%</td>
                            <td class="resource-list">{resource_list}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
                
                <h2>详细资源列表</h2>
        """
        
        # 为每个创建者添加详细资源列表
        for creator, data in sorted_creators:
            html += f"""
                <h3>{creator} - 资源明细</h3>
                <table>
                    <thead>
                        <tr>
                            <th>资源名称</th>
                            <th>资源类型</th>
                            <th>成本 (USD)</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for resource in data['resources']:
                html += f"""
                        <tr>
                            <td>{resource.get('resource_name', 'N/A')}</td>
                            <td>{resource.get('resource_type', 'N/A')}</td>
                            <td>${resource.get('cost', 0):.2f}</td>
                        </tr>
                """
            
            html += """
                    </tbody>
                </table>
            """
        
        html += """
                <p style="margin-top: 20px; color: #666; font-size: 12px;">
                    此报告由 Azure 成本监控系统自动生成
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _build_text_report(self, sorted_creators: List, month: str, total_cost: float) -> str:
        """构建纯文本格式的报告"""
        text = f"""
Azure 月度成本报告
==================

报告月份: {month}
总成本: ${total_cost:.2f}
创建者数量: {len(sorted_creators)}

按创建者排序的成本明细:
"""
        
        for idx, (creator, data) in enumerate(sorted_creators, 1):
            percentage = (data['total_cost'] / total_cost * 100) if total_cost > 0 else 0
            text += f"""
{idx}. {creator}
   总成本: ${data['total_cost']:.2f}
   资源数量: {data['resource_count']}
   占比: {percentage:.1f}%
   
   主要资源:
"""
            for resource in data['resources'][:10]:  # 显示前10个资源
                text += f"   - {resource.get('resource_name', 'N/A')} ({resource.get('resource_type', 'N/A')}): ${resource.get('cost', 0):.2f}\n"
            
            if len(data['resources']) > 10:
                text += f"   ... 还有 {len(data['resources']) - 10} 个资源\n"
        
        text += "\n此报告由 Azure 成本监控系统自动生成"
        
        return text

