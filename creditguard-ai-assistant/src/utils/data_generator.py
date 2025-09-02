#!/usr/bin/env python3
"""
🏦 CreditGuard AI Assistant - Synthetic Data Generator
👨‍💼 Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
📅 Version: 1.0.0
🎯 Purpose: Generate realistic synthetic data for credit risk analysis training
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse
import logging
from pathlib import Path
import pandas as pd
from faker import Faker
import numpy as np
from dataclasses import dataclass, asdict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Faker for realistic data generation
fake = Faker('en_US')
Faker.seed(42)  # For reproducible results
random.seed(42)
np.random.seed(42)

@dataclass
class PersonalInfo:
    """Personal information structure"""
    firstName: str
    lastName: str
    age: int
    dateOfBirth: str
    ssn: str
    occupation: str
    annualIncome: int
    employmentYears: int
    education: str
    maritalStatus: str
    dependents: int

@dataclass
class AddressInfo:
    """Address information structure"""
    street: str
    city: str
    state: str
    zipCode: str
    country: str
    yearsAtAddress: int
    homeOwnership: str
    monthlyRent: Optional[int]
    monthlyMortgage: Optional[int]

@dataclass
class FinancialProfile:
    """Financial profile structure"""
    currentAccounts: List[str]
    creditHistory: str
    debtToIncome: float
    paymentHistory: str
    bankruptcyHistory: bool
    creditScore: int
    existingCreditCards: int
    totalCreditLimit: int
    totalDebt: int
    monthlyExpenses: int
    savingsAccount: int
    checkingAccount: int

@dataclass
class RiskFactors:
    """Risk assessment factors"""
    addressStability: str
    incomeVerification: str
    previousApplications: int
    fraudAlerts: bool
    identityVerified: bool
    phoneVerified: bool
    emailVerified: bool
    employmentVerified: bool

@dataclass
class Customer:
    """Complete customer profile"""
    customerId: str
    personalInfo: PersonalInfo
    addressInfo: AddressInfo
    financialProfile: FinancialProfile
    riskFactors: RiskFactors
    createdDate: str
    lastUpdated: str
    customerSegment: str
    riskScore: float

class DataGenerator:
    """Main data generator class"""
    
    def __init__(self):
        self.customers = []
        self.credit_products = []
        self.applications = []
        
        # Industry data for realistic generation
        self.occupations = [
            "Software Engineer", "Teacher", "Nurse", "Manager", "Sales Representative",
            "Accountant", "Engineer", "Doctor", "Lawyer", "Consultant",
            "Marketing Manager", "Data Analyst", "Project Manager", "Designer",
            "Customer Service Representative", "Mechanic", "Electrician", "Plumber",
            "Real Estate Agent", "Financial Advisor", "Restaurant Manager",
            "Administrative Assistant", "HR Specialist", "Operations Manager",
            "Business Analyst", "IT Support", "Pharmacist", "Social Worker"
        ]
        
        self.education_levels = [
            "High School", "Some College", "Associate's", "Bachelor's", 
            "Master's", "Doctorate", "Professional"
        ]
        
        self.marital_statuses = ["Single", "Married", "Divorced", "Widowed"]
        
        self.credit_histories = ["Excellent", "Good", "Fair", "Poor", "No History"]
        
        self.payment_histories = ["Excellent", "Good", "Fair", "Poor"]
        
        self.home_ownerships = ["Own", "Rent", "Live with Family", "Other"]
        
        # US States for realistic addresses
        self.us_states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]

    def generate_personal_info(self) -> PersonalInfo:
        """Generate realistic personal information"""
        first_name = fake.first_name()
        last_name = fake.last_name()
        age = random.randint(18, 75)
        date_of_birth = fake.date_of_birth(minimum_age=age, maximum_age=age).isoformat()
        
        # Generate realistic income based on occupation and age
        occupation = random.choice(self.occupations)
        base_income = self._get_base_income_for_occupation(occupation)
        age_multiplier = min(1.0 + (age - 25) * 0.02, 2.0)  # Income increases with age
        annual_income = int(base_income * age_multiplier * random.uniform(0.8, 1.3))
        
        return PersonalInfo(
            firstName=first_name,
            lastName=last_name,
            age=age,
            dateOfBirth=date_of_birth,
            ssn=fake.ssn(),
            occupation=occupation,
            annualIncome=annual_income,
            employmentYears=random.randint(1, min(age - 18, 25)),
            education=random.choice(self.education_levels),
            maritalStatus=random.choice(self.marital_statuses),
            dependents=random.choices([0, 1, 2, 3, 4], weights=[40, 25, 20, 10, 5])[0]
        )

    def _get_base_income_for_occupation(self, occupation: str) -> int:
        """Get realistic base income for occupation"""
        income_map = {
            "Doctor": 200000, "Lawyer": 150000, "Software Engineer": 95000,
            "Engineer": 85000, "Financial Advisor": 80000, "Manager": 75000,
            "Consultant": 85000, "Pharmacist": 120000, "Data Analyst": 70000,
            "Accountant": 60000, "Marketing Manager": 70000, "Project Manager": 85000,
            "Business Analyst": 75000, "Operations Manager": 80000,
            "Real Estate Agent": 55000, "Designer": 55000, "IT Support": 55000,
            "Teacher": 50000, "Nurse": 65000, "HR Specialist": 60000,
            "Sales Representative": 50000, "Administrative Assistant": 40000,
            "Customer Service Representative": 35000, "Social Worker": 45000,
            "Mechanic": 45000, "Electrician": 55000, "Plumber": 55000,
            "Restaurant Manager": 45000
        }
        return income_map.get(occupation, 50000)

    def generate_address_info(self, income: int) -> AddressInfo:
        """Generate realistic address information based on income"""
        state = random.choice(self.us_states)
        home_ownership = random.choices(
            self.home_ownerships,
            weights=[30, 50, 15, 5] if income < 50000 else [60, 30, 5, 5]
        )[0]
        
        monthly_rent = None
        monthly_mortgage = None
        
        if home_ownership == "Rent":
            monthly_rent = int(income * random.uniform(0.2, 0.35) / 12)
        elif home_ownership == "Own":
            monthly_mortgage = int(income * random.uniform(0.15, 0.28) / 12)
        
        return AddressInfo(
            street=fake.street_address(),
            city=fake.city(),
            state=state,
            zipCode=fake.zipcode(),
            country="USA",
            yearsAtAddress=random.randint(1, 15),
            homeOwnership=home_ownership,
            monthlyRent=monthly_rent,
            monthlyMortgage=monthly_mortgage
        )

    def generate_financial_profile(self, personal_info: PersonalInfo, address_info: AddressInfo) -> FinancialProfile:
        """Generate realistic financial profile"""
        # Credit score influenced by age, income, and employment history
        base_score = 650
        age_bonus = min((personal_info.age - 25) * 3, 100)
        income_bonus = min((personal_info.annualIncome - 30000) / 1000, 50)
        employment_bonus = min(personal_info.employmentYears * 5, 50)
        
        credit_score = int(base_score + age_bonus + income_bonus + employment_bonus + random.randint(-50, 50))
        credit_score = max(300, min(850, credit_score))  # Keep within valid range
        
        # Other financial metrics based on credit score
        if credit_score >= 750:
            credit_history = "Excellent"
            payment_history = "Excellent"
            debt_to_income = random.uniform(0.1, 0.3)
        elif credit_score >= 700:
            credit_history = "Good"
            payment_history = random.choice(["Good", "Excellent"])
            debt_to_income = random.uniform(0.2, 0.4)
        elif credit_score >= 650:
            credit_history = "Fair"
            payment_history = "Good"
            debt_to_income = random.uniform(0.3, 0.5)
        else:
            credit_history = "Poor"
            payment_history = random.choice(["Fair", "Poor"])
            debt_to_income = random.uniform(0.4, 0.6)
        
        existing_cards = random.choices([0, 1, 2, 3, 4, 5], weights=[10, 30, 25, 20, 10, 5])[0]
        total_credit_limit = existing_cards * random.randint(2000, 15000) if existing_cards > 0 else 0
        total_debt = int(total_credit_limit * debt_to_income) if total_credit_limit > 0 else 0
        
        monthly_expenses = int(personal_info.annualIncome * 0.6 / 12)  # 60% of income for expenses
        savings = int(personal_info.annualIncome * random.uniform(0.05, 0.25))
        checking = int(monthly_expenses * random.uniform(1.5, 3.0))
        
        return FinancialProfile(
            currentAccounts=random.sample(["checking", "savings", "money_market", "cd"], k=random.randint(1, 3)),
            creditHistory=credit_history,
            debtToIncome=round(debt_to_income, 2),
            paymentHistory=payment_history,
            bankruptcyHistory=random.choices([True, False], weights=[5, 95])[0],
            creditScore=credit_score,
            existingCreditCards=existing_cards,
            totalCreditLimit=total_credit_limit,
            totalDebt=total_debt,
            monthlyExpenses=monthly_expenses,
            savingsAccount=savings,
            checkingAccount=checking
        )

    def generate_risk_factors(self, address_info: AddressInfo, financial_profile: FinancialProfile) -> RiskFactors:
        """Generate risk assessment factors"""
        stability = "High" if address_info.yearsAtAddress >= 5 else "Medium" if address_info.yearsAtAddress >= 2 else "Low"
        
        return RiskFactors(
            addressStability=stability,
            incomeVerification=random.choices(["Verified", "Pending", "Failed"], weights=[85, 10, 5])[0],
            previousApplications=random.choices([0, 1, 2, 3], weights=[60, 25, 10, 5])[0],
            fraudAlerts=random.choices([True, False], weights=[2, 98])[0],
            identityVerified=random.choices([True, False], weights=[95, 5])[0],
            phoneVerified=random.choices([True, False], weights=[90, 10])[0],
            emailVerified=random.choices([True, False], weights=[85, 15])[0],
            employmentVerified=random.choices([True, False], weights=[80, 20])[0]
        )

    def calculate_risk_score(self, customer: Customer) -> float:
        """Calculate composite risk score (0-100, lower is better)"""
        score = 50.0  # Base score
        
        # Credit score impact (most important factor)
        if customer.financialProfile.creditScore >= 750:
            score -= 20
        elif customer.financialProfile.creditScore >= 700:
            score -= 10
        elif customer.financialProfile.creditScore >= 650:
            score += 0
        else:
            score += 20
        
        # Income stability
        if customer.personalInfo.annualIncome >= 75000:
            score -= 10
        elif customer.personalInfo.annualIncome < 30000:
            score += 15
        
        # Employment history
        if customer.personalInfo.employmentYears >= 5:
            score -= 5
        elif customer.personalInfo.employmentYears < 2:
            score += 10
        
        # Debt to income ratio
        if customer.financialProfile.debtToIncome <= 0.3:
            score -= 5
        elif customer.financialProfile.debtToIncome >= 0.5:
            score += 15
        
        # Address stability
        if customer.addressInfo.yearsAtAddress >= 5:
            score -= 5
        elif customer.addressInfo.yearsAtAddress < 2:
            score += 5
        
        # Fraud alerts and verification issues
        if customer.riskFactors.fraudAlerts:
            score += 25
        if not customer.riskFactors.identityVerified:
            score += 20
        if not customer.riskFactors.employmentVerified:
            score += 10
        
        # Previous applications (too many is suspicious)
        score += customer.riskFactors.previousApplications * 5
        
        # Bankruptcy history
        if customer.financialProfile.bankruptcyHistory:
            score += 30
        
        return max(0.0, min(100.0, round(score, 1)))

    def determine_customer_segment(self, customer: Customer) -> str:
        """Determine customer segment based on risk and income"""
        risk_score = customer.riskScore
        income = customer.personalInfo.annualIncome
        credit_score = customer.financialProfile.creditScore
        
        if credit_score >= 750 and income >= 75000 and risk_score <= 25:
            return "Premium"
        elif credit_score >= 700 and income >= 50000 and risk_score <= 35:
            return "Preferred"
        elif credit_score >= 650 and risk_score <= 50:
            return "Standard"
        elif credit_score >= 600 and risk_score <= 65:
            return "Subprime"
        else:
            return "High Risk"

    def generate_customers(self, count: int = 1000) -> List[Customer]:
        """Generate specified number of realistic customers"""
        logger.info(f"🏦 Generating {count} customer profiles...")
        
        customers = []
        for i in range(count):
            if i % 100 == 0:
                logger.info(f"Generated {i}/{count} customers...")
            
            customer_id = f"CUST_{str(i+1).zfill(4)}"
            
            personal_info = self.generate_personal_info()
            address_info = self.generate_address_info(personal_info.annualIncome)
            financial_profile = self.generate_financial_profile(personal_info, address_info)
            risk_factors = self.generate_risk_factors(address_info, financial_profile)
            
            # Create customer object
            customer = Customer(
                customerId=customer_id,
                personalInfo=personal_info,
                addressInfo=address_info,
                financialProfile=financial_profile,
                riskFactors=risk_factors,
                createdDate=fake.date_time_between(start_date='-2y', end_date='now').isoformat(),
                lastUpdated=datetime.now().isoformat(),
                customerSegment="",  # Will be set after risk calculation
                riskScore=0.0  # Will be calculated
            )
            
            # Calculate risk score and segment
            customer.riskScore = self.calculate_risk_score(customer)
            customer.customerSegment = self.determine_customer_segment(customer)
            
            customers.append(customer)
        
        logger.info(f"✅ Successfully generated {len(customers)} customer profiles")
        return customers

    def generate_credit_products(self) -> List[Dict[str, Any]]:
        """Generate credit card product catalog"""
        logger.info("💳 Generating credit card products...")
        
        products = [
            {
                "productId": "PLATINUM_001",
                "name": "Platinum Rewards Card",
                "category": "premium",
                "description": "Premium rewards card with travel benefits and high credit limits",
                "requirements": {
                    "minimumIncome": 70000,
                    "minimumCreditScore": 750,
                    "employmentStatus": "full-time",
                    "debtToIncomeMax": 0.40,
                    "minimumAge": 21
                },
                "benefits": {
                    "creditLimit": {"min": 10000, "max": 50000},
                    "apr": 16.99,
                    "rewardsRate": 0.02,
                    "annualFee": 95,
                    "introOffers": {
                        "aprMonths": 12,
                        "aprRate": 0.0,
                        "bonusPoints": 50000,
                        "spendRequirement": 3000
                    },
                    "benefits": ["Airport lounge access", "Travel insurance", "Concierge service"]
                },
                "targetSegments": ["Premium", "Preferred"],
                "riskTolerance": "Low",
                "active": True
            },
            {
                "productId": "GOLD_002",
                "name": "Gold Cashback Card",
                "category": "standard",
                "description": "Solid rewards card with cashback on everyday purchases",
                "requirements": {
                    "minimumIncome": 45000,
                    "minimumCreditScore": 700,
                    "employmentStatus": "full-time",
                    "debtToIncomeMax": 0.45,
                    "minimumAge": 21
                },
                "benefits": {
                    "creditLimit": {"min": 5000, "max": 25000},
                    "apr": 19.99,
                    "rewardsRate": 0.015,
                    "annualFee": 0,
                    "introOffers": {
                        "aprMonths": 15,
                        "aprRate": 0.0,
                        "bonusPoints": 25000,
                        "spendRequirement": 2000
                    },
                    "benefits": ["No annual fee", "Cashback rewards", "Purchase protection"]
                },
                "targetSegments": ["Preferred", "Standard"],
                "riskTolerance": "Medium",
                "active": True
            },
            {
                "productId": "STANDARD_003", 
                "name": "Standard Credit Card",
                "category": "basic",
                "description": "Basic credit card for building credit history",
                "requirements": {
                    "minimumIncome": 25000,
                    "minimumCreditScore": 650,
                    "employmentStatus": "any",
                    "debtToIncomeMax": 0.50,
                    "minimumAge": 18
                },
                "benefits": {
                    "creditLimit": {"min": 1000, "max": 10000},
                    "apr": 24.99,
                    "rewardsRate": 0.005,
                    "annualFee": 25,
                    "introOffers": {
                        "aprMonths": 6,
                        "aprRate": 19.99,
                        "bonusPoints": 5000,
                        "spendRequirement": 500
                    },
                    "benefits": ["Credit building", "Basic purchase protection"]
                },
                "targetSegments": ["Standard", "Subprime"],
                "riskTolerance": "Medium",
                "active": True
            },
            {
                "productId": "SECURED_004",
                "name": "Secured Credit Card",
                "category": "secured",
                "description": "Secured card for credit building with deposit requirement",
                "requirements": {
                    "minimumIncome": 15000,
                    "minimumCreditScore": 0,
                    "employmentStatus": "any",
                    "debtToIncomeMax": 1.0,
                    "minimumAge": 18,
                    "securityDeposit": {"min": 200, "max": 5000}
                },
                "benefits": {
                    "creditLimit": {"min": 200, "max": 5000},
                    "apr": 29.99,
                    "rewardsRate": 0.0,
                    "annualFee": 39,
                    "introOffers": None,
                    "benefits": ["Credit building", "Graduation to unsecured card"]
                },
                "targetSegments": ["Subprime", "High Risk"],
                "riskTolerance": "High",
                "active": True
            }
        ]
        
        logger.info(f"✅ Generated {len(products)} credit card products")
        return products

    def generate_applications(self, customers: List[Customer], products: List[Dict], count: int = 500) -> List[Dict[str, Any]]:
        """Generate credit card applications"""
        logger.info(f"📋 Generating {count} credit card applications...")
        
        applications = []
        statuses = ["Pending", "Approved", "Denied", "Under Review"]
        
        for i in range(count):
            customer = random.choice(customers)
            product = random.choice(products)
            
            # Determine likely outcome based on customer profile and product requirements
            meets_income = customer.personalInfo.annualIncome >= product["requirements"]["minimumIncome"]
            meets_credit_score = customer.financialProfile.creditScore >= product["requirements"]["minimumCreditScore"]
            meets_dti = customer.financialProfile.debtToIncome <= product["requirements"]["debtToIncomeMax"]
            
            # Calculate approval probability
            approval_prob = 0.5  # Base probability
            if meets_income:
                approval_prob += 0.2
            if meets_credit_score:
                approval_prob += 0.25
            if meets_dti:
                approval_prob += 0.15
            if customer.riskFactors.identityVerified and customer.riskFactors.employmentVerified:
                approval_prob += 0.1
            if customer.riskFactors.fraudAlerts:
                approval_prob -= 0.5
            
            # Determine status
            if approval_prob >= 0.8:
                status = "Approved"
                credit_limit = random.randint(
                    product["benefits"]["creditLimit"]["min"],
                    min(product["benefits"]["creditLimit"]["max"], 
                        int(customer.personalInfo.annualIncome * 0.3))
                )
            elif approval_prob >= 0.6:
                status = random.choice(["Approved", "Under Review"])
                credit_limit = random.randint(
                    product["benefits"]["creditLimit"]["min"],
                    int(product["benefits"]["creditLimit"]["max"] * 0.7)
                )
            elif approval_prob >= 0.3:
                status = random.choice(["Under Review", "Denied"])
                credit_limit = None
            else:
                status = "Denied"
                credit_limit = None
            
            application = {
                "applicationId": f"APP_{str(i+1).zfill(6)}",
                "customerId": customer.customerId,
                "productId": product["productId"],
                "applicationDate": fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
                "status": status,
                "requestedLimit": random.randint(5000, 25000),
                "approvedLimit": credit_limit,
                "interestRate": product["benefits"]["apr"] if status == "Approved" else None,
                "applicationChannel": random.choice(["Online", "Phone", "Branch", "Mail"]),
                "processingTime": random.randint(1, 14),  # Days
                "riskScore": customer.riskScore,
                "underwriterNotes": self._generate_underwriter_notes(customer, product, status),
                "lastUpdated": datetime.now().isoformat()
            }
            
            applications.append(application)
        
        logger.info(f"✅ Generated {len(applications)} credit card applications")
        return applications

    def _generate_underwriter_notes(self, customer: Customer, product: Dict, status: str) -> str:
        """Generate realistic underwriter notes"""
        notes = []
        
        if status == "Approved":
            notes.append("Application meets all criteria.")
            if customer.financialProfile.creditScore >= 750:
                notes.append("Excellent credit score.")
            if customer.personalInfo.annualIncome >= 100000:
                notes.append("High income verified.")
        elif status == "Denied":
            if customer.personalInfo.annualIncome < product["requirements"]["minimumIncome"]:
                notes.append("Income below minimum requirement.")
            if customer.financialProfile.creditScore < product["requirements"]["minimumCreditScore"]:
                notes.append("Credit score below threshold.")
            if customer.financialProfile.debtToIncome > product["requirements"]["debtToIncomeMax"]:
                notes.append("DTI ratio too high.")
            if customer.riskFactors.fraudAlerts:
                notes.append("Fraud alerts present.")
        else:
            notes.append("Application requires additional review.")
            if not customer.riskFactors.employmentVerified:
                notes.append("Employment verification pending.")
        
        return " ".join(notes) if notes else "Standard processing."

    def generate_policies_content(self) -> str:
        """Generate credit policies document content"""
        logger.info("📋 Generating credit policies document...")
        
        content = """# FinanceFirst Bank - Credit Card Approval Policies v2.4

## Executive Summary
This document outlines the credit risk assessment and approval policies for FinanceFirst Bank's credit card products. All underwriters and risk analysts must follow these guidelines to ensure consistent and compliant decision-making.

## Risk Assessment Matrix

### Credit Score Tiers
- **Excellent (750+)**: Auto-approve up to $25,000 for qualified applicants
- **Good (700-749)**: Manual review required, approve up to $15,000
- **Fair (650-699)**: Enhanced verification required, approve up to $8,000
- **Poor (600-649)**: Secured products only or decline
- **Very Poor (<600)**: Decline or refer to secured card program

### Income Verification Requirements
- **W2 Employees**: Minimum 2 years employment history, current pay stubs
- **Self-Employed**: 2 years tax returns, bank statements, CPA letter
- **Commission-Based**: 2 years tax returns, average monthly income calculation
- **Minimum DTI Ratio**: 40% or less (total debt payments / gross monthly income)

### Employment Verification
- Contact employer directly or use third-party verification service
- Confirm position title, start date, and current employment status
- Document any recent job changes or gaps in employment

## Product-Specific Guidelines

### Platinum Card ($70K+ income, 750+ score)
- Target market: High-income professionals
- Standard approval: $10,000 - $50,000 credit limit
- Enhanced benefits justify premium requirements
- Manual review for limits above $25,000

### Gold Card ($45K+ income, 700+ score)
- Target market: Middle-income, established credit
- Standard approval: $5,000 - $25,000 credit limit
- Balance transfer offers available to qualified customers

### Standard Card ($25K+ income, 650+ score)
- Entry-level product for credit building
- Standard approval: $1,000 - $10,000 credit limit
- Focus on responsible credit use education

### Secured Card (No minimum score)
- Credit building product requiring security deposit
- Credit limit equals security deposit ($200 - $5,000)
- Graduation to unsecured products after 12 months good standing

## Risk Factors and Red Flags

### High-Risk Indicators
- Bankruptcy within last 7 years
- Multiple recent credit inquiries (6+ in 6 months)
- High DTI ratio (>50%)
- Recent late payments (30+ days in last 6 months)
- Address changes every 6 months
- Income not verifiable through standard channels

### Fraud Prevention
- Verify identity through multiple data sources
- Check for synthetic identity indicators
- Review application velocity and patterns
- Flag applications from high-risk geographic areas

## Compliance Requirements

### Fair Credit Reporting Act (FCRA)
- Obtain written consent before pulling credit reports
- Provide adverse action notices when required
- Maintain records of credit decisions for 25 months

### Equal Credit Opportunity Act (ECOA)
- No discrimination based on protected classes
- Document legitimate business reasons for all credit decisions
- Provide specific reasons for adverse actions

### Bank Secrecy Act (BSA)
- Verify customer identity (CIP requirements)
- Monitor for suspicious activity
- File SARs when appropriate

## Appeal Process
Declined applicants may appeal decisions within 60 days. Appeals must include:
- Updated financial information
- Explanation of circumstances leading to decline
- Supporting documentation

## Quality Assurance
- Random review of 10% of approved applications
- Monthly calibration sessions for underwriters  
- Annual policy review and updates

---
Document Version: 2.4
Last Updated: December 2024
Next Review: June 2025
Approved By: Chief Risk Officer, FinanceFirst Bank
"""
        
        return content

    def generate_procedures_manual(self) -> str:
        """Generate procedures manual content"""
        logger.info("📖 Generating procedures manual...")
        
        content = """# Credit Risk Assessment Procedures Manual
## FinanceFirst Bank - Operations Guide v3.1

### Table of Contents
1. KYC (Know Your Customer) Requirements
2. AML (Anti-Money Laundering) Procedures  
3. Credit Application Processing
4. Fraud Detection Protocols
5. Documentation Standards
6. Escalation Procedures

---

## 1. KYC (Know Your Customer) Requirements

### Primary Identity Verification
**Required Documents (Choose 1):**
- Government-issued photo ID (Driver's license, Passport, State ID)
- Military ID with photo
- Tribal identification with photo

### Address Verification  
**Required Documents (Choose 1):**
- Utility bill (electricity, gas, water) dated within 60 days
- Bank statement dated within 60 days  
- Lease agreement or mortgage statement
- Government correspondence (tax notice, voter registration)

### Income Verification
**W2 Employees:**
- Most recent pay stub showing year-to-date earnings
- W2 from previous tax year
- Employment verification letter from HR

**Self-Employed:**
- Last 2 years tax returns (1040 with Schedule C)
- Profit & Loss statement (current year)
- Bank statements (business and personal, 3 months)
- CPA letter verifying income

**Other Income Sources:**
- Social Security award letter
- Pension/retirement income statements  
- Disability income verification
- Investment income statements

### Employment Verification
1. Contact employer's HR department directly
2. Verify: Position title, start date, employment status, salary
3. Document conversation in customer file
4. For recent employment changes, obtain explanation

---

## 2. AML (Anti-Money Laundering) Procedures

### Customer Due Diligence (CDD)
**Standard CDD Requirements:**
- Verify customer identity using reliable, independent documents
- Verify customer address through acceptable documentation
- Understand the nature and purpose of customer relationships

### Enhanced Due Diligence (EDD)
**Required for:**
- High-risk customers (geographic, occupation, transaction patterns)
- Politically Exposed Persons (PEPs)  
- Customers with suspicious activity history
- Non-resident aliens

### OFAC Screening
- Screen all applicants against OFAC Specially Designated Nationals list
- Use automated screening system with manual review
- Document screening results in customer file
- Escalate any potential matches immediately

### Politically Exposed Persons (PEP) Check
**Screen for:**
- Foreign government officials and their families
- Senior executives of state-owned enterprises
- Prominent political party officials
- Senior judges, prosecutors, military officers

### Sanctions List Verification
**Check against:**
- OFAC Specially Designated Nationals (SDN) List
- OFAC Consolidated Sanctions List  
- BIS Entity List
- State Department sanctions lists

---

## 3. Credit Application Processing

### Application Review Checklist
□ Identity documents reviewed and copies retained
□ Income verification completed and documented
□ Employment verification completed
□ Credit report pulled and reviewed
□ Bank account verification completed
□ Application completeness verified
□ Risk assessment completed
□ Policy compliance verified

### Credit Report Analysis
**Key Areas to Review:**
- Payment history (35% of decision weight)
- Credit utilization (30% of decision weight)  
- Length of credit history (15% of decision weight)
- Types of credit (10% of decision weight)
- Recent credit inquiries (10% of decision weight)

### Decision Matrix
**Auto-Approve Criteria:**
- Credit score 750+
- Income verification completed
- DTI ratio <30%
- No derogatory marks in last 24 months
- Stable employment (2+ years)

**Manual Review Required:**
- Credit score 650-749
- DTI ratio 30-40%
- Recent credit inquiries (3+ in 6 months)
- Employment gaps or recent job changes
- First-time credit applicants

**Auto-Decline Criteria:**
- Credit score <600
- DTI ratio >50%
- Active bankruptcy or recent discharge
- Fraud alerts or identity verification failures
- OFAC match or other sanctions screening hits

---

## 4. Fraud Detection Protocols

### Identity Verification Red Flags
- Mismatched personal information across data sources
- Recently issued Social Security number for older applicant
- Address associated with mail drop or commercial location
- Phone number disconnected or invalid
- Applicant unfamiliar with own credit history details

### Synthetic Identity Indicators
- Thin credit file with few trade lines
- Authorized user accounts that don't match family relationships
- Credit file creation date inconsistent with stated age
- Limited cross-references in public records
- All accounts opened around same time period

### Application Velocity Monitoring  
- Multiple applications from same IP address
- Similar applications with slight variations in personal data
- Applications from same device or browser fingerprint
- Unusual geographic patterns in application submissions

### Device Fingerprinting
- Monitor device characteristics and browser information
- Flag applications from known fraud devices
- Analyze time zones and geographic inconsistencies
- Review session replay for suspicious behavior patterns

---

## 5. Documentation Standards

### File Documentation Requirements
**Every customer file must contain:**
- Completed credit application (original or electronic)
- Identity verification documents (copies)
- Income verification documents (copies)
- Credit report with score (dated within 30 days)
- Decision rationale documentation
- Any correspondence with customer

### Record Retention Schedule
- **Approved Applications**: 7 years from account closure
- **Declined Applications**: 25 months from decision date
- **Fraud Cases**: 7 years from resolution
- **Audit Documentation**: 7 years from audit date

### Electronic Document Standards
- Scan quality minimum 300 DPI
- Files must be searchable PDF format
- File naming convention: CustomerID_DocumentType_Date
- Backup copies maintained in secure location

---

## 6. Escalation Procedures

### Management Escalation Triggers
- Credit limit requests >$25,000
- Applications with policy exceptions
- Fraud investigations
- Customer complaints about credit decisions
- Regulatory compliance issues

### Escalation Contacts
**Level 1 - Senior Underwriter**
- Credit limit exceptions up to $35,000
- Policy interpretation questions
- Complex income verification cases

**Level 2 - Credit Manager**  
- Credit limit exceptions up to $50,000
- Policy exceptions requiring management approval
- Fraud case coordination

**Level 3 - Chief Risk Officer**
- Credit limits >$50,000
- Significant policy changes
- Regulatory examination issues
- Major fraud cases

### Documentation Requirements
- Document reason for escalation
- Include all supporting materials
- Note management decision and rationale
- Update customer file with final decision

---

## Emergency Procedures

### System Outages
- Use manual credit application backup process
- Obtain verbal approvals for time-sensitive applications
- Document all manual decisions for later system entry
- Notify IT and management immediately

### Fraud Emergencies
- Immediately escalate to security team
- Document all evidence and suspicious activity
- Contact law enforcement if criminal activity suspected
- Notify customers if their information may be compromised

---

**Document Information:**
- Version: 3.1
- Last Updated: December 2024
- Next Review: March 2025  
- Document Owner: Operations Manager
- Approved By: Chief Risk Officer
"""
        
        return content

    def save_data_to_files(self, customers: List[Customer], products: List[Dict], applications: List[Dict]):
        """Save all generated data to files"""
        logger.info("💾 Saving generated data to files...")
        
        # Create data directory if it doesn't exist
        data_dir = Path("../data")
        data_dir.mkdir(exist_ok=True)
        
        # Save customers data
        customers_dict = [asdict(customer) for customer in customers]
        with open(data_dir / "sample-customers.json", "w") as f:
            json.dump(customers_dict, f, indent=2, default=str)
        logger.info(f"✅ Saved {len(customers)} customers to sample-customers.json")
        
        # Save products data
        with open(data_dir / "bank-products.json", "w") as f:
            json.dump(products, f, indent=2)
        logger.info(f"✅ Saved {len(products)} products to bank-products.json")
        
        # Save applications data
        with open(data_dir / "credit-applications.json", "w") as f:
            json.dump(applications, f, indent=2, default=str)
        logger.info(f"✅ Saved {len(applications)} applications to credit-applications.json")
        
        # Save policies document
        policies_content = self.generate_policies_content()
        with open(data_dir / "credit-policies.md", "w") as f:
            f.write(policies_content)
        logger.info("✅ Saved credit policies to credit-policies.md")
        
        # Save procedures manual
        procedures_content = self.generate_procedures_manual()
        with open(data_dir / "procedures-manual.md", "w") as f:
            f.write(procedures_content)
        logger.info("✅ Saved procedures manual to procedures-manual.md")

    def generate_summary_stats(self, customers: List[Customer], applications: List[Dict]):
        """Generate and display summary statistics"""
        logger.info("📊 Generating summary statistics...")
        
        # Customer statistics
        segments = {}
        risk_levels = {"Low": 0, "Medium": 0, "High": 0}
        income_brackets = {"<30K": 0, "30K-50K": 0, "50K-75K": 0, "75K+": 0}
        
        for customer in customers:
            # Segment distribution
            segment = customer.customerSegment
            segments[segment] = segments.get(segment, 0) + 1
            
            # Risk level distribution
            if customer.riskScore <= 30:
                risk_levels["Low"] += 1
            elif customer.riskScore <= 60:
                risk_levels["Medium"] += 1
            else:
                risk_levels["High"] += 1
            
            # Income distribution
            income = customer.personalInfo.annualIncome
            if income < 30000:
                income_brackets["<30K"] += 1
            elif income < 50000:
                income_brackets["30K-50K"] += 1
            elif income < 75000:
                income_brackets["50K-75K"] += 1
            else:
                income_brackets["75K+"] += 1
        
        # Application statistics
        app_statuses = {}
        for app in applications:
            status = app["status"]
            app_statuses[status] = app_statuses.get(status, 0) + 1
        
        # Display statistics
        print("\n" + "="*50)
        print("🏦 CREDITGUARD DATA GENERATION SUMMARY")
        print("="*50)
        
        print(f"\n👥 Customer Statistics ({len(customers)} total):")
        print("-" * 30)
        for segment, count in segments.items():
            percentage = (count / len(customers)) * 100
            print(f"  {segment}: {count} ({percentage:.1f}%)")
        
        print(f"\n⚠️  Risk Distribution:")
        print("-" * 30)
        for level, count in risk_levels.items():
            percentage = (count / len(customers)) * 100
            print(f"  {level} Risk: {count} ({percentage:.1f}%)")
        
        print(f"\n💰 Income Distribution:")
        print("-" * 30)
        for bracket, count in income_brackets.items():
            percentage = (count / len(customers)) * 100
            print(f"  {bracket}: {count} ({percentage:.1f}%)")
        
        print(f"\n📋 Application Statistics ({len(applications)} total):")
        print("-" * 30)
        for status, count in app_statuses.items():
            percentage = (count / len(applications)) * 100
            print(f"  {status}: {count} ({percentage:.1f}%)")
        
        print("\n" + "="*50)
        print("✅ Data generation completed successfully!")
        print("📁 Files saved to ../data/ directory")
        print("🚀 Ready for CreditGuard AI Assistant development")
        print("="*50)


def main():
    """Main function to generate all synthetic data"""
    parser = argparse.ArgumentParser(description="CreditGuard AI Assistant - Synthetic Data Generator")
    parser.add_argument("--customers", type=int, default=1000, help="Number of customers to generate")
    parser.add_argument("--applications", type=int, default=500, help="Number of applications to generate")
    parser.add_argument("--generate-all", action="store_true", help="Generate all datasets")
    parser.add_argument("--verify-data", action="store_true", help="Verify generated data")
    
    args = parser.parse_args()
    
    generator = DataGenerator()
    
    if args.verify_data:
        # Verify existing data files
        data_dir = Path("../data")
        files_to_check = [
            "sample-customers.json",
            "bank-products.json", 
            "credit-applications.json",
            "credit-policies.md",
            "procedures-manual.md"
        ]
        
        print("🔍 Verifying data files...")
        for file_name in files_to_check:
            file_path = data_dir / file_name
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"✅ {file_name}: {file_size:,} bytes")
            else:
                print(f"❌ {file_name}: Missing")
        return
    
    if args.generate_all:
        # Generate all datasets
        print("🏦 Starting complete CreditGuard data generation...")
        print("👨‍💼 Instructor: Steven Uba - Azure Digital Solution Engineer")
        print("="*60)
        
        # Generate customers
        customers = generator.generate_customers(args.customers)
        generator.customers = customers
        
        # Generate products
        products = generator.generate_credit_products()
        generator.credit_products = products
        
        # Generate applications
        applications = generator.generate_applications(customers, products, args.applications)
        generator.applications = applications
        
        # Save all data
        generator.save_data_to_files(customers, products, applications)
        
        # Generate summary statistics
        generator.generate_summary_stats(customers, applications)
        
    else:
        print("Use --generate-all to generate complete dataset")
        print("Use --verify-data to check existing data files")


if __name__ == "__main__":
    main()