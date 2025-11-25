"""Monthly cost report generator"""
from datetime import datetime
from typing import Dict, List
from email_sender import EmailSender
import config


class ReportGenerator:
    """Monthly cost report generator"""
    
    def __init__(self):
        self.email_sender = EmailSender()
    
    def generate_monthly_report(self, creator_summary: Dict[str, Dict], month: str) -> bool:
        """Generate and send monthly cost report
        
        Args:
            creator_summary: Cost data aggregated by creator
            month: Month string, e.g., "2024-01"
        
        Returns:
            bool: Whether sending was successful
        """
        if not creator_summary:
            print("No cost data, skipping report generation")
            return False
        
        # Sort by total cost
        sorted_creators = sorted(
            creator_summary.items(),
            key=lambda x: x[1]['total_cost'],
            reverse=True
        )
        
        # Calculate total cost
        total_monthly_cost = sum(data['total_cost'] for data in creator_summary.values())
        
        # Generate report
        html_report = self._build_html_report(sorted_creators, month, total_monthly_cost)
        text_report = self._build_text_report(sorted_creators, month, total_monthly_cost)
        
        # Send email
        subject = f"Azure Monthly Cost Report - {month}"
        
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
            
            print(f"✅ Monthly report successfully sent to {config.Config.ALERT_EMAIL_TO}")
            return True
        except Exception as e:
            print(f"❌ Failed to send monthly report: {e}")
            return False
    
    def _build_html_report(self, sorted_creators: List, month: str, total_cost: float) -> str:
        """Build HTML format report"""
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
                    <h1>Azure Monthly Cost Report</h1>
                    <p>Report Month: <strong>{month}</strong></p>
                </div>
                
                <div class="summary-box">
                    <h2>Cost Summary</h2>
                    <p>Total Cost: <span class="total-cost">${total_cost:.2f}</span></p>
                    <p>Number of Creators: <strong>{len(sorted_creators)}</strong></p>
                </div>
                
                <h2>Cost Details Sorted by Creator</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Creator</th>
                            <th>Total Cost (USD)</th>
                            <th>Resource Count</th>
                            <th>Percentage</th>
                            <th>Main Resources</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for idx, (creator, data) in enumerate(sorted_creators, 1):
            percentage = (data['total_cost'] / total_cost * 100) if total_cost > 0 else 0
            top_resources = data['resources'][:5]  # Show top 5 resources
            resource_list = ", ".join([f"{r['resource_name']} (${r['cost']:.2f})" for r in top_resources])
            if len(data['resources']) > 5:
                resource_list += f" ... and {data['resource_count']} resources in total"
            
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
                
                <h2>Detailed Resource List</h2>
        """
        
        # Add detailed resource list for each creator
        for creator, data in sorted_creators:
            html += f"""
                <h3>{creator} - Resource Details</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Resource Name</th>
                            <th>Resource Type</th>
                            <th>Cost (USD)</th>
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
                    This report was automatically generated by Azure Cost Monitoring System
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _build_text_report(self, sorted_creators: List, month: str, total_cost: float) -> str:
        """Build plain text format report"""
        text = f"""
Azure Monthly Cost Report
=========================

Report Month: {month}
Total Cost: ${total_cost:.2f}
Number of Creators: {len(sorted_creators)}

Cost Details Sorted by Creator:
"""
        
        for idx, (creator, data) in enumerate(sorted_creators, 1):
            percentage = (data['total_cost'] / total_cost * 100) if total_cost > 0 else 0
            text += f"""
{idx}. {creator}
   Total Cost: ${data['total_cost']:.2f}
   Resource Count: {data['resource_count']}
   Percentage: {percentage:.1f}%
   
   Main Resources:
"""
            for resource in data['resources'][:10]:  # Show top 10 resources
                text += f"   - {resource.get('resource_name', 'N/A')} ({resource.get('resource_type', 'N/A')}): ${resource.get('cost', 0):.2f}\n"
            
            if len(data['resources']) > 10:
                text += f"   ... and {len(data['resources']) - 10} more resources\n"
        
        text += "\nThis report was automatically generated by Azure Cost Monitoring System"
        
        return text

