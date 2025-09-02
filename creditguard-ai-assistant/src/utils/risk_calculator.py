#!/usr/bin/env python3
"""
CreditGuard AI Assistant - Risk Calculator Utility
Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
Version: 1.0.0
Purpose: Comprehensive credit risk calculation and scoring algorithms
"""

import json
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskFactor:
    """Individual risk factor"""
    factor_name: str
    factor_type: str  # FINANCIAL, BEHAVIORAL, DEMOGRAPHIC, EXTERNAL
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    weight: float
    value: Any
    description: str
    recommendation: str


@dataclass
class RiskScoreBreakdown:
    """Detailed risk score breakdown"""
    base_score: float
    credit_score_component: float
    financial_component: float
    behavioral_component: float
    demographic_component: float
    external_component: float
    adjustments: List[Dict[str, float]]
    final_score: float


@dataclass
class RiskAssessment:
    """Complete risk assessment result"""
    overall_risk_score: float
    risk_level: RiskLevel
    confidence_score: float
    risk_factors: List[RiskFactor]
    score_breakdown: RiskScoreBreakdown
    recommendations: List[str]
    assessment_timestamp: str
    model_version: str


class RiskCalculator:
    """
    Advanced Credit Risk Calculator for CreditGuard AI Assistant
    
    Implements multi-dimensional risk scoring including:
    - Traditional credit metrics (FICO, DTI, payment history)
    - Behavioral risk indicators
    - Market and economic factors
    - Fraud risk assessment
    - Regulatory compliance considerations
    """
    
    def __init__(self, model_version: str = "1.0.0"):
        self.model_version = model_version
        self.logger = logging.getLogger(__name__)
        
        # Risk scoring weights and parameters
        self.scoring_weights = {
            'credit_score': 0.35,
            'financial_stability': 0.25,
            'behavioral_patterns': 0.20,
            'demographic_factors': 0.10,
            'external_factors': 0.10
        }
        
        # Credit score ranges and base risk scores
        self.credit_score_bands = {
            (800, 850): {'base_risk': 5, 'multiplier': 0.5},
            (750, 799): {'base_risk': 10, 'multiplier': 0.7},
            (700, 749): {'base_risk': 20, 'multiplier': 1.0},
            (650, 699): {'base_risk': 35, 'multiplier': 1.3},
            (600, 649): {'base_risk': 50, 'multiplier': 1.6},
            (550, 599): {'base_risk': 70, 'multiplier': 2.0},
            (300, 549): {'base_risk': 85, 'multiplier': 2.5}
        }
        
        # Financial stability thresholds
        self.financial_thresholds = {
            'excellent_dti': 0.20,
            'good_dti': 0.30,
            'acceptable_dti': 0.40,
            'high_dti': 0.50,
            'min_income_multiplier': 0.3,  # Min credit limit as % of income
            'employment_stability_months': 24
        }
        
        # Behavioral risk indicators
        self.behavioral_indicators = {
            'multiple_inquiries_threshold': 5,  # Hard inquiries in 6 months
            'new_accounts_threshold': 3,  # New accounts in 12 months
            'utilization_high_threshold': 0.80,
            'utilization_optimal_threshold': 0.30,
            'payment_delinquency_weight': 15.0
        }
        
        # Market risk factors
        self.market_factors = {
            'economic_recession_multiplier': 1.3,
            'high_unemployment_multiplier': 1.2,
            'industry_risk_multipliers': {
                'hospitality': 1.4,
                'retail': 1.2,
                'technology': 0.9,
                'healthcare': 0.8,
                'government': 0.7,
                'education': 0.8
            }
        }
        
        self.logger.info(f"RiskCalculator initialized with model version: {model_version}")
    
    def calculate_comprehensive_risk(
        self,
        customer_data: Dict[str, Any],
        application_data: Dict[str, Any],
        bureau_data: Dict[str, Any] = None,
        market_context: List[Dict[str, Any]] = None
    ) -> RiskAssessment:
        """
        Calculate comprehensive risk assessment
        
        Args:
            customer_data: Customer profile information
            application_data: Credit application details
            bureau_data: Credit bureau information (optional)
            market_context: Market intelligence data (optional)
            
        Returns:
            Complete RiskAssessment object
        """
        self.logger.info(f"Calculating comprehensive risk for customer: {customer_data.get('customerId', 'unknown')}")
        
        try:
            # Initialize risk factors list
            risk_factors = []
            adjustments = []
            
            # 1. Credit Score Component (35% weight)
            credit_component, credit_factors = self._calculate_credit_score_component(
                customer_data, bureau_data
            )
            risk_factors.extend(credit_factors)
            
            # 2. Financial Stability Component (25% weight)
            financial_component, financial_factors = self._calculate_financial_component(
                customer_data, application_data
            )
            risk_factors.extend(financial_factors)
            
            # 3. Behavioral Patterns Component (20% weight)
            behavioral_component, behavioral_factors = self._calculate_behavioral_component(
                customer_data, bureau_data
            )
            risk_factors.extend(behavioral_factors)
            
            # 4. Demographic Factors Component (10% weight)
            demographic_component, demographic_factors = self._calculate_demographic_component(
                customer_data
            )
            risk_factors.extend(demographic_factors)
            
            # 5. External/Market Factors Component (10% weight)
            external_component, external_factors = self._calculate_external_component(
                customer_data, market_context
            )
            risk_factors.extend(external_factors)
            
            # Calculate base score
            base_score = (
                credit_component * self.scoring_weights['credit_score'] +
                financial_component * self.scoring_weights['financial_stability'] +
                behavioral_component * self.scoring_weights['behavioral_patterns'] +
                demographic_component * self.scoring_weights['demographic_factors'] +
                external_component * self.scoring_weights['external_factors']
            )
            
            # Apply risk adjustments
            final_score, adjustments = self._apply_risk_adjustments(
                base_score, risk_factors, customer_data, application_data
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(final_score)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                customer_data, bureau_data, risk_factors
            )
            
            # Create score breakdown
            score_breakdown = RiskScoreBreakdown(
                base_score=base_score,
                credit_score_component=credit_component,
                financial_component=financial_component,
                behavioral_component=behavioral_component,
                demographic_component=demographic_component,
                external_component=external_component,
                adjustments=adjustments,
                final_score=final_score
            )
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(risk_factors, risk_level)
            
            # Create final assessment
            assessment = RiskAssessment(
                overall_risk_score=final_score,
                risk_level=risk_level,
                confidence_score=confidence_score,
                risk_factors=risk_factors,
                score_breakdown=score_breakdown,
                recommendations=recommendations,
                assessment_timestamp=datetime.now().isoformat(),
                model_version=self.model_version
            )
            
            self.logger.info(f"Risk assessment completed: {risk_level.value} ({final_score:.1f})")
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error calculating comprehensive risk: {str(e)}")
            raise
    
    def _calculate_credit_score_component(
        self,
        customer_data: Dict[str, Any],
        bureau_data: Dict[str, Any] = None
    ) -> Tuple[float, List[RiskFactor]]:
        """Calculate credit score component of risk"""
        
        risk_factors = []
        
        # Get credit score from customer data or bureau data
        credit_score = 0
        if bureau_data and 'credit_score' in bureau_data:
            credit_score = bureau_data['credit_score']
        elif 'financialProfile' in customer_data:
            credit_score = customer_data['financialProfile'].get('creditScore', 0)
        
        # Find appropriate credit band
        base_risk = 50  # Default medium risk
        multiplier = 1.0
        
        for (min_score, max_score), band_data in self.credit_score_bands.items():
            if min_score <= credit_score <= max_score:
                base_risk = band_data['base_risk']
                multiplier = band_data['multiplier']
                break
        
        # Create credit score risk factor
        if credit_score < 650:
            severity = "HIGH"
            description = f"Credit score of {credit_score} indicates elevated credit risk"
            recommendation = "Consider secured credit products or co-signer requirements"
        elif credit_score < 700:
            severity = "MEDIUM"
            description = f"Credit score of {credit_score} indicates moderate credit risk"
            recommendation = "Standard underwriting with close monitoring"
        else:
            severity = "LOW"
            description = f"Credit score of {credit_score} indicates low credit risk"
            recommendation = "Eligible for premium credit products"
        
        credit_risk_factor = RiskFactor(
            factor_name="credit_score",
            factor_type="FINANCIAL",
            severity=severity,
            weight=self.scoring_weights['credit_score'],
            value=credit_score,
            description=description,
            recommendation=recommendation
        )
        risk_factors.append(credit_risk_factor)
        
        # Additional credit bureau factors
        if bureau_data:
            # Payment history
            payment_history = bureau_data.get('account_summary', {}).get('payment_history', 'UNKNOWN')
            if payment_history in ['POOR', 'FAIR']:
                payment_risk = RiskFactor(
                    factor_name="payment_history",
                    factor_type="BEHAVIORAL",
                    severity="HIGH" if payment_history == 'POOR' else "MEDIUM",
                    weight=0.15,
                    value=payment_history,
                    description=f"Payment history rated as {payment_history.lower()}",
                    recommendation="Require additional verification or monitoring"
                )
                risk_factors.append(payment_risk)
                base_risk += 10 if payment_history == 'POOR' else 5
            
            # Credit utilization
            utilization = bureau_data.get('account_summary', {}).get('credit_utilization', 0)
            if utilization > self.behavioral_indicators['utilization_high_threshold']:
                util_risk = RiskFactor(
                    factor_name="high_credit_utilization",
                    factor_type="BEHAVIORAL",
                    severity="HIGH",
                    weight=0.10,
                    value=utilization,
                    description=f"High credit utilization at {utilization*100:.1f}%",
                    recommendation="Monitor spending patterns closely"
                )
                risk_factors.append(util_risk)
                base_risk += 8
        
        return base_risk * multiplier, risk_factors
    
    def _calculate_financial_component(
        self,
        customer_data: Dict[str, Any],
        application_data: Dict[str, Any]
    ) -> Tuple[float, List[RiskFactor]]:
        """Calculate financial stability component"""
        
        risk_factors = []
        base_score = 30  # Default moderate risk
        
        # Get financial data
        personal_info = customer_data.get('personalInfo', {})
        financial_profile = customer_data.get('financialProfile', {})
        
        annual_income = personal_info.get('annualIncome', 0)
        employment_years = personal_info.get('employmentYears', 0)
        occupation = personal_info.get('occupation', 'unknown')
        
        # Debt-to-income calculation
        existing_debt = financial_profile.get('monthlyDebtPayments', 0)
        monthly_income = annual_income / 12 if annual_income > 0 else 0
        dti_ratio = existing_debt / monthly_income if monthly_income > 0 else 1.0
        
        # DTI Risk Assessment
        if dti_ratio > self.financial_thresholds['high_dti']:
            severity = "HIGH"
            description = f"High debt-to-income ratio at {dti_ratio*100:.1f}%"
            recommendation = "Require debt consolidation or co-signer"
            base_score += 20
        elif dti_ratio > self.financial_thresholds['acceptable_dti']:
            severity = "MEDIUM"
            description = f"Elevated debt-to-income ratio at {dti_ratio*100:.1f}%"
            recommendation = "Lower credit limits and close monitoring"
            base_score += 10
        elif dti_ratio > self.financial_thresholds['good_dti']:
            severity = "LOW"
            description = f"Acceptable debt-to-income ratio at {dti_ratio*100:.1f}%"
            recommendation = "Standard underwriting acceptable"
            base_score -= 5
        else:
            severity = "LOW"
            description = f"Excellent debt-to-income ratio at {dti_ratio*100:.1f}%"
            recommendation = "Qualified for premium products"
            base_score -= 15
        
        dti_risk_factor = RiskFactor(
            factor_name="debt_to_income_ratio",
            factor_type="FINANCIAL",
            severity=severity,
            weight=0.20,
            value=dti_ratio,
            description=description,
            recommendation=recommendation
        )
        risk_factors.append(dti_risk_factor)
        
        # Income stability assessment
        if annual_income < 25000:
            income_risk = RiskFactor(
                factor_name="low_income",
                factor_type="FINANCIAL",
                severity="HIGH",
                weight=0.15,
                value=annual_income,
                description=f"Low annual income of ${annual_income:,}",
                recommendation="Consider secured products or lower limits"
            )
            risk_factors.append(income_risk)
            base_score += 15
        elif annual_income < 40000:
            income_risk = RiskFactor(
                factor_name="moderate_income",
                factor_type="FINANCIAL",
                severity="MEDIUM",
                weight=0.10,
                value=annual_income,
                description=f"Moderate annual income of ${annual_income:,}",
                recommendation="Standard underwriting with income verification"
            )
            risk_factors.append(income_risk)
            base_score += 5
        
        # Employment stability
        if employment_years < 1:
            employment_risk = RiskFactor(
                factor_name="short_employment",
                factor_type="FINANCIAL",
                severity="HIGH",
                weight=0.10,
                value=employment_years,
                description=f"Short employment history: {employment_years} years",
                recommendation="Require additional income verification"
            )
            risk_factors.append(employment_risk)
            base_score += 10
        elif employment_years < 2:
            employment_risk = RiskFactor(
                factor_name="recent_employment",
                factor_type="FINANCIAL",
                severity="MEDIUM",
                weight=0.08,
                value=employment_years,
                description=f"Recent employment history: {employment_years} years",
                recommendation="Monitor for income stability"
            )
            risk_factors.append(employment_risk)
            base_score += 5
        
        # Occupation risk
        if occupation.lower() in self.market_factors.get('industry_risk_multipliers', {}):
            multiplier = self.market_factors['industry_risk_multipliers'][occupation.lower()]
            if multiplier > 1.0:
                occ_risk = RiskFactor(
                    factor_name="high_risk_occupation",
                    factor_type="DEMOGRAPHIC",
                    severity="MEDIUM",
                    weight=0.08,
                    value=occupation,
                    description=f"Higher risk occupation: {occupation}",
                    recommendation="Consider industry-specific risk factors"
                )
                risk_factors.append(occ_risk)
                base_score *= multiplier
        
        return min(100, max(0, base_score)), risk_factors
    
    def _calculate_behavioral_component(
        self,
        customer_data: Dict[str, Any],
        bureau_data: Dict[str, Any] = None
    ) -> Tuple[float, List[RiskFactor]]:
        """Calculate behavioral risk component"""
        
        risk_factors = []
        base_score = 25  # Default low-medium risk
        
        if not bureau_data:
            return base_score, risk_factors
        
        # Credit inquiries analysis
        inquiries = bureau_data.get('inquiries', [])
        recent_hard_inquiries = len([
            inq for inq in inquiries 
            if inq.get('inquiry_type') == 'HARD' and 
            self._is_recent_inquiry(inq.get('inquiry_date', ''))
        ])
        
        if recent_hard_inquiries > self.behavioral_indicators['multiple_inquiries_threshold']:
            inquiry_risk = RiskFactor(
                factor_name="excessive_credit_inquiries",
                factor_type="BEHAVIORAL",
                severity="HIGH",
                weight=0.15,
                value=recent_hard_inquiries,
                description=f"{recent_hard_inquiries} hard inquiries in past 6 months",
                recommendation="Investigate credit-seeking behavior"
            )
            risk_factors.append(inquiry_risk)
            base_score += 20
        elif recent_hard_inquiries > 2:
            inquiry_risk = RiskFactor(
                factor_name="multiple_credit_inquiries",
                factor_type="BEHAVIORAL",
                severity="MEDIUM",
                weight=0.10,
                value=recent_hard_inquiries,
                description=f"{recent_hard_inquiries} hard inquiries in past 6 months",
                recommendation="Monitor credit application patterns"
            )
            risk_factors.append(inquiry_risk)
            base_score += 10
        
        # Account opening patterns
        accounts = bureau_data.get('accounts', [])
        recent_accounts = len([
            acc for acc in accounts 
            if self._is_recent_account(acc.get('opened_date', ''))
        ])
        
        if recent_accounts > self.behavioral_indicators['new_accounts_threshold']:
            new_account_risk = RiskFactor(
                factor_name="rapid_account_opening",
                factor_type="BEHAVIORAL",
                severity="HIGH",
                weight=0.12,
                value=recent_accounts,
                description=f"{recent_accounts} new accounts opened in past 12 months",
                recommendation="Investigate potential credit abuse"
            )
            risk_factors.append(new_account_risk)
            base_score += 15
        
        # Payment patterns
        delinquent_accounts = len([
            acc for acc in accounts 
            if acc.get('delinquencies', 0) > 0
        ])
        
        if delinquent_accounts > 0:
            total_accounts = len(accounts)
            delinquency_rate = delinquent_accounts / total_accounts if total_accounts > 0 else 0
            
            if delinquency_rate > 0.3:
                severity = "CRITICAL"
                base_score += 25
            elif delinquency_rate > 0.15:
                severity = "HIGH"
                base_score += 15
            else:
                severity = "MEDIUM"
                base_score += 8
            
            payment_risk = RiskFactor(
                factor_name="payment_delinquencies",
                factor_type="BEHAVIORAL",
                severity=severity,
                weight=0.18,
                value=delinquency_rate,
                description=f"{delinquent_accounts} accounts with delinquencies ({delinquency_rate*100:.1f}%)",
                recommendation="Implement enhanced payment monitoring"
            )
            risk_factors.append(payment_risk)
        
        # Credit utilization behavior
        account_summary = bureau_data.get('account_summary', {})
        utilization = account_summary.get('credit_utilization', 0)
        
        if utilization > self.behavioral_indicators['utilization_high_threshold']:
            util_risk = RiskFactor(
                factor_name="high_utilization_pattern",
                factor_type="BEHAVIORAL",
                severity="HIGH",
                weight=0.12,
                value=utilization,
                description=f"High credit utilization at {utilization*100:.1f}%",
                recommendation="Monitor spending patterns and consider lower limits"
            )
            risk_factors.append(util_risk)
            base_score += 12
        elif utilization > 0.5:
            util_risk = RiskFactor(
                factor_name="elevated_utilization",
                factor_type="BEHAVIORAL",
                severity="MEDIUM",
                weight=0.08,
                value=utilization,
                description=f"Elevated credit utilization at {utilization*100:.1f}%",
                recommendation="Encourage utilization management"
            )
            risk_factors.append(util_risk)
            base_score += 6
        
        return min(100, max(0, base_score)), risk_factors
    
    def _calculate_demographic_component(
        self,
        customer_data: Dict[str, Any]
    ) -> Tuple[float, List[RiskFactor]]:
        """Calculate demographic risk component"""
        
        risk_factors = []
        base_score = 20  # Default low risk
        
        personal_info = customer_data.get('personalInfo', {})
        
        # Age-based risk assessment
        age = personal_info.get('age', 30)
        
        if age < 21:
            age_risk = RiskFactor(
                factor_name="young_age",
                factor_type="DEMOGRAPHIC",
                severity="MEDIUM",
                weight=0.08,
                value=age,
                description=f"Young age of {age} years indicates limited credit history",
                recommendation="Consider secured products or parental co-signer"
            )
            risk_factors.append(age_risk)
            base_score += 10
        elif age < 25:
            age_risk = RiskFactor(
                factor_name="early_career_age",
                factor_type="DEMOGRAPHIC",
                severity="LOW",
                weight=0.05,
                value=age,
                description=f"Age {age} indicates early career stage",
                recommendation="Standard underwriting with income verification"
            )
            risk_factors.append(age_risk)
            base_score += 5
        elif age > 70:
            age_risk = RiskFactor(
                factor_name="senior_age",
                factor_type="DEMOGRAPHIC",
                severity="LOW",
                weight=0.05,
                value=age,
                description=f"Senior age of {age} years",
                recommendation="Verify income stability and retirement planning"
            )
            risk_factors.append(age_risk)
            base_score += 3
        
        # Geographic risk (basic implementation)
        # In production, this would use sophisticated geographic risk models
        address = customer_data.get('addressInfo', {})
        state = address.get('state', '').upper()
        
        # High-risk states (example - would use real data)
        high_risk_states = ['NV', 'FL', 'AZ']  # Example high-foreclosure states
        
        if state in high_risk_states:
            geo_risk = RiskFactor(
                factor_name="high_risk_geography",
                factor_type="DEMOGRAPHIC",
                severity="MEDIUM",
                weight=0.06,
                value=state,
                description=f"Location in higher-risk state: {state}",
                recommendation="Apply regional risk adjustments"
            )
            risk_factors.append(geo_risk)
            base_score += 8
        
        return min(100, max(0, base_score)), risk_factors
    
    def _calculate_external_component(
        self,
        customer_data: Dict[str, Any],
        market_context: List[Dict[str, Any]] = None
    ) -> Tuple[float, List[RiskFactor]]:
        """Calculate external/market risk component"""
        
        risk_factors = []
        base_score = 15  # Default low risk
        
        if not market_context:
            return base_score, risk_factors
        
        # Analyze market intelligence for relevant risk factors
        for insight in market_context[:5]:  # Top 5 insights
            if insight.get('severity') in ['HIGH', 'CRITICAL']:
                if 'fraud' in insight.get('summary', '').lower():
                    fraud_risk = RiskFactor(
                        factor_name="market_fraud_trend",
                        factor_type="EXTERNAL",
                        severity="HIGH",
                        weight=0.12,
                        value=insight.get('confidence_level', 0),
                        description=f"Market fraud trend: {insight.get('summary', '')[:100]}",
                        recommendation="Implement enhanced fraud monitoring"
                    )
                    risk_factors.append(fraud_risk)
                    base_score += 15
                
                elif 'economic' in insight.get('summary', '').lower():
                    econ_risk = RiskFactor(
                        factor_name="economic_headwinds",
                        factor_type="EXTERNAL",
                        severity="MEDIUM",
                        weight=0.08,
                        value=insight.get('confidence_level', 0),
                        description=f"Economic risk factor: {insight.get('summary', '')[:100]}",
                        recommendation="Apply conservative underwriting"
                    )
                    risk_factors.append(econ_risk)
                    base_score += 10
        
        # Industry-specific external factors
        personal_info = customer_data.get('personalInfo', {})
        occupation = personal_info.get('occupation', '').lower()
        
        if any(keyword in occupation for keyword in ['hospitality', 'restaurant', 'tourism']):
            # These industries were heavily impacted by COVID-19, for example
            industry_risk = RiskFactor(
                factor_name="volatile_industry",
                factor_type="EXTERNAL",
                severity="MEDIUM",
                weight=0.10,
                value=occupation,
                description=f"Employment in volatile industry: {occupation}",
                recommendation="Monitor employment stability closely"
            )
            risk_factors.append(industry_risk)
            base_score += 12
        
        return min(100, max(0, base_score)), risk_factors
    
    def _apply_risk_adjustments(
        self,
        base_score: float,
        risk_factors: List[RiskFactor],
        customer_data: Dict[str, Any],
        application_data: Dict[str, Any]
    ) -> Tuple[float, List[Dict[str, float]]]:
        """Apply final risk adjustments"""
        
        adjustments = []
        final_score = base_score
        
        # First-time customer adjustment
        if self._is_first_time_customer(customer_data):
            adjustment = base_score * 0.1  # 10% increase for new customers
            adjustments.append({"first_time_customer": adjustment})
            final_score += adjustment
        
        # High credit limit request adjustment
        requested_limit = application_data.get('requested_limit', 0)
        annual_income = customer_data.get('personalInfo', {}).get('annualIncome', 0)
        
        if annual_income > 0:
            limit_to_income_ratio = requested_limit / annual_income
            if limit_to_income_ratio > 0.5:  # Requesting more than 50% of annual income
                adjustment = base_score * 0.15
                adjustments.append({"high_limit_request": adjustment})
                final_score += adjustment
        
        # Multiple high-severity risk factors
        high_severity_count = len([rf for rf in risk_factors if rf.severity == "HIGH"])
        critical_severity_count = len([rf for rf in risk_factors if rf.severity == "CRITICAL"])
        
        if critical_severity_count > 0:
            adjustment = base_score * 0.25 * critical_severity_count
            adjustments.append({"critical_risk_factors": adjustment})
            final_score += adjustment
        elif high_severity_count > 2:
            adjustment = base_score * 0.12 * (high_severity_count - 2)
            adjustments.append({"multiple_high_risks": adjustment})
            final_score += adjustment
        
        # Cap the score at 100
        final_score = min(100, max(0, final_score))
        
        return final_score, adjustments
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from numeric score"""
        
        if risk_score >= 75:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_confidence_score(
        self,
        customer_data: Dict[str, Any],
        bureau_data: Dict[str, Any] = None,
        risk_factors: List[RiskFactor] = None
    ) -> float:
        """Calculate confidence in the risk assessment"""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on data completeness
        if customer_data.get('personalInfo', {}).get('annualIncome', 0) > 0:
            confidence += 0.1
        
        if customer_data.get('personalInfo', {}).get('employmentYears', 0) > 0:
            confidence += 0.1
        
        if bureau_data:
            confidence += 0.2  # Credit bureau data significantly increases confidence
            
            if bureau_data.get('accounts', []):
                confidence += 0.1  # Account history available
            
            if bureau_data.get('credit_score', 0) > 0:
                confidence += 0.1  # Credit score available
        
        # Reduce confidence for inconsistencies or missing data
        if not customer_data.get('personalInfo', {}).get('occupation'):
            confidence -= 0.05
        
        if risk_factors:
            critical_count = len([rf for rf in risk_factors if rf.severity == "CRITICAL"])
            if critical_count > 0:
                confidence += 0.05 * critical_count  # More certain about high-risk cases
        
        return min(1.0, max(0.1, confidence))
    
    def _generate_risk_recommendations(
        self,
        risk_factors: List[RiskFactor],
        risk_level: RiskLevel
    ) -> List[str]:
        """Generate actionable risk recommendations"""
        
        recommendations = []
        
        # Risk level specific recommendations
        if risk_level == RiskLevel.CRITICAL:
            recommendations.extend([
                "Strongly recommend denial of credit application",
                "If approved, implement maximum monitoring and lowest possible limits",
                "Require co-signer or secured collateral",
                "Manual review required for any credit decisions"
            ])
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "Consider denial or approve with strict conditions",
                "Implement enhanced monitoring and fraud detection",
                "Lower credit limits significantly below requested amount",
                "Require additional income verification"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "Approve with standard to conservative terms",
                "Implement regular account monitoring",
                "Consider graduated credit limit increases based on performance"
            ])
        else:  # LOW risk
            recommendations.extend([
                "Eligible for standard or premium credit products",
                "Consider competitive rates and higher credit limits",
                "Good candidate for relationship banking products"
            ])
        
        # Factor-specific recommendations
        factor_recommendations = set()
        for factor in risk_factors:
            if factor.recommendation and factor.recommendation not in factor_recommendations:
                factor_recommendations.add(factor.recommendation)
        
        recommendations.extend(list(factor_recommendations)[:5])  # Top 5 unique recommendations
        
        return recommendations
    
    def _is_recent_inquiry(self, inquiry_date: str, months: int = 6) -> bool:
        """Check if credit inquiry is within recent months"""
        
        try:
            if not inquiry_date:
                return False
            
            inquiry_dt = datetime.fromisoformat(inquiry_date.replace('Z', '+00:00'))
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            return inquiry_dt >= cutoff_date
        except:
            return False
    
    def _is_recent_account(self, opened_date: str, months: int = 12) -> bool:
        """Check if account was opened within recent months"""
        
        try:
            if not opened_date:
                return False
            
            opened_dt = datetime.fromisoformat(opened_date.replace('Z', '+00:00'))
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            return opened_dt >= cutoff_date
        except:
            return False
    
    def _is_first_time_customer(self, customer_data: Dict[str, Any]) -> bool:
        """Determine if this is a first-time customer"""
        
        # Simple heuristic - in production would check against customer database
        financial_profile = customer_data.get('financialProfile', {})
        credit_score = financial_profile.get('creditScore', 0)
        
        # If credit score is very low or missing, likely first-time customer
        return credit_score < 600 or credit_score == 0
    
    def calculate_simple_risk_score(
        self,
        credit_score: int,
        annual_income: float,
        debt_to_income: float,
        employment_years: float
    ) -> Dict[str, Any]:
        """
        Calculate simplified risk score for quick assessments
        
        Args:
            credit_score: FICO credit score
            annual_income: Annual income in dollars
            debt_to_income: Debt-to-income ratio (0-1)
            employment_years: Years of employment
            
        Returns:
            Simplified risk assessment
        """
        
        # Simple scoring algorithm
        base_score = 50
        
        # Credit score component (40% weight)
        if credit_score >= 750:
            credit_component = -20
        elif credit_score >= 700:
            credit_component = -10
        elif credit_score >= 650:
            credit_component = 0
        elif credit_score >= 600:
            credit_component = 15
        else:
            credit_component = 30
        
        # Income component (25% weight)
        if annual_income >= 75000:
            income_component = -10
        elif annual_income >= 50000:
            income_component = -5
        elif annual_income >= 30000:
            income_component = 0
        else:
            income_component = 10
        
        # DTI component (25% weight)
        if debt_to_income <= 0.2:
            dti_component = -10
        elif debt_to_income <= 0.3:
            dti_component = -5
        elif debt_to_income <= 0.4:
            dti_component = 0
        elif debt_to_income <= 0.5:
            dti_component = 10
        else:
            dti_component = 20
        
        # Employment component (10% weight)
        if employment_years >= 5:
            employment_component = -5
        elif employment_years >= 2:
            employment_component = 0
        elif employment_years >= 1:
            employment_component = 5
        else:
            employment_component = 10
        
        # Calculate final score
        final_score = base_score + credit_component + income_component + dti_component + employment_component
        final_score = max(0, min(100, final_score))
        
        # Determine risk level
        risk_level = self._determine_risk_level(final_score)
        
        return {
            'risk_score': final_score,
            'risk_level': risk_level.value,
            'components': {
                'credit_score': credit_component,
                'income': income_component,
                'debt_to_income': dti_component,
                'employment': employment_component
            },
            'calculation_type': 'simplified',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the risk model"""
        
        return {
            'model_version': self.model_version,
            'scoring_weights': self.scoring_weights,
            'component_count': len(self.scoring_weights),
            'risk_levels': [level.value for level in RiskLevel],
            'last_updated': datetime.now().isoformat(),
            'features': [
                'Credit score analysis',
                'Financial stability assessment',
                'Behavioral pattern detection',
                'Demographic risk factors',
                'External market factors',
                'Fraud risk indicators',
                'Employment stability analysis',
                'Geographic risk assessment'
            ]
        }
    
    def __str__(self):
        return f"RiskCalculator(version={self.model_version}, components={len(self.scoring_weights)})"