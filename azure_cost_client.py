"""Azure 成本管理客户端"""
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
    """Azure 成本查询客户端"""
    
    def __init__(self):
        """初始化 Azure 客户端"""
        credential = ClientSecretCredential(
            tenant_id=config.Config.AZURE_TENANT_ID,
            client_id=config.Config.AZURE_CLIENT_ID,
            client_secret=config.Config.AZURE_CLIENT_SECRET
        )
        self.client = CostManagementClient(credential)
        self.subscription_id = config.Config.AZURE_SUBSCRIPTION_ID
    
    def get_yesterday_cost(self) -> float:
        """获取前一天的总体成本"""
        yesterday = datetime.now() - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 构建查询定义
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
                # 返回总成本（通常是第一行的第一个值）
                total_cost = sum(float(row[0]) for row in result.rows if row and len(row) > 0 and row[0])
                return total_cost
            return 0.0
        except Exception as e:
            print(f"获取成本数据时出错: {e}")
            return 0.0
    
    def get_top_resources_by_cost(self, limit: int = 5) -> List[Dict]:
        """获取花费前N的资源及其创建者信息"""
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
                    if row and len(row) >= 3 and row[0]:  # 确保有足够的数据
                        cost = float(row[0])
                        resource_id = str(row[1]) if len(row) > 1 else "Unknown"
                        resource_type = str(row[2]) if len(row) > 2 else "Unknown"
                        
                        # 提取资源名称
                        resource_name = resource_id.split('/')[-1] if '/' in resource_id else resource_id
                        
                        resources.append({
                            'resource_id': resource_id,
                            'resource_name': resource_name,
                            'resource_type': resource_type,
                            'cost': cost,
                            'creator': "Unknown"  # 稍后在详细查询中填充
                        })
            
            # 按成本排序并返回前N个
            resources.sort(key=lambda x: x['cost'], reverse=True)
            return resources[:limit]
        except Exception as e:
            print(f"获取资源成本数据时出错: {e}")
            return []
    
    def get_detailed_cost_by_resource(self) -> List[Dict]:
        """获取详细的资源成本信息，包括创建者"""
        from azure.mgmt.resource import ResourceManagementClient
        
        # 获取基础成本数据
        top_resources = self.get_top_resources_by_cost(limit=10)
        
        if not top_resources:
            return []
        
        # 获取资源标签以找到创建者
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
                # 获取资源信息
                resource_info = resource_client.resources.get_by_id(
                    resource_id,
                    api_version='2021-04-01'
                )
                
                # 从标签中获取创建者信息
                if resource_info.tags:
                    # 常见的创建者标签键
                    creator_tags = ['CreatedBy', 'createdBy', 'Owner', 'owner', 'Creator', 'creator']
                    for tag_key in creator_tags:
                        if tag_key in resource_info.tags:
                            creator = resource_info.tags[tag_key]
                            break
                
                resource['creator'] = creator
            except Exception as e:
                # 如果无法获取资源信息，保持原有数据
                print(f"无法获取资源 {resource_id} 的详细信息: {e}")
                resource['creator'] = "Unknown"
            
            detailed_resources.append(resource)
        
        return detailed_resources[:5]
    
    def get_last_month_cost_by_creator(self) -> Dict[str, Dict]:
        """获取上个月按创建者汇总的成本数据
        
        Returns:
            Dict: {
                'creator_email': {
                    'total_cost': float,
                    'resource_count': int,
                    'resources': List[Dict]  # 该创建者的所有资源
                }
            }
        """
        from azure.mgmt.resource import ResourceManagementClient
        from collections import defaultdict
        
        # 计算上个月的日期范围
        today = datetime.now()
        # 上个月的第一天
        if today.month == 1:
            last_month_start = datetime(today.year - 1, 12, 1)
        else:
            last_month_start = datetime(today.year, today.month - 1, 1)
        
        # 上个月的最后一天
        if today.month == 1:
            last_month_end = datetime(today.year - 1, 12, 31, 23, 59, 59, 999999)
        else:
            # 计算上个月的最后一天
            if today.month == 2:
                last_day = 28 if today.year % 4 != 0 or (today.year % 100 == 0 and today.year % 400 != 0) else 29
            elif today.month in [4, 6, 9, 11]:
                last_day = 30
            else:
                last_day = 31
            last_month_end = datetime(today.year, today.month - 1, last_day, 23, 59, 59, 999999)
        
        print(f"查询上个月成本: {last_month_start.strftime('%Y-%m-%d')} 到 {last_month_end.strftime('%Y-%m-%d')}")
        
        # 查询所有资源的成本
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
                print("上个月没有成本数据")
                return {}
            
            # 获取所有资源及其成本
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
            
            print(f"找到 {len(all_resources)} 个资源，正在获取创建者信息...")
            
            # 获取资源标签以找到创建者
            credential = ClientSecretCredential(
                tenant_id=config.Config.AZURE_TENANT_ID,
                client_id=config.Config.AZURE_CLIENT_ID,
                client_secret=config.Config.AZURE_CLIENT_SECRET
            )
            resource_client = ResourceManagementClient(credential, self.subscription_id)
            
            # 按创建者汇总
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
                    # 获取资源信息
                    resource_info = resource_client.resources.get_by_id(
                        resource_id,
                        api_version='2021-04-01'
                    )
                    
                    # 从标签中获取创建者信息
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
                    # 如果无法获取资源信息，归类为 Unknown
                    print(f"无法获取资源 {resource_id} 的详细信息: {e}")
                    resource['creator'] = "Unknown"
                    unknown_count += 1
                    unknown_cost += resource['cost']
            
            # 如果有 Unknown 的资源，添加到汇总中
            if unknown_count > 0:
                creator_summary["Unknown"] = {
                    'total_cost': unknown_cost,
                    'resource_count': unknown_count,
                    'resources': [r for r in all_resources if r.get('creator') == 'Unknown']
                }
            
            # 转换为普通字典并按成本排序
            result_dict = dict(creator_summary)
            
            # 对每个创建者的资源按成本排序
            for creator in result_dict:
                result_dict[creator]['resources'].sort(key=lambda x: x['cost'], reverse=True)
            
            print(f"汇总完成，共 {len(result_dict)} 个创建者")
            return result_dict
            
        except Exception as e:
            print(f"获取上个月成本数据时出错: {e}")
            import traceback
            traceback.print_exc()
            return {}

