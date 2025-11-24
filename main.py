"""Azure 成本监控主程序"""
import schedule
import time
from datetime import datetime
import config
from azure_cost_client import AzureCostClient
from email_sender import EmailSender
from report_generator import ReportGenerator


def check_cost_and_alert():
    """检查成本并发送告警"""
    print(f"[{datetime.now()}] 开始检查 Azure 成本...")
    
    try:
        # 初始化客户端
        cost_client = AzureCostClient()
        email_sender = EmailSender()
        
        # 获取前一天的总体成本
        total_cost = cost_client.get_yesterday_cost()
        print(f"前一天总成本: ${total_cost:.2f}")
        
        # 检查是否超过阈值
        threshold = config.Config.COST_THRESHOLD
        if total_cost > threshold:
            print(f"⚠️ 成本 ${total_cost:.2f} 超过阈值 ${threshold:.2f}，准备发送告警...")
            
            # 获取花费前5的资源
            print("正在获取花费前5的资源信息...")
            top_resources = cost_client.get_detailed_cost_by_resource()
            
            # 发送告警邮件
            success = email_sender.send_cost_alert(
                total_cost=total_cost,
                threshold=threshold,
                top_resources=top_resources
            )
            
            if success:
                print("✅ 告警邮件发送成功")
            else:
                print("❌ 告警邮件发送失败")
        else:
            print(f"✅ 成本 ${total_cost:.2f} 在阈值 ${threshold:.2f} 以内，无需告警")
    
    except Exception as e:
        print(f"❌ 检查成本时发生错误: {e}")
        import traceback
        traceback.print_exc()


def run_once():
    """立即运行一次检查（用于测试）"""
    check_cost_and_alert()


def check_monthly_report():
    """检查并生成月度报告"""
    print(f"[{datetime.now()}] 开始生成月度成本报告...")
    
    try:
        cost_client = AzureCostClient()
        report_generator = ReportGenerator()
        
        # 获取上个月的成本数据
        creator_summary = cost_client.get_last_month_cost_by_creator()
        
        if not creator_summary:
            print("没有成本数据，跳过报告生成")
            return
        
        # 生成月份字符串
        today = datetime.now()
        if today.month == 1:
            last_month = f"{today.year - 1}-12"
        else:
            last_month = f"{today.year}-{today.month - 1:02d}"
        
        # 生成并发送报告
        success = report_generator.generate_monthly_report(creator_summary, last_month)
        
        if success:
            print("✅ 月度报告生成并发送成功")
        else:
            print("❌ 月度报告生成或发送失败")
    
    except Exception as e:
        print(f"❌ 生成月度报告时发生错误: {e}")
        import traceback
        traceback.print_exc()


def run_scheduled():
    """按计划运行（每天执行）"""
    # 每天上午9点执行日常检查
    schedule.every().day.at("09:00").do(check_cost_and_alert)
    
    # 每月1号上午10点执行月度报告
    # schedule 库不支持每月执行，使用每天检查日期的方式
    def check_and_run_monthly():
        today = datetime.now()
        if today.day == 1:  # 每月1号
            check_monthly_report()
    
    schedule.every().day.at("10:00").do(check_and_run_monthly)
    
    print("成本监控服务已启动")
    print("- 每天 09:00 执行日常成本检查")
    print("- 每月 1号 10:00 生成月度报告")
    print("按 Ctrl+C 停止服务")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次是否有待执行的任务
    except KeyboardInterrupt:
        print("\n服务已停止")


if __name__ == "__main__":
    import sys
    
    # 验证配置
    try:
        config.Config.validate()
    except ValueError as e:
        print(f"配置错误: {e}")
        print("请检查 .env 文件中的配置项")
        sys.exit(1)
    
    # 根据命令行参数决定运行模式
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            # 立即运行一次日常检查（用于测试）
            run_once()
        elif sys.argv[1] == "--monthly":
            # 立即生成月度报告（用于测试）
            check_monthly_report()
        else:
            print("用法:")
            print("  python main.py          # 按计划运行（每天检查 + 每月报告）")
            print("  python main.py --once   # 立即执行一次日常检查")
            print("  python main.py --monthly # 立即生成月度报告")
    else:
        # 按计划运行
        run_scheduled()

