"""Azure cost management client"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    QueryDefinition, 
    QueryTimePeriod, 
    QueryAggregation, 
    QueryGrouping,
    QueryDataset
)
import config


class AzureCostClient:
    """Azure cost query client"""
    
    def __init__(self):
        """Initialize Azure client"""
        credential = ClientSecretCredential(
            tenant_id=config.Config.AZURE_TENANT_ID,
            client_id=config.Config.AZURE_CLIENT_ID,
            client_secret=config.Config.AZURE_CLIENT_SECRET
        )
        self.client = CostManagementClient(credential)
        self.subscription_id = config.Config.AZURE_SUBSCRIPTION_ID
    
    def get_yesterday_cost(self) -> float:
        """Get previous day's total cost"""
        yesterday = datetime.now() - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Build query definition
        query_definition = QueryDefinition(
            type="ActualCost",
            timeframe="Custom",
            time_period=QueryTimePeriod(
                from_property=start_date,
                to=end_date
            ),
            dataset=QueryDataset(
                granularity="Daily",
                aggregation={
                    "totalCost": QueryAggregation(
                        name="PreTaxCost",
                        function="Sum"
                    )
                }
            )
        )
        
        scope = f"/subscriptions/{self.subscription_id}"
        
        try:
            result = self.client.query.usage(scope=scope, parameters=query_definition)
            
            if result.rows:
                # Return total cost (usually the first value of the first row)
                total_cost = sum(float(row[0]) for row in result.rows if row and len(row) > 0 and row[0])
                return total_cost
            return 0.0
        except Exception as e:
            print(f"Error retrieving cost data: {e}")
            return 0.0
    
    def get_top_resources_by_cost(self, limit: int = 5) -> List[Dict]:
        """Get top N resources by cost and their creator information"""
        yesterday = datetime.now() - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        query_definition = QueryDefinition(
            type="ActualCost",
            timeframe="Custom",
            time_period=QueryTimePeriod(
                from_property=start_date,
                to=end_date
            ),
            dataset=QueryDataset(
                granularity="None",
                aggregation={
                    "totalCost": QueryAggregation(
                        name="PreTaxCost",
                        function="Sum"
                    )
                },
                grouping=[
                    QueryGrouping(
                        type="Dimension",
                        name="ResourceId"
                    ),
                    QueryGrouping(
                        type="Dimension",
                        name="ResourceType"
                    )
                ]
            )
        )
        
        scope = f"/subscriptions/{self.subscription_id}"
        
        try:
            result = self.client.query.usage(scope=scope, parameters=query_definition)
            
            resources = []
            if result.rows:
                for row in result.rows:
                    if row and len(row) >= 3 and row[0]:  # Ensure sufficient data
                        cost = float(row[0])
                        resource_id = str(row[1]) if len(row) > 1 else "Unknown"
                        resource_type = str(row[2]) if len(row) > 2 else "Unknown"
                        
                        # Extract resource name
                        resource_name = resource_id.split('/')[-1] if '/' in resource_id else resource_id
                        
                        resources.append({
                            'resource_id': resource_id,
                            'resource_name': resource_name,
                            'resource_type': resource_type,
                            'cost': cost,
                            'creator': "Unknown"  # Will be filled in detailed query later
                        })
            
            # Sort by cost and return top N
            resources.sort(key=lambda x: x['cost'], reverse=True)
            return resources[:limit]
        except Exception as e:
            print(f"Error retrieving resource cost data: {e}")
            return []
    
    def get_detailed_cost_by_resource(self) -> List[Dict]:
        """Get detailed resource cost information, including creator"""
        from azure.mgmt.resource import ResourceManagementClient
        
        # Get basic cost data
        top_resources = self.get_top_resources_by_cost(limit=10)
        
        if not top_resources:
            return []
        
        # Get resource tags to find creator
        credential = ClientSecretCredential(
            tenant_id=config.Config.AZURE_TENANT_ID,
            client_id=config.Config.AZURE_CLIENT_ID,
            client_secret=config.Config.AZURE_CLIENT_SECRET
        )
        resource_client = ResourceManagementClient(credential, self.subscription_id)
        
        detailed_resources = []
        for resource in top_resources:
            resource_id = resource['resource_id']
            creator = "Unknown"
            
            try:
                # Get resource information
                resource_info = resource_client.resources.get_by_id(
                    resource_id,
                    api_version='2021-04-01'
                )
                
                # Get creator information from tags
                if resource_info.tags:
                    # Common creator tag keys
                    creator_tags = ['CreatedBy', 'createdBy', 'Owner', 'owner', 'Creator', 'creator']
                    for tag_key in creator_tags:
                        if tag_key in resource_info.tags:
                            creator = resource_info.tags[tag_key]
                            break
                
                resource['creator'] = creator
            except Exception as e:
                # If unable to get resource information, keep original data
                print(f"Unable to get detailed information for resource {resource_id}: {e}")
                resource['creator'] = "Unknown"
            
            detailed_resources.append(resource)
        
        return detailed_resources[:5]
    
    def get_last_month_cost_by_creator(self) -> Dict[str, Dict]:
        """Get last month's cost data aggregated by creator
        
        Returns:
            Dict: {
                'creator_email': {
                    'total_cost': float,
                    'resource_count': int,
                    'resources': List[Dict]  # All resources for this creator
                }
            }
        """
        from azure.mgmt.resource import ResourceManagementClient
        from collections import defaultdict
        
        # Calculate last month's date range
        today = datetime.now()
        # First day of last month
        if today.month == 1:
            last_month_start = datetime(today.year - 1, 12, 1)
        else:
            last_month_start = datetime(today.year, today.month - 1, 1)
        
        # Last day of last month
        if today.month == 1:
            last_month_end = datetime(today.year - 1, 12, 31, 23, 59, 59, 999999)
        else:
            # Calculate last day of last month
            if today.month == 2:
                last_day = 28 if today.year % 4 != 0 or (today.year % 100 == 0 and today.year % 400 != 0) else 29
            elif today.month in [4, 6, 9, 11]:
                last_day = 30
            else:
                last_day = 31
            last_month_end = datetime(today.year, today.month - 1, last_day, 23, 59, 59, 999999)
        
        print(f"Querying last month's cost: {last_month_start.strftime('%Y-%m-%d')} to {last_month_end.strftime('%Y-%m-%d')}")
        
        # Query cost for all resources
        query_definition = QueryDefinition(
            type="ActualCost",
            timeframe="Custom",
            time_period=QueryTimePeriod(
                from_property=last_month_start,
                to=last_month_end
            ),
            dataset=QueryDataset(
                granularity="None",
                aggregation={
                    "totalCost": QueryAggregation(
                        name="PreTaxCost",
                        function="Sum"
                    )
                },
                grouping=[
                    QueryGrouping(
                        type="Dimension",
                        name="ResourceId"
                    ),
                    QueryGrouping(
                        type="Dimension",
                        name="ResourceType"
                    )
                ]
            )
        )
        
        scope = f"/subscriptions/{self.subscription_id}"
        
        try:
            result = self.client.query.usage(scope=scope, parameters=query_definition)
            
            if not result.rows:
                print("No cost data for last month")
                return {}
            
            # Get all resources and their costs
            all_resources = []
            for row in result.rows:
                if row and len(row) >= 3 and row[0]:
                    cost = float(row[0])
                    resource_id = str(row[1]) if len(row) > 1 else "Unknown"
                    resource_type = str(row[2]) if len(row) > 2 else "Unknown"
                    
                    resource_name = resource_id.split('/')[-1] if '/' in resource_id else resource_id
                    
                    all_resources.append({
                        'resource_id': resource_id,
                        'resource_name': resource_name,
                        'resource_type': resource_type,
                        'cost': cost
                    })
            
            print(f"Found {len(all_resources)} resources, retrieving creator information...")
            
            # Get resource tags to find creator
            credential = ClientSecretCredential(
                tenant_id=config.Config.AZURE_TENANT_ID,
                client_id=config.Config.AZURE_CLIENT_ID,
                client_secret=config.Config.AZURE_CLIENT_SECRET
            )
            resource_client = ResourceManagementClient(credential, self.subscription_id)
            
            # Aggregate by creator
            creator_summary = defaultdict(lambda: {
                'total_cost': 0.0,
                'resource_count': 0,
                'resources': []
            })
            
            unknown_count = 0
            unknown_cost = 0.0
            
            for resource in all_resources:
                resource_id = resource['resource_id']
                creator = "Unknown"
                
                try:
                    # Get resource information
                    resource_info = resource_client.resources.get_by_id(
                        resource_id,
                        api_version='2021-04-01'
                    )
                    
                    # Get creator information from tags
                    if resource_info.tags:
                        creator_tags = ['CreatedBy', 'createdBy', 'Owner', 'owner', 'Creator', 'creator']
                        for tag_key in creator_tags:
                            if tag_key in resource_info.tags:
                                creator = resource_info.tags[tag_key]
                                break
                    
                    resource['creator'] = creator
                    
                    if creator != "Unknown":
                        creator_summary[creator]['total_cost'] += resource['cost']
                        creator_summary[creator]['resource_count'] += 1
                        creator_summary[creator]['resources'].append(resource)
                    else:
                        unknown_count += 1
                        unknown_cost += resource['cost']
                        
                except Exception as e:
                    # If unable to get resource information, categorize as Unknown
                    print(f"Unable to get detailed information for resource {resource_id}: {e}")
                    resource['creator'] = "Unknown"
                    unknown_count += 1
                    unknown_cost += resource['cost']
            
            # If there are Unknown resources, add to summary
            if unknown_count > 0:
                creator_summary["Unknown"] = {
                    'total_cost': unknown_cost,
                    'resource_count': unknown_count,
                    'resources': [r for r in all_resources if r.get('creator') == 'Unknown']
                }
            
            # Convert to regular dict and sort by cost
            result_dict = dict(creator_summary)
            
            # Sort resources by cost for each creator
            for creator in result_dict:
                result_dict[creator]['resources'].sort(key=lambda x: x['cost'], reverse=True)
            
            print(f"Aggregation completed, total {len(result_dict)} creators")
            return result_dict
            
        except Exception as e:
            print(f"Error retrieving last month's cost data: {e}")
            import traceback
            traceback.print_exc()
            return {}
