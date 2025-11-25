"""Azure cost monitoring main program"""
import schedule
import time
from datetime import datetime
import config
from azure_cost_client import AzureCostClient
from email_sender import EmailSender
from report_generator import ReportGenerator


def check_cost_and_alert():
    """Check cost and send alert"""
    print(f"[{datetime.now()}] Starting Azure cost check...")
    
    try:
        # Initialize clients
        cost_client = AzureCostClient()
        email_sender = EmailSender()
        
        # Get previous day's total cost
        total_cost = cost_client.get_yesterday_cost()
        print(f"Previous day total cost: ${total_cost:.2f}")
        
        # Check if threshold is exceeded
        threshold = config.Config.COST_THRESHOLD
        if total_cost > threshold:
            print(f"⚠️ Cost ${total_cost:.2f} exceeded threshold ${threshold:.2f}, preparing to send alert...")
            
            # Get top 5 resources by cost
            print("Retrieving top 5 resources information...")
            top_resources = cost_client.get_detailed_cost_by_resource()
            
            # Send alert email
            success = email_sender.send_cost_alert(
                total_cost=total_cost,
                threshold=threshold,
                top_resources=top_resources
            )
            
            if success:
                print("✅ Alert email sent successfully")
            else:
                print("❌ Failed to send alert email")
        else:
            print(f"✅ Cost ${total_cost:.2f} is within threshold ${threshold:.2f}, no alert needed")
    
    except Exception as e:
        print(f"❌ Error occurred while checking cost: {e}")
        import traceback
        traceback.print_exc()


def run_once():
    """Run check once immediately (for testing)"""
    check_cost_and_alert()


def check_monthly_report():
    """Check and generate monthly report"""
    print(f"[{datetime.now()}] Starting monthly cost report generation...")
    
    try:
        cost_client = AzureCostClient()
        report_generator = ReportGenerator()
        
        # Get last month's cost data
        creator_summary = cost_client.get_last_month_cost_by_creator()
        
        if not creator_summary:
            print("No cost data, skipping report generation")
            return
        
        # Generate month string
        today = datetime.now()
        if today.month == 1:
            last_month = f"{today.year - 1}-12"
        else:
            last_month = f"{today.year}-{today.month - 1:02d}"
        
        # Generate and send report
        success = report_generator.generate_monthly_report(creator_summary, last_month)
        
        if success:
            print("✅ Monthly report generated and sent successfully")
        else:
            print("❌ Failed to generate or send monthly report")
    
    except Exception as e:
        print(f"❌ Error occurred while generating monthly report: {e}")
        import traceback
        traceback.print_exc()


def run_scheduled():
    """Run on schedule (daily execution)"""
    # Execute daily check at 9 AM
    schedule.every().day.at("09:00").do(check_cost_and_alert)
    
    # Execute monthly report on 1st of each month at 10 AM
    # schedule library doesn't support monthly execution, use daily date check instead
    def check_and_run_monthly():
        today = datetime.now()
        if today.day == 1:  # 1st of each month
            check_monthly_report()
    
    schedule.every().day.at("10:00").do(check_and_run_monthly)
    
    print("Cost monitoring service started")
    print("- Daily cost check at 09:00")
    print("- Monthly report generation on 1st at 10:00")
    print("Press Ctrl+C to stop the service")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for pending tasks
    except KeyboardInterrupt:
        print("\nService stopped")


if __name__ == "__main__":
    import sys
    
    # Validate configuration
    try:
        config.Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check the configuration items in .env file")
        sys.exit(1)
    
    # Determine run mode based on command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            # Run daily check once immediately (for testing)
            run_once()
        elif sys.argv[1] == "--monthly":
            # Generate monthly report immediately (for testing)
            check_monthly_report()
        else:
            print("Usage:")
            print("  python main.py          # Run on schedule (daily check + monthly report)")
            print("  python main.py --once   # Execute daily check once immediately")
            print("  python main.py --monthly # Generate monthly report immediately")
    else:
        # Run on schedule
        run_scheduled()
