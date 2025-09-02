#!/usr/bin/env python3
"""
CreditGuard AI Assistant - Cosmos DB Service
Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
Version: 1.0.0
Purpose: Azure Cosmos DB integration for storing customer data, evaluations, and decisions
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass, asdict

# Azure Cosmos DB
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions, PartitionKey


@dataclass
class CosmosConfig:
    """Cosmos DB configuration"""
    database_name: str = "creditguard_db"
    containers: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.containers is None:
            self.containers = {
                "customers": {
                    "partition_key": "/customerId",
                    "default_ttl": None,
                    "indexing_policy": {
                        "indexingMode": "consistent",
                        "automatic": True,
                        "includedPaths": [
                            {"path": "/*"}
                        ],
                        "excludedPaths": [
                            {"path": "/\"_etag\"/?"}
                        ]
                    }
                },
                "applications": {
                    "partition_key": "/customerId",
                    "default_ttl": None,
                    "indexing_policy": {
                        "indexingMode": "consistent",
                        "automatic": True,
                        "includedPaths": [
                            {"path": "/*"}
                        ]
                    }
                },
                "risk_evaluations": {
                    "partition_key": "/customer_id",
                    "default_ttl": 7776000,  # 90 days
                    "indexing_policy": {
                        "indexingMode": "consistent",
                        "automatic": True,
                        "includedPaths": [
                            {"path": "/customer_id/?"},
                            {"path": "/evaluation_timestamp/?"},
                            {"path": "/risk_level/?"},
                            {"path": "/overall_risk_score/?"}
                        ]
                    }
                },
                "credit_decisions": {
                    "partition_key": "/customer_id",
                    "default_ttl": None,  # Keep indefinitely for compliance
                    "indexing_policy": {
                        "indexingMode": "consistent",
                        "automatic": True,
                        "includedPaths": [
                            {"path": "/customer_id/?"},
                            {"path": "/application_id/?"},
                            {"path": "/outcome/?"},
                            {"path": "/decision_timestamp/?"}
                        ]
                    }
                },
                "compliance_reports": {
                    "partition_key": "/customer_id",
                    "default_ttl": None,  # Keep indefinitely for audit
                    "indexing_policy": {
                        "indexingMode": "consistent",
                        "automatic": True,
                        "includedPaths": [
                            {"path": "/customer_id/?"},
                            {"path": "/application_id/?"},
                            {"path": "/report_timestamp/?"}
                        ]
                    }
                },
                "audit_logs": {
                    "partition_key": "/operation_type",
                    "default_ttl": 31536000,  # 365 days
                    "indexing_policy": {
                        "indexingMode": "consistent",
                        "automatic": True,
                        "includedPaths": [
                            {"path": "/operation_type/?"},
                            {"path": "/timestamp/?"},
                            {"path": "/user_id/?"}
                        ]
                    }
                }
            }


class CosmosDBService:
    """
    Azure Cosmos DB Service for CreditGuard AI Assistant
    
    Manages all data persistence including:
    - Customer profiles and applications
    - Risk evaluations and credit decisions  
    - Compliance reports and audit trails
    - Performance metrics and analytics
    """
    
    def __init__(
        self,
        endpoint: str,
        key: str,
        config: Optional[CosmosConfig] = None
    ):
        self.endpoint = endpoint
        self.key = key
        self.config = config or CosmosConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Cosmos client
        self.client = None
        self.database = None
        self.containers = {}
        
        # Connection state
        self._initialized = False
        
        self.logger.info(f"CosmosDBService configured for database: {self.config.database_name}")
    
    async def initialize(self):
        """Initialize Cosmos DB client and ensure database/containers exist"""
        
        if self._initialized:
            return
        
        try:
            self.logger.info("Initializing Cosmos DB connection...")
            
            # Create Cosmos client
            self.client = CosmosClient(self.endpoint, credential=self.key)
            
            # Create or get database
            self.database = await self.client.create_database_if_not_exists(
                id=self.config.database_name
            )
            
            # Create containers
            for container_name, container_config in self.config.containers.items():
                container = await self.database.create_container_if_not_exists(
                    id=container_name,
                    partition_key=PartitionKey(path=container_config["partition_key"]),
                    default_ttl=container_config.get("default_ttl"),
                    indexing_policy=container_config.get("indexing_policy")
                )
                self.containers[container_name] = container
                
            self._initialized = True
            self.logger.info(f"Cosmos DB initialized with {len(self.containers)} containers")
            
        except Exception as e:
            self.logger.error(f"Error initializing Cosmos DB: {str(e)}")
            raise
    
    async def store_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store or update customer profile
        
        Args:
            customer_data: Customer profile information
            
        Returns:
            Stored customer document
        """
        await self._ensure_initialized()
        
        try:
            # Add metadata
            customer_data['document_type'] = 'customer_profile'
            customer_data['last_updated'] = datetime.now().isoformat()
            customer_data['version'] = customer_data.get('version', 1) + 1
            
            # Store in customers container
            result = await self.containers['customers'].upsert_item(customer_data)
            
            # Log audit trail
            await self._log_operation(
                operation_type='customer_update',
                document_id=customer_data['customerId'],
                details={'action': 'upsert', 'version': customer_data['version']}
            )
            
            self.logger.info(f"Customer stored: {customer_data['customerId']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing customer: {str(e)}")
            raise
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve customer profile by ID
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Customer profile data or None if not found
        """
        await self._ensure_initialized()
        
        try:
            item = await self.containers['customers'].read_item(
                item=customer_id,
                partition_key=customer_id
            )
            
            self.logger.info(f"Customer retrieved: {customer_id}")
            return item
            
        except exceptions.CosmosResourceNotFoundError:
            self.logger.info(f"Customer not found: {customer_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving customer: {str(e)}")
            raise
    
    async def store_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store credit application
        
        Args:
            application_data: Credit application information
            
        Returns:
            Stored application document
        """
        await self._ensure_initialized()
        
        try:
            # Add metadata
            application_data['document_type'] = 'credit_application'
            application_data['created_timestamp'] = datetime.now().isoformat()
            
            if 'application_id' not in application_data:
                application_data['application_id'] = f"APP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{application_data['customer_id']}"
            
            # Store in applications container
            result = await self.containers['applications'].create_item(application_data)
            
            # Log audit trail
            await self._log_operation(
                operation_type='application_created',
                document_id=application_data['application_id'],
                details={'customer_id': application_data['customer_id']}
            )
            
            self.logger.info(f"Application stored: {application_data['application_id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing application: {str(e)}")
            raise
    
    async def get_applications_by_customer(
        self, 
        customer_id: str,
        limit: int = 10,
        status_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get applications for a specific customer
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of applications to return
            status_filter: Filter by application status (optional)
            
        Returns:
            List of application documents
        """
        await self._ensure_initialized()
        
        try:
            query = "SELECT * FROM c WHERE c.customer_id = @customer_id"
            parameters = [{"name": "@customer_id", "value": customer_id}]
            
            if status_filter:
                query += " AND c.status = @status"
                parameters.append({"name": "@status", "value": status_filter})
            
            query += " ORDER BY c.created_timestamp DESC"
            
            applications = []
            async for item in self.containers['applications'].query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit
            ):
                applications.append(item)
            
            self.logger.info(f"Retrieved {len(applications)} applications for customer: {customer_id}")
            return applications
            
        except Exception as e:
            self.logger.error(f"Error retrieving applications: {str(e)}")
            raise
    
    async def store_risk_evaluation(self, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store risk evaluation results
        
        Args:
            evaluation_data: Risk evaluation information
            
        Returns:
            Stored evaluation document
        """
        await self._ensure_initialized()
        
        try:
            # Add metadata
            evaluation_data['document_type'] = 'risk_evaluation'
            evaluation_data['id'] = f"EVAL_{evaluation_data['customer_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if 'evaluation_timestamp' not in evaluation_data:
                evaluation_data['evaluation_timestamp'] = datetime.now().isoformat()
            
            # Store in risk_evaluations container
            result = await self.containers['risk_evaluations'].create_item(evaluation_data)
            
            # Log audit trail
            await self._log_operation(
                operation_type='risk_evaluation',
                document_id=evaluation_data['id'],
                details={
                    'customer_id': evaluation_data['customer_id'],
                    'risk_level': evaluation_data.get('risk_level'),
                    'risk_score': evaluation_data.get('overall_risk_score')
                }
            )
            
            self.logger.info(f"Risk evaluation stored: {evaluation_data['id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing risk evaluation: {str(e)}")
            raise
    
    async def get_risk_evaluations_by_customer(
        self,
        customer_id: str,
        limit: int = 10,
        days_back: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get risk evaluations for a customer within time period
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of evaluations to return
            days_back: Number of days to look back
            
        Returns:
            List of risk evaluation documents
        """
        await self._ensure_initialized()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            query = """
            SELECT * FROM c 
            WHERE c.customer_id = @customer_id 
            AND c.evaluation_timestamp >= @cutoff_date
            ORDER BY c.evaluation_timestamp DESC
            """
            
            parameters = [
                {"name": "@customer_id", "value": customer_id},
                {"name": "@cutoff_date", "value": cutoff_date}
            ]
            
            evaluations = []
            async for item in self.containers['risk_evaluations'].query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit
            ):
                evaluations.append(item)
            
            self.logger.info(f"Retrieved {len(evaluations)} risk evaluations for customer: {customer_id}")
            return evaluations
            
        except Exception as e:
            self.logger.error(f"Error retrieving risk evaluations: {str(e)}")
            raise
    
    async def store_credit_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store credit decision
        
        Args:
            decision_data: Credit decision information
            
        Returns:
            Stored decision document
        """
        await self._ensure_initialized()
        
        try:
            # Add metadata
            decision_data['document_type'] = 'credit_decision'
            decision_data['id'] = f"DEC_{decision_data['customer_id']}_{decision_data['application_id']}"
            
            if 'decision_timestamp' not in decision_data:
                decision_data['decision_timestamp'] = datetime.now().isoformat()
            
            # Store in credit_decisions container
            result = await self.containers['credit_decisions'].create_item(decision_data)
            
            # Log audit trail
            await self._log_operation(
                operation_type='credit_decision',
                document_id=decision_data['id'],
                details={
                    'customer_id': decision_data['customer_id'],
                    'application_id': decision_data['application_id'],
                    'outcome': decision_data.get('outcome'),
                    'approved_limit': decision_data.get('approved_limit')
                }
            )
            
            self.logger.info(f"Credit decision stored: {decision_data['id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing credit decision: {str(e)}")
            raise
    
    async def get_credit_decisions_by_customer(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get credit decisions for a customer
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of decisions to return
            
        Returns:
            List of credit decision documents
        """
        await self._ensure_initialized()
        
        try:
            query = """
            SELECT * FROM c 
            WHERE c.customer_id = @customer_id
            ORDER BY c.decision_timestamp DESC
            """
            
            parameters = [{"name": "@customer_id", "value": customer_id}]
            
            decisions = []
            async for item in self.containers['credit_decisions'].query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit
            ):
                decisions.append(item)
            
            self.logger.info(f"Retrieved {len(decisions)} credit decisions for customer: {customer_id}")
            return decisions
            
        except Exception as e:
            self.logger.error(f"Error retrieving credit decisions: {str(e)}")
            raise
    
    async def store_compliance_report(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store compliance report
        
        Args:
            compliance_data: Compliance report information
            
        Returns:
            Stored compliance document
        """
        await self._ensure_initialized()
        
        try:
            # Add metadata
            compliance_data['document_type'] = 'compliance_report'
            compliance_data['id'] = f"COMP_{compliance_data['customer_id']}_{compliance_data['application_id']}"
            
            if 'report_timestamp' not in compliance_data:
                compliance_data['report_timestamp'] = datetime.now().isoformat()
            
            # Store in compliance_reports container
            result = await self.containers['compliance_reports'].create_item(compliance_data)
            
            # Log audit trail
            await self._log_operation(
                operation_type='compliance_report',
                document_id=compliance_data['id'],
                details={
                    'customer_id': compliance_data['customer_id'],
                    'application_id': compliance_data['application_id'],
                    'compliance_score': compliance_data.get('compliance_score')
                }
            )
            
            self.logger.info(f"Compliance report stored: {compliance_data['id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing compliance report: {str(e)}")
            raise
    
    async def get_compliance_reports_by_customer(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get compliance reports for a customer
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of reports to return
            
        Returns:
            List of compliance report documents
        """
        await self._ensure_initialized()
        
        try:
            query = """
            SELECT * FROM c 
            WHERE c.customer_id = @customer_id
            ORDER BY c.report_timestamp DESC
            """
            
            parameters = [{"name": "@customer_id", "value": customer_id}]
            
            reports = []
            async for item in self.containers['compliance_reports'].query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit
            ):
                reports.append(item)
            
            self.logger.info(f"Retrieved {len(reports)} compliance reports for customer: {customer_id}")
            return reports
            
        except Exception as e:
            self.logger.error(f"Error retrieving compliance reports: {str(e)}")
            raise
    
    async def get_analytics_data(
        self,
        metric_type: str,
        time_period: int = 30,
        aggregation: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        Get analytics data for dashboard and reporting
        
        Args:
            metric_type: Type of metric ('applications', 'approvals', 'risk_scores', etc.)
            time_period: Number of days to analyze
            aggregation: Aggregation level ('daily', 'weekly', 'monthly')
            
        Returns:
            List of aggregated metric data
        """
        await self._ensure_initialized()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=time_period)).isoformat()
            
            if metric_type == 'applications':
                query = """
                SELECT 
                    COUNT(1) as count,
                    LEFT(c.created_timestamp, 10) as date
                FROM c 
                WHERE c.document_type = 'credit_application'
                AND c.created_timestamp >= @cutoff_date
                GROUP BY LEFT(c.created_timestamp, 10)
                ORDER BY LEFT(c.created_timestamp, 10)
                """
                
            elif metric_type == 'decisions':
                query = """
                SELECT 
                    COUNT(1) as count,
                    c.outcome,
                    LEFT(c.decision_timestamp, 10) as date
                FROM c 
                WHERE c.document_type = 'credit_decision'
                AND c.decision_timestamp >= @cutoff_date
                GROUP BY c.outcome, LEFT(c.decision_timestamp, 10)
                ORDER BY LEFT(c.decision_timestamp, 10)
                """
                
            elif metric_type == 'risk_distribution':
                query = """
                SELECT 
                    COUNT(1) as count,
                    c.risk_level
                FROM c 
                WHERE c.document_type = 'risk_evaluation'
                AND c.evaluation_timestamp >= @cutoff_date
                GROUP BY c.risk_level
                """
                
            else:
                raise ValueError(f"Unsupported metric type: {metric_type}")
            
            parameters = [{"name": "@cutoff_date", "value": cutoff_date}]
            
            # Choose appropriate container based on metric type
            container_map = {
                'applications': 'applications',
                'decisions': 'credit_decisions', 
                'risk_distribution': 'risk_evaluations'
            }
            
            container = self.containers[container_map[metric_type]]
            
            results = []
            async for item in container.query_items(query=query, parameters=parameters):
                results.append(item)
            
            self.logger.info(f"Retrieved {len(results)} analytics data points for {metric_type}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error retrieving analytics data: {str(e)}")
            raise
    
    async def search_documents(
        self,
        container_name: str,
        query: str,
        parameters: List[Dict[str, Any]] = None,
        max_items: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Execute custom search query across documents
        
        Args:
            container_name: Container to search in
            query: SQL query string
            parameters: Query parameters
            max_items: Maximum items to return
            
        Returns:
            List of matching documents
        """
        await self._ensure_initialized()
        
        try:
            if container_name not in self.containers:
                raise ValueError(f"Container {container_name} not found")
            
            container = self.containers[container_name]
            
            results = []
            async for item in container.query_items(
                query=query,
                parameters=parameters or [],
                max_item_count=max_items
            ):
                results.append(item)
            
            self.logger.info(f"Search returned {len(results)} results from {container_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing search query: {str(e)}")
            raise
    
    async def bulk_operations(
        self,
        container_name: str,
        operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute bulk operations (create, upsert, delete)
        
        Args:
            container_name: Container to operate on
            operations: List of operations with 'type' and 'item' keys
            
        Returns:
            List of operation results
        """
        await self._ensure_initialized()
        
        try:
            if container_name not in self.containers:
                raise ValueError(f"Container {container_name} not found")
            
            container = self.containers[container_name]
            results = []
            
            for operation in operations:
                op_type = operation.get('type', 'upsert')
                item = operation.get('item')
                
                try:
                    if op_type == 'create':
                        result = await container.create_item(item)
                    elif op_type == 'upsert':
                        result = await container.upsert_item(item)
                    elif op_type == 'delete':
                        result = await container.delete_item(
                            item=item['id'],
                            partition_key=item.get('partition_key', item['id'])
                        )
                    else:
                        raise ValueError(f"Unsupported operation type: {op_type}")
                    
                    results.append({
                        'success': True,
                        'operation': op_type,
                        'id': item.get('id'),
                        'result': result
                    })
                    
                except Exception as e:
                    results.append({
                        'success': False,
                        'operation': op_type,
                        'id': item.get('id'),
                        'error': str(e)
                    })
            
            success_count = sum(1 for r in results if r['success'])
            self.logger.info(f"Bulk operations completed: {success_count}/{len(operations)} successful")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in bulk operations: {str(e)}")
            raise
    
    async def _log_operation(
        self,
        operation_type: str,
        document_id: str,
        details: Dict[str, Any] = None
    ):
        """Log operation to audit trail"""
        
        try:
            audit_entry = {
                'id': f"AUDIT_{operation_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                'operation_type': operation_type,
                'document_id': document_id,
                'timestamp': datetime.now().isoformat(),
                'details': details or {},
                'user_id': 'system',  # In production, would use actual user ID
                'system_version': '1.0.0'
            }
            
            await self.containers['audit_logs'].create_item(audit_entry)
            
        except Exception as e:
            # Don't let audit logging failure break the main operation
            self.logger.warning(f"Failed to log audit entry: {str(e)}")
    
    async def get_audit_trail(
        self,
        document_id: str = None,
        operation_type: str = None,
        days_back: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail entries
        
        Args:
            document_id: Filter by specific document (optional)
            operation_type: Filter by operation type (optional)
            days_back: Number of days to look back
            limit: Maximum entries to return
            
        Returns:
            List of audit trail entries
        """
        await self._ensure_initialized()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            query = "SELECT * FROM c WHERE c.timestamp >= @cutoff_date"
            parameters = [{"name": "@cutoff_date", "value": cutoff_date}]
            
            if document_id:
                query += " AND c.document_id = @document_id"
                parameters.append({"name": "@document_id", "value": document_id})
            
            if operation_type:
                query += " AND c.operation_type = @operation_type"
                parameters.append({"name": "@operation_type", "value": operation_type})
            
            query += " ORDER BY c.timestamp DESC"
            
            audit_entries = []
            async for item in self.containers['audit_logs'].query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit
            ):
                audit_entries.append(item)
            
            self.logger.info(f"Retrieved {len(audit_entries)} audit entries")
            return audit_entries
            
        except Exception as e:
            self.logger.error(f"Error retrieving audit trail: {str(e)}")
            raise
    
    async def get_container_metrics(self) -> Dict[str, Any]:
        """Get metrics about container usage and performance"""
        
        await self._ensure_initialized()
        
        try:
            metrics = {}
            
            for container_name, container in self.containers.items():
                # Get basic container info
                container_properties = await container.read()
                
                # Count documents (basic query)
                count_query = "SELECT VALUE COUNT(1) FROM c"
                count_result = []
                async for item in container.query_items(query=count_query, max_item_count=1):
                    count_result.append(item)
                
                document_count = count_result[0] if count_result else 0
                
                metrics[container_name] = {
                    'document_count': document_count,
                    'last_modified': container_properties.get('_ts'),
                    'partition_key': container_properties.get('partitionKey', {}).get('paths', []),
                    'indexing_mode': container_properties.get('indexingPolicy', {}).get('indexingMode')
                }
            
            # Add database-level metrics
            database_properties = await self.database.read()
            metrics['database'] = {
                'name': self.config.database_name,
                'last_modified': database_properties.get('_ts'),
                'total_containers': len(self.containers)
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting container metrics: {str(e)}")
            raise
    
    async def cleanup_expired_documents(self) -> Dict[str, int]:
        """Clean up expired documents based on TTL policies"""
        
        await self._ensure_initialized()
        
        try:
            cleanup_results = {}
            
            # Clean up risk evaluations older than 90 days
            cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
            
            expired_evaluations_query = """
            SELECT c.id, c.customer_id FROM c 
            WHERE c.document_type = 'risk_evaluation' 
            AND c.evaluation_timestamp < @cutoff_date
            """
            
            parameters = [{"name": "@cutoff_date", "value": cutoff_date}]
            
            expired_count = 0
            async for item in self.containers['risk_evaluations'].query_items(
                query=expired_evaluations_query,
                parameters=parameters
            ):
                try:
                    await self.containers['risk_evaluations'].delete_item(
                        item=item['id'],
                        partition_key=item['customer_id']
                    )
                    expired_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete expired evaluation {item['id']}: {str(e)}")
            
            cleanup_results['risk_evaluations_deleted'] = expired_count
            
            # Clean up audit logs older than 365 days
            audit_cutoff = (datetime.now() - timedelta(days=365)).isoformat()
            
            expired_audit_query = """
            SELECT c.id, c.operation_type FROM c 
            WHERE c.timestamp < @audit_cutoff
            """
            
            audit_parameters = [{"name": "@audit_cutoff", "value": audit_cutoff}]
            
            audit_deleted = 0
            async for item in self.containers['audit_logs'].query_items(
                query=expired_audit_query,
                parameters=audit_parameters
            ):
                try:
                    await self.containers['audit_logs'].delete_item(
                        item=item['id'],
                        partition_key=item['operation_type']
                    )
                    audit_deleted += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete expired audit log {item['id']}: {str(e)}")
            
            cleanup_results['audit_logs_deleted'] = audit_deleted
            
            self.logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            raise
    
    async def _ensure_initialized(self):
        """Ensure service is initialized before operations"""
        if not self._initialized:
            await self.initialize()
    
    async def close(self):
        """Close Cosmos DB connection"""
        
        try:
            if self.client:
                await self.client.close()
                self.client = None
                self.database = None
                self.containers.clear()
                self._initialized = False
                
            self.logger.info("Cosmos DB connection closed")
            
        except Exception as e:
            self.logger.error(f"Error closing Cosmos DB connection: {str(e)}")
    
    def __str__(self):
        return f"CosmosDBService(database={self.config.database_name}, containers={len(self.containers)}, initialized={self._initialized})"