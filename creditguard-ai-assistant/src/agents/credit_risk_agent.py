#!/usr/bin/env python3
"""
CreditGuard AI Assistant - Main Credit Risk Agent
Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
Version: 1.0.0
Purpose: Main orchestrating agent for credit risk evaluation
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass, asdict

# Azure AI Services
from azure.identity import DefaultAzureCredential
from azure.ai.foundry import AIFoundryClient
from openai import AsyncAzureOpenAI

# Semantic Kernel
import semantic_kernel as sk
from semantic_kernel.core_plugins import TextPlugin
from semantic_kernel.planning import BasicPlanner
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function

# Project imports
from ..services.cosmos_db_service import CosmosDBService
from ..services.ai_search_service import AISearchService
from ..services.embeddings_service import EmbeddingsService
from ..utils.risk_calculator import RiskCalculator


@dataclass
class RiskEvaluation:
    """Risk evaluation result structure"""
    customer_id: str
    overall_risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors: List[Dict[str, Any]]
    market_insights: List[Dict[str, Any]]
    compliance_notes: List[str]
    recommendation: str
    confidence_score: float
    evaluation_timestamp: str


@dataclass
class CreditDecision:
    """Credit decision result structure"""
    customer_id: str
    application_id: str
    outcome: str  # APPROVED, DENIED, CONDITIONAL, FRAUD_ALERT
    approved_limit: Optional[float]
    risk_level: str
    conditions: List[str]
    reasoning: str
    compliance_score: float
    decision_timestamp: str
    underwriter_notes: str


class CreditRiskAgent:
    """
    Main Credit Risk Agent for comprehensive credit evaluation
    
    Orchestrates multiple plugins and services to perform:
    - Customer risk assessment
    - Market research and fraud detection
    - Policy compliance checking
    - Decision making with reasoning
    """
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        azure_openai_key: str,
        deployment_name: str,
        cosmos_service: CosmosDBService,
        search_service: AISearchService,
        embeddings_service: EmbeddingsService,
        model_temperature: float = 0.1
    ):
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_key = azure_openai_key
        self.deployment_name = deployment_name
        self.model_temperature = model_temperature
        
        # Services
        self.cosmos_service = cosmos_service
        self.search_service = search_service
        self.embeddings_service = embeddings_service
        self.risk_calculator = RiskCalculator()
        
        # Plugins registry
        self.plugins: Dict[str, Any] = {}
        
        # Initialize Azure OpenAI client
        self.openai_client = AsyncAzureOpenAI(
            api_key=azure_openai_key,
            api_version="2024-02-15-preview",
            azure_endpoint=azure_openai_endpoint
        )
        
        # Initialize Semantic Kernel
        self._initialize_kernel()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # System prompts
        self._load_system_prompts()
    
    def _initialize_kernel(self):
        """Initialize Semantic Kernel with Azure OpenAI"""
        self.kernel = sk.Kernel()
        
        # Add Azure OpenAI service
        self.kernel.add_service(
            sk.connectors.ai.open_ai.AzureChatCompletion(
                service_id="credit_ai",
                deployment_name=self.deployment_name,
                endpoint=self.azure_openai_endpoint,
                api_key=self.azure_openai_key,
                api_version="2024-02-15-preview"
            )
        )
        
        # Add core plugins
        self.kernel.add_plugin(TextPlugin(), plugin_name="text")
        
        # Initialize planner
        self.planner = BasicPlanner(service_id="credit_ai")
    
    def _load_system_prompts(self):
        """Load system prompts for different agent functions"""
        self.system_prompts = {
            "risk_evaluation": """You are a senior credit risk analyst at FinanceFirst Bank with 15+ years of experience. 
            Your role is to perform comprehensive credit risk evaluations using multiple data sources including:
            - Customer financial profiles and credit history
            - Real-time market research on fraud trends
            - Bank policies and regulatory requirements
            - External credit bureau data
            
            Evaluate each application thoroughly and provide detailed risk assessments with clear reasoning.
            Always prioritize regulatory compliance and customer protection while maintaining business objectives.
            
            Your analysis should be:
            - Factual and evidence-based
            - Compliant with banking regulations
            - Clear in reasoning and recommendations
            - Balanced between risk and business opportunity""",
            
            "decision_making": """You are the Chief Credit Officer at FinanceFirst Bank responsible for final credit decisions.
            Based on comprehensive risk evaluations, you must make final approval/denial decisions that:
            - Align with bank risk appetite and policies
            - Comply with all regulatory requirements
            - Protect the bank from excessive risk
            - Provide clear reasoning for auditability
            - Consider customer relationship value
            
            Your decisions should be decisive, well-reasoned, and fully documented for compliance purposes.""",
            
            "compliance_review": """You are a Compliance Officer ensuring all credit decisions meet regulatory requirements.
            Review all evaluations and decisions for:
            - Fair Credit Reporting Act (FCRA) compliance
            - Equal Credit Opportunity Act (ECOA) compliance
            - Know Your Customer (KYC) requirements
            - Anti-Money Laundering (AML) considerations
            - Consumer protection regulations
            
            Flag any compliance concerns and provide recommendations for remediation."""
        }
    
    async def register_plugin(self, name: str, plugin: Any):
        """Register a plugin with the agent"""
        self.plugins[name] = plugin
        self.logger.info(f"Registered plugin: {name}")
    
    async def evaluate_credit_risk(
        self,
        customer_data: Dict[str, Any],
        application_data: Dict[str, Any],
        include_market_research: bool = True,
        include_voice_summary: bool = False
    ) -> RiskEvaluation:
        """
        Perform comprehensive credit risk evaluation
        
        Args:
            customer_data: Customer profile information
            application_data: Credit application details
            include_market_research: Whether to include market fraud research
            include_voice_summary: Whether to generate voice summary
        
        Returns:
            RiskEvaluation object with comprehensive assessment
        """
        self.logger.info(f"Starting risk evaluation for customer: {customer_data['customerId']}")
        
        try:
            # Step 1: Get enhanced customer profile from credit bureau
            bureau_data = {}
            if 'credit_bureau' in self.plugins:
                self.logger.info("Fetching credit bureau data...")
                bureau_data = await self.plugins['credit_bureau'].get_credit_report(
                    customer_data['customerId']
                )
            
            # Step 2: Get relevant policies and procedures via RAG
            self.logger.info("Retrieving relevant policies...")
            policy_context = await self._get_policy_context(customer_data, application_data)
            
            # Step 3: Market research for fraud trends (if requested)
            market_insights = []
            if include_market_research and 'market_research' in self.plugins:
                self.logger.info("Conducting market research...")
                search_query = f"credit card fraud trends {datetime.now().year} {customer_data.get('personalInfo', {}).get('occupation', '')}"
                market_insights = await self.plugins['market_research'].search_fraud_trends(search_query)
            
            # Step 4: Calculate comprehensive risk score
            risk_score_data = self.risk_calculator.calculate_comprehensive_risk(
                customer_data=customer_data,
                application_data=application_data,
                bureau_data=bureau_data,
                market_context=market_insights
            )
            
            # Step 5: AI-powered risk analysis
            risk_analysis = await self._perform_ai_risk_analysis(
                customer_data=customer_data,
                application_data=application_data,
                bureau_data=bureau_data,
                policy_context=policy_context,
                market_insights=market_insights,
                risk_score_data=risk_score_data
            )
            
            # Step 6: Generate voice summary if requested
            if include_voice_summary and 'voice_communication' in self.plugins:
                await self._generate_voice_summary(risk_analysis)
            
            # Step 7: Create comprehensive risk evaluation
            risk_evaluation = RiskEvaluation(
                customer_id=customer_data['customerId'],
                overall_risk_score=risk_analysis['risk_score'],
                risk_level=risk_analysis['risk_level'],
                risk_factors=risk_analysis['risk_factors'],
                market_insights=market_insights[:3],  # Top 3 insights
                compliance_notes=risk_analysis['compliance_notes'],
                recommendation=risk_analysis['recommendation'],
                confidence_score=risk_analysis['confidence_score'],
                evaluation_timestamp=datetime.now().isoformat()
            )
            
            # Step 8: Store evaluation in Cosmos DB
            await self.cosmos_service.store_risk_evaluation(asdict(risk_evaluation))
            
            self.logger.info(f"Risk evaluation completed: {risk_evaluation.risk_level}")
            return risk_evaluation
            
        except Exception as e:
            self.logger.error(f"Error in risk evaluation: {str(e)}")
            raise
    
    async def make_credit_decision(
        self,
        risk_evaluation: RiskEvaluation,
        application_data: Dict[str, Any]
    ) -> CreditDecision:
        """
        Make final credit decision based on risk evaluation
        
        Args:
            risk_evaluation: Comprehensive risk evaluation
            application_data: Original application data
        
        Returns:
            CreditDecision object with final decision
        """
        self.logger.info(f"Making credit decision for customer: {risk_evaluation.customer_id}")
        
        try:
            # Get decision context from policies
            decision_context = await self._get_decision_context(risk_evaluation, application_data)
            
            # AI-powered decision making
            decision_analysis = await self._perform_ai_decision_analysis(
                risk_evaluation=risk_evaluation,
                application_data=application_data,
                decision_context=decision_context
            )
            
            # Create credit decision
            credit_decision = CreditDecision(
                customer_id=risk_evaluation.customer_id,
                application_id=application_data.get('application_id', f"APP_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                outcome=decision_analysis['outcome'],
                approved_limit=decision_analysis.get('approved_limit'),
                risk_level=risk_evaluation.risk_level,
                conditions=decision_analysis.get('conditions', []),
                reasoning=decision_analysis['reasoning'],
                compliance_score=decision_analysis['compliance_score'],
                decision_timestamp=datetime.now().isoformat(),
                underwriter_notes=decision_analysis['underwriter_notes']
            )
            
            # Store decision in Cosmos DB
            await self.cosmos_service.store_credit_decision(asdict(credit_decision))
            
            self.logger.info(f"Credit decision made: {credit_decision.outcome}")
            return credit_decision
            
        except Exception as e:
            self.logger.error(f"Error in decision making: {str(e)}")
            raise
    
    async def generate_compliance_report(
        self,
        customer_id: str,
        decision: CreditDecision,
        risk_factors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate compliance report for audit purposes"""
        
        self.logger.info(f"Generating compliance report for: {customer_id}")
        
        try:
            # Get compliance context
            compliance_context = await self._get_compliance_context(decision, risk_factors)
            
            # AI-powered compliance analysis
            compliance_analysis = await self._perform_compliance_analysis(
                customer_id=customer_id,
                decision=decision,
                risk_factors=risk_factors,
                compliance_context=compliance_context
            )
            
            compliance_report = {
                'customer_id': customer_id,
                'application_id': decision.application_id,
                'compliance_score': compliance_analysis['compliance_score'],
                'regulatory_checks': compliance_analysis['regulatory_checks'],
                'audit_trail': compliance_analysis['audit_trail'],
                'recommendations': compliance_analysis['recommendations'],
                'risk_mitigation': compliance_analysis['risk_mitigation'],
                'report_timestamp': datetime.now().isoformat(),
                'reviewed_by': 'CreditGuard AI Assistant',
                'next_review_date': (datetime.now() + timedelta(days=90)).isoformat()
            }
            
            # Store compliance report
            await self.cosmos_service.store_compliance_report(compliance_report)
            
            return compliance_report
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {str(e)}")
            raise
    
    async def _get_policy_context(
        self,
        customer_data: Dict[str, Any],
        application_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get relevant policy context using RAG"""
        
        # Create context-aware query
        query = f"""
        Customer profile: {customer_data.get('customerSegment', '')} customer
        Income: ${customer_data.get('personalInfo', {}).get('annualIncome', 0)}
        Credit score: {customer_data.get('financialProfile', {}).get('creditScore', 0)}
        Product type: {application_data.get('product_type', 'credit_card')}
        Requested limit: ${application_data.get('requested_limit', 0)}
        """
        
        # Get context from embeddings service
        context = await self.embeddings_service.get_context_for_query(
            query=query.strip(),
            max_results=5,
            min_similarity=0.7
        )
        
        return context
    
    async def _get_decision_context(
        self,
        risk_evaluation: RiskEvaluation,
        application_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get decision-making context from policies"""
        
        query = f"""
        Risk level: {risk_evaluation.risk_level}
        Risk score: {risk_evaluation.overall_risk_score}
        Product approval criteria
        Credit limit guidelines
        Risk mitigation strategies
        """
        
        context = await self.embeddings_service.get_context_for_query(
            query=query.strip(),
            max_results=3,
            min_similarity=0.75
        )
        
        return context
    
    async def _get_compliance_context(
        self,
        decision: CreditDecision,
        risk_factors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get compliance context for report generation"""
        
        query = f"""
        Credit decision: {decision.outcome}
        Risk factors: {', '.join([rf.get('factor', '') for rf in risk_factors[:3]])}
        Compliance requirements
        Regulatory documentation
        Audit requirements
        """
        
        context = await self.embeddings_service.get_context_for_query(
            query=query.strip(),
            max_results=4,
            min_similarity=0.7
        )
        
        return context
    
    async def _perform_ai_risk_analysis(
        self,
        customer_data: Dict[str, Any],
        application_data: Dict[str, Any],
        bureau_data: Dict[str, Any],
        policy_context: List[Dict[str, Any]],
        market_insights: List[Dict[str, Any]],
        risk_score_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform AI-powered risk analysis"""
        
        # Create comprehensive context
        context_text = "\n".join([doc['content'] for doc in policy_context])
        market_text = "\n".join([insight.get('summary', '') for insight in market_insights[:3]])
        
        prompt = f"""
        {self.system_prompts['risk_evaluation']}
        
        CUSTOMER PROFILE:
        {json.dumps(customer_data, indent=2)}
        
        APPLICATION DATA:
        {json.dumps(application_data, indent=2)}
        
        CREDIT BUREAU DATA:
        {json.dumps(bureau_data, indent=2)}
        
        CALCULATED RISK METRICS:
        {json.dumps(risk_score_data, indent=2)}
        
        RELEVANT BANK POLICIES:
        {context_text}
        
        MARKET FRAUD INSIGHTS:
        {market_text}
        
        Based on this comprehensive information, provide a detailed risk analysis in the following JSON format:
        {{
            "risk_score": <float 0-100>,
            "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
            "risk_factors": [
                {{"factor": "factor_name", "severity": "LOW|MEDIUM|HIGH", "description": "explanation"}},
                ...
            ],
            "compliance_notes": ["note1", "note2", ...],
            "recommendation": "detailed recommendation",
            "confidence_score": <float 0-1>,
            "key_insights": ["insight1", "insight2", ...]
        }}
        
        Ensure your analysis is thorough, compliant, and business-focused.
        """
        
        response = await self.openai_client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.model_temperature,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _perform_ai_decision_analysis(
        self,
        risk_evaluation: RiskEvaluation,
        application_data: Dict[str, Any],
        decision_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform AI-powered decision analysis"""
        
        context_text = "\n".join([doc['content'] for doc in decision_context])
        
        prompt = f"""
        {self.system_prompts['decision_making']}
        
        RISK EVALUATION:
        {json.dumps(asdict(risk_evaluation), indent=2)}
        
        APPLICATION DATA:
        {json.dumps(application_data, indent=2)}
        
        DECISION POLICIES:
        {context_text}
        
        Make a final credit decision based on this information. Provide your decision in JSON format:
        {{
            "outcome": "<APPROVED|DENIED|CONDITIONAL|FRAUD_ALERT>",
            "approved_limit": <amount if approved, null otherwise>,
            "conditions": ["condition1", "condition2", ...],
            "reasoning": "detailed explanation of decision",
            "compliance_score": <0-100>,
            "underwriter_notes": "additional notes for underwriting team",
            "next_steps": ["step1", "step2", ...]
        }}
        
        Your decision must be defensible, compliant, and aligned with bank policies.
        """
        
        response = await self.openai_client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.model_temperature,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _perform_compliance_analysis(
        self,
        customer_id: str,
        decision: CreditDecision,
        risk_factors: List[Dict[str, Any]],
        compliance_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform compliance analysis"""
        
        context_text = "\n".join([doc['content'] for doc in compliance_context])
        
        prompt = f"""
        {self.system_prompts['compliance_review']}
        
        CUSTOMER ID: {customer_id}
        
        CREDIT DECISION:
        {json.dumps(asdict(decision), indent=2)}
        
        RISK FACTORS:
        {json.dumps(risk_factors, indent=2)}
        
        COMPLIANCE REQUIREMENTS:
        {context_text}
        
        Perform a comprehensive compliance review and provide results in JSON format:
        {{
            "compliance_score": <0-100>,
            "regulatory_checks": {{
                "fcra_compliance": {{"status": "PASS|FAIL|REVIEW", "notes": "explanation"}},
                "ecoa_compliance": {{"status": "PASS|FAIL|REVIEW", "notes": "explanation"}},
                "kyc_compliance": {{"status": "PASS|FAIL|REVIEW", "notes": "explanation"}},
                "aml_compliance": {{"status": "PASS|FAIL|REVIEW", "notes": "explanation"}}
            }},
            "audit_trail": ["item1", "item2", ...],
            "recommendations": ["rec1", "rec2", ...],
            "risk_mitigation": ["mitigation1", "mitigation2", ...]
        }}
        
        Ensure thorough compliance coverage and actionable recommendations.
        """
        
        response = await self.openai_client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.model_temperature,
            max_tokens=1200,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _generate_voice_summary(self, risk_analysis: Dict[str, Any]):
        """Generate voice summary of risk analysis"""
        
        if 'voice_communication' not in self.plugins:
            return
        
        summary_text = f"""
        Risk assessment completed. 
        Overall risk level: {risk_analysis['risk_level']}.
        Risk score: {risk_analysis['risk_score']:.1f} out of 100.
        {risk_analysis['recommendation']}
        """
        
        try:
            await self.plugins['voice_communication'].text_to_speech(
                text=summary_text,
                language="en-US",
                voice_style="professional"
            )
        except Exception as e:
            self.logger.warning(f"Voice summary generation failed: {str(e)}")
    
    async def close_connections(self):
        """Close all service connections"""
        try:
            await self.cosmos_service.close()
            await self.search_service.close()
            # Close plugin connections
            for plugin in self.plugins.values():
                if hasattr(plugin, 'close'):
                    await plugin.close()
            self.logger.info("All connections closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing connections: {str(e)}")
    
    def __str__(self):
        return f"CreditRiskAgent(plugins={list(self.plugins.keys())}, services={['cosmos', 'search', 'embeddings']})"