#!/usr/bin/env python3
"""
CreditGuard AI Assistant - Market Research Plugin
Instructor: Steven Uba - Azure Digital Solution Engineer - Data and AI
Version: 1.0.0
Purpose: Research current fraud trends and market intelligence using Bing Search API
"""

import asyncio
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
import re
from urllib.parse import quote_plus


@dataclass
class NewsArticle:
    """News article structure"""
    title: str
    url: str
    description: str
    published_date: str
    source: str
    relevance_score: float
    sentiment: str
    key_insights: List[str]


@dataclass
class FraudTrend:
    """Fraud trend analysis structure"""
    trend_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    affected_demographics: List[str]
    prevention_strategies: List[str]
    impact_description: str
    data_sources: List[str]
    confidence_level: float


@dataclass
class MarketIntelligence:
    """Market intelligence summary"""
    search_query: str
    search_timestamp: str
    total_results: int
    relevant_articles: List[NewsArticle]
    identified_trends: List[FraudTrend]
    risk_indicators: List[str]
    recommendations: List[str]
    intelligence_summary: str


class MarketResearchPlugin:
    """
    Market Research Plugin for CreditGuard AI Assistant
    
    Uses Bing Search API to gather real-time intelligence on:
    - Credit card fraud trends
    - Identity theft patterns
    - Regulatory changes
    - Industry best practices
    - Economic indicators affecting credit risk
    """
    
    def __init__(
        self, 
        bing_api_key: str,
        max_results: int = 20,
        api_timeout: float = 10.0
    ):
        self.bing_api_key = bing_api_key
        self.max_results = max_results
        self.api_timeout = api_timeout
        self.logger = logging.getLogger(__name__)
        
        # Bing Search API configuration
        self.bing_endpoint = "https://api.bing.microsoft.com/v7.0/search"
        self.news_endpoint = "https://api.bing.microsoft.com/v7.0/news/search"
        
        # Headers for Bing API
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.bing_api_key,
            'Content-Type': 'application/json'
        }
        
        # Search categories and keywords
        self.fraud_keywords = {
            'credit_card_fraud': [
                'credit card fraud 2024', 'payment card fraud trends', 'card skimming',
                'EMV fraud', 'card-not-present fraud', 'synthetic identity fraud'
            ],
            'identity_theft': [
                'identity theft statistics', 'social security fraud', 'account takeover',
                'identity verification fraud', 'synthetic identity creation'
            ],
            'digital_fraud': [
                'online fraud trends', 'mobile payment fraud', 'digital wallet fraud',
                'cryptocurrency fraud', 'phishing attacks financial'
            ],
            'regulatory_updates': [
                'CFPB credit regulations', 'banking compliance updates', 'FCRA updates',
                'credit reporting regulations', 'consumer protection laws'
            ]
        }
        
        # Cache for search results
        self._cache = {}
        
        self.logger.info("MarketResearchPlugin initialized")
    
    async def search_fraud_trends(
        self, 
        query: str,
        time_filter: str = "month",
        market_filter: str = "US"
    ) -> List[Dict[str, Any]]:
        """
        Search for current fraud trends and patterns
        
        Args:
            query: Search query for fraud trends
            time_filter: Time filter (day, week, month, year)
            market_filter: Market/region filter
            
        Returns:
            List of relevant fraud trend insights
        """
        self.logger.info(f"Searching fraud trends for query: {query}")
        
        try:
            # Check cache first
            cache_key = f"fraud_trends_{hash(query)}_{time_filter}"
            if cache_key in self._cache:
                cache_age = datetime.now() - self._cache[cache_key]['timestamp']
                if cache_age < timedelta(hours=6):  # Cache for 6 hours
                    self.logger.info("Returning cached fraud trends")
                    return self._cache[cache_key]['data']
            
            # Perform comprehensive search
            all_results = []
            
            # Search news articles
            news_results = await self._search_news(query, time_filter)
            all_results.extend(news_results)
            
            # Search web for additional insights
            web_results = await self._search_web(query, time_filter)
            all_results.extend(web_results)
            
            # Process and analyze results
            intelligence = await self._analyze_search_results(query, all_results)
            
            # Extract actionable insights
            fraud_insights = self._extract_fraud_insights(intelligence)
            
            # Cache the results
            self._cache[cache_key] = {
                'data': fraud_insights,
                'timestamp': datetime.now()
            }
            
            self.logger.info(f"Found {len(fraud_insights)} fraud trend insights")
            return fraud_insights
            
        except Exception as e:
            self.logger.error(f"Error searching fraud trends: {str(e)}")
            # Return fallback insights if API fails
            return self._get_fallback_insights(query)
    
    async def get_industry_benchmarks(
        self, 
        metric_type: str,
        industry: str = "banking"
    ) -> Dict[str, Any]:
        """
        Get industry benchmarks and statistics
        
        Args:
            metric_type: Type of benchmark (fraud_rates, approval_rates, etc.)
            industry: Industry segment
            
        Returns:
            Industry benchmark data
        """
        self.logger.info(f"Getting industry benchmarks for: {metric_type}")
        
        try:
            # Construct targeted search query
            query = f"{industry} {metric_type} industry benchmark statistics 2024"
            
            # Search for industry data
            search_results = await self._search_web(query, "year")
            
            # Process benchmarks
            benchmarks = self._process_benchmark_data(search_results, metric_type)
            
            return benchmarks
            
        except Exception as e:
            self.logger.error(f"Error getting industry benchmarks: {str(e)}")
            return self._get_fallback_benchmarks(metric_type)
    
    async def monitor_regulatory_changes(
        self, 
        regulation_type: str = "credit_reporting"
    ) -> List[Dict[str, Any]]:
        """
        Monitor for recent regulatory changes affecting credit decisions
        
        Args:
            regulation_type: Type of regulation to monitor
            
        Returns:
            List of recent regulatory updates
        """
        self.logger.info(f"Monitoring regulatory changes for: {regulation_type}")
        
        try:
            # Search for regulatory updates
            regulatory_queries = [
                f"CFPB {regulation_type} new rules 2024",
                f"Federal Reserve {regulation_type} guidelines",
                f"FCRA amendments {datetime.now().year}",
                f"credit bureau regulations updates"
            ]
            
            all_updates = []
            
            for query in regulatory_queries:
                results = await self._search_news(query, "month")
                all_updates.extend(results)
            
            # Process regulatory updates
            processed_updates = self._process_regulatory_updates(all_updates)
            
            return processed_updates
            
        except Exception as e:
            self.logger.error(f"Error monitoring regulatory changes: {str(e)}")
            return []
    
    async def analyze_economic_indicators(
        self, 
        indicators: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze economic indicators affecting credit risk
        
        Args:
            indicators: List of economic indicators to analyze
            
        Returns:
            Economic analysis relevant to credit risk
        """
        if indicators is None:
            indicators = [
                "unemployment rate", "inflation rate", "interest rates",
                "consumer confidence", "housing market", "stock market volatility"
            ]
        
        self.logger.info(f"Analyzing economic indicators: {indicators}")
        
        try:
            economic_data = {}
            
            for indicator in indicators:
                query = f"{indicator} current trends impact credit risk 2024"
                results = await self._search_web(query, "week")
                
                analysis = self._analyze_economic_indicator(indicator, results)
                economic_data[indicator] = analysis
            
            # Generate overall economic risk assessment
            overall_assessment = self._generate_economic_assessment(economic_data)
            
            return {
                'indicators': economic_data,
                'overall_assessment': overall_assessment,
                'risk_level': overall_assessment.get('risk_level', 'MEDIUM'),
                'recommendations': overall_assessment.get('recommendations', []),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing economic indicators: {str(e)}")
            return self._get_fallback_economic_analysis()
    
    async def _search_news(self, query: str, time_filter: str) -> List[Dict[str, Any]]:
        """Search Bing News API"""
        
        try:
            # Construct news search parameters
            params = {
                'q': quote_plus(query),
                'count': min(self.max_results, 50),
                'mkt': 'en-US',
                'safeSearch': 'Strict',
                'textFormat': 'HTML',
                'freshness': self._convert_time_filter(time_filter)
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.api_timeout)) as session:
                async with session.get(
                    self.news_endpoint,
                    headers=self.headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._process_news_results(data.get('value', []))
                    else:
                        self.logger.warning(f"News API returned status {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error in news search: {str(e)}")
            return []
    
    async def _search_web(self, query: str, time_filter: str) -> List[Dict[str, Any]]:
        """Search Bing Web Search API"""
        
        try:
            # Construct web search parameters
            params = {
                'q': quote_plus(query),
                'count': min(self.max_results, 50),
                'mkt': 'en-US',
                'safeSearch': 'Strict',
                'textFormat': 'HTML',
                'responseFilter': 'Webpages,News'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.api_timeout)) as session:
                async with session.get(
                    self.bing_endpoint,
                    headers=self.headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._process_web_results(data.get('webPages', {}).get('value', []))
                    else:
                        self.logger.warning(f"Web API returned status {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error in web search: {str(e)}")
            return []
    
    def _process_news_results(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process news search results"""
        
        processed_results = []
        
        for item in news_items:
            try:
                # Extract key information
                result = {
                    'type': 'news',
                    'title': item.get('name', ''),
                    'url': item.get('url', ''),
                    'description': item.get('description', ''),
                    'published_date': item.get('datePublished', ''),
                    'source': item.get('provider', [{}])[0].get('name', '') if item.get('provider') else '',
                    'relevance_score': self._calculate_relevance_score(item),
                    'category': item.get('category', 'general'),
                    'language': item.get('language', 'en')
                }
                
                # Add sentiment analysis
                result['sentiment'] = self._analyze_sentiment(result['title'] + ' ' + result['description'])
                
                # Extract key insights
                result['key_insights'] = self._extract_key_insights(result['description'])
                
                processed_results.append(result)
                
            except Exception as e:
                self.logger.warning(f"Error processing news item: {str(e)}")
                continue
        
        # Sort by relevance and recency
        processed_results.sort(key=lambda x: (x['relevance_score'], x.get('published_date', '')), reverse=True)
        
        return processed_results[:15]  # Return top 15 results
    
    def _process_web_results(self, web_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process web search results"""
        
        processed_results = []
        
        for item in web_items:
            try:
                result = {
                    'type': 'web',
                    'title': item.get('name', ''),
                    'url': item.get('url', ''),
                    'description': item.get('snippet', ''),
                    'published_date': item.get('dateLastCrawled', datetime.now().isoformat()),
                    'source': self._extract_domain(item.get('url', '')),
                    'relevance_score': self._calculate_relevance_score(item),
                    'authority_score': self._calculate_authority_score(item.get('url', ''))
                }
                
                # Add sentiment analysis
                result['sentiment'] = self._analyze_sentiment(result['title'] + ' ' + result['description'])
                
                # Extract key insights
                result['key_insights'] = self._extract_key_insights(result['description'])
                
                processed_results.append(result)
                
            except Exception as e:
                self.logger.warning(f"Error processing web item: {str(e)}")
                continue
        
        # Sort by relevance and authority
        processed_results.sort(key=lambda x: (x['relevance_score'], x['authority_score']), reverse=True)
        
        return processed_results[:10]  # Return top 10 results
    
    async def _analyze_search_results(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]]
    ) -> MarketIntelligence:
        """Analyze and synthesize search results"""
        
        # Convert to NewsArticle objects
        articles = []
        for result in search_results:
            if result['relevance_score'] > 0.6:  # Filter for relevant results only
                article = NewsArticle(
                    title=result['title'],
                    url=result['url'],
                    description=result['description'],
                    published_date=result.get('published_date', ''),
                    source=result['source'],
                    relevance_score=result['relevance_score'],
                    sentiment=result['sentiment'],
                    key_insights=result['key_insights']
                )
                articles.append(article)
        
        # Identify fraud trends
        trends = self._identify_fraud_trends(articles)
        
        # Extract risk indicators
        risk_indicators = self._extract_risk_indicators(articles)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(trends, risk_indicators)
        
        # Create intelligence summary
        summary = self._create_intelligence_summary(query, articles, trends)
        
        return MarketIntelligence(
            search_query=query,
            search_timestamp=datetime.now().isoformat(),
            total_results=len(search_results),
            relevant_articles=articles[:10],  # Top 10 most relevant
            identified_trends=trends,
            risk_indicators=risk_indicators,
            recommendations=recommendations,
            intelligence_summary=summary
        )
    
    def _extract_fraud_insights(self, intelligence: MarketIntelligence) -> List[Dict[str, Any]]:
        """Extract actionable fraud insights from intelligence data"""
        
        insights = []
        
        # Process each identified trend
        for trend in intelligence.identified_trends:
            insight = {
                'type': 'fraud_trend',
                'category': trend.trend_type,
                'severity': trend.severity,
                'title': f"{trend.trend_type.replace('_', ' ').title()} Trend Alert",
                'summary': trend.impact_description,
                'affected_demographics': trend.affected_demographics,
                'prevention_strategies': trend.prevention_strategies,
                'confidence_level': trend.confidence_level,
                'data_sources': len(trend.data_sources),
                'recommendation_priority': 'HIGH' if trend.severity in ['HIGH', 'CRITICAL'] else 'MEDIUM'
            }
            insights.append(insight)
        
        # Add general risk indicators
        for indicator in intelligence.risk_indicators[:5]:  # Top 5 indicators
            insight = {
                'type': 'risk_indicator',
                'category': 'market_risk',
                'severity': 'MEDIUM',
                'title': 'Market Risk Indicator',
                'summary': indicator,
                'recommendation_priority': 'MEDIUM',
                'source_articles': len(intelligence.relevant_articles)
            }
            insights.append(insight)
        
        # Add key recommendations as insights
        for i, rec in enumerate(intelligence.recommendations[:3]):  # Top 3 recommendations
            insight = {
                'type': 'recommendation',
                'category': 'operational_improvement',
                'severity': 'LOW',
                'title': f'Market Intelligence Recommendation #{i+1}',
                'summary': rec,
                'recommendation_priority': 'LOW',
                'implementation_effort': 'MEDIUM'
            }
            insights.append(insight)
        
        return insights
    
    def _identify_fraud_trends(self, articles: List[NewsArticle]) -> List[FraudTrend]:
        """Identify fraud trends from news articles"""
        
        trends = []
        
        # Analyze article content for trend patterns
        fraud_keywords = {
            'credit_card_skimming': ['skimming', 'card reader', 'ATM fraud', 'point of sale'],
            'identity_theft': ['identity theft', 'social security', 'personal information', 'data breach'],
            'synthetic_fraud': ['synthetic identity', 'fake identity', 'identity creation'],
            'account_takeover': ['account takeover', 'credential stuffing', 'password breach'],
            'online_fraud': ['online fraud', 'e-commerce fraud', 'digital fraud', 'phishing']
        }
        
        for trend_type, keywords in fraud_keywords.items():
            matching_articles = []
            severity_indicators = []
            
            for article in articles:
                content = (article.title + ' ' + article.description).lower()
                
                # Check for keyword matches
                matches = sum(1 for keyword in keywords if keyword.lower() in content)
                if matches > 0:
                    matching_articles.append(article)
                    
                    # Assess severity based on content
                    if any(word in content for word in ['surge', 'increase', 'rising', 'epidemic']):
                        severity_indicators.append('HIGH')
                    elif any(word in content for word in ['concern', 'alert', 'warning']):
                        severity_indicators.append('MEDIUM')
                    else:
                        severity_indicators.append('LOW')
            
            if matching_articles:
                # Determine overall severity
                severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
                for sev in severity_indicators:
                    severity_counts[sev] += 1
                
                if severity_counts['HIGH'] >= 2:
                    overall_severity = 'HIGH'
                elif severity_counts['MEDIUM'] >= 2:
                    overall_severity = 'MEDIUM'
                else:
                    overall_severity = 'LOW'
                
                # Create fraud trend
                trend = FraudTrend(
                    trend_type=trend_type,
                    severity=overall_severity,
                    affected_demographics=self._extract_demographics(matching_articles),
                    prevention_strategies=self._extract_prevention_strategies(matching_articles),
                    impact_description=self._summarize_trend_impact(matching_articles),
                    data_sources=[article.source for article in matching_articles],
                    confidence_level=min(0.9, len(matching_articles) * 0.15)
                )
                trends.append(trend)
        
        return trends
    
    def _extract_risk_indicators(self, articles: List[NewsArticle]) -> List[str]:
        """Extract risk indicators from articles"""
        
        indicators = []
        risk_patterns = [
            (r'(\d+%)\s+(increase|rise|surge)', 'Statistical increase detected'),
            (r'(new|emerging|latest)\s+fraud', 'Emerging fraud pattern identified'),
            (r'(breach|hack|compromise)', 'Security breach reported'),
            (r'(regulation|compliance|penalty)', 'Regulatory change detected'),
            (r'(economic|recession|inflation)', 'Economic risk factor'),
        ]
        
        for article in articles:
            content = article.title + ' ' + article.description
            
            for pattern, description in risk_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    indicator = f"{description}: {matches[0] if isinstance(matches[0], str) else ' '.join(matches[0])}"
                    if indicator not in indicators:
                        indicators.append(indicator)
        
        return indicators[:10]  # Return top 10 indicators
    
    def _generate_recommendations(
        self, 
        trends: List[FraudTrend], 
        risk_indicators: List[str]
    ) -> List[str]:
        """Generate actionable recommendations based on trends and indicators"""
        
        recommendations = []
        
        # Generate trend-based recommendations
        for trend in trends:
            if trend.severity in ['HIGH', 'CRITICAL']:
                recommendations.extend([
                    f"Implement enhanced monitoring for {trend.trend_type.replace('_', ' ')} patterns",
                    f"Review and update fraud detection rules for {trend.trend_type.replace('_', ' ')}",
                    f"Consider additional verification steps for applications matching {trend.trend_type.replace('_', ' ')} risk profile"
                ])
        
        # Generate risk indicator-based recommendations
        high_risk_count = len([t for t in trends if t.severity == 'HIGH'])
        if high_risk_count >= 2:
            recommendations.append("Consider implementing temporary additional security measures due to elevated fraud environment")
        
        if any('breach' in indicator.lower() for indicator in risk_indicators):
            recommendations.append("Review customer data sources for potential compromise")
        
        if any('regulation' in indicator.lower() for indicator in risk_indicators):
            recommendations.append("Review compliance procedures for recent regulatory changes")
        
        # Add general recommendations
        recommendations.extend([
            "Conduct regular review of fraud detection models against current market trends",
            "Consider implementing real-time fraud scoring based on current threat landscape",
            "Maintain ongoing monitoring of fraud trend evolution"
        ])
        
        return list(set(recommendations))[:8]  # Remove duplicates, return top 8
    
    def _create_intelligence_summary(
        self, 
        query: str, 
        articles: List[NewsArticle], 
        trends: List[FraudTrend]
    ) -> str:
        """Create executive summary of intelligence findings"""
        
        high_severity_trends = [t for t in trends if t.severity in ['HIGH', 'CRITICAL']]
        medium_severity_trends = [t for t in trends if t.severity == 'MEDIUM']
        
        summary = f"Market Intelligence Summary for '{query}':\n\n"
        
        if high_severity_trends:
            summary += f"HIGH PRIORITY ALERTS ({len(high_severity_trends)}):\n"
            for trend in high_severity_trends[:3]:
                summary += f"- {trend.trend_type.replace('_', ' ').title()}: {trend.impact_description[:100]}...\n"
            summary += "\n"
        
        if medium_severity_trends:
            summary += f"MODERATE CONCERNS ({len(medium_severity_trends)}):\n"
            for trend in medium_severity_trends[:2]:
                summary += f"- {trend.trend_type.replace('_', ' ').title()}: {trend.impact_description[:100]}...\n"
            summary += "\n"
        
        summary += f"Analysis based on {len(articles)} relevant sources from the past 30 days.\n"
        summary += f"Key sources include: {', '.join(set([a.source for a in articles[:5]]))}"
        
        return summary
    
    def _calculate_relevance_score(self, item: Dict[str, Any]) -> float:
        """Calculate relevance score for search result"""
        
        score = 0.0
        
        # Title relevance
        title = item.get('name', '').lower()
        if any(keyword in title for keyword in ['fraud', 'credit', 'security', 'breach']):
            score += 0.3
        
        # Description relevance  
        description = item.get('description', '').lower()
        if any(keyword in description for keyword in ['fraud', 'credit card', 'identity', 'theft']):
            score += 0.2
        
        # Source authority (basic check)
        url = item.get('url', '').lower()
        if any(domain in url for domain in ['reuters.com', 'bloomberg.com', 'wsj.com', 'cnn.com']):
            score += 0.2
        elif any(domain in url for domain in ['.gov', '.edu', 'federalreserve']):
            score += 0.3
        
        # Recency (if available)
        if 'datePublished' in item or 'dateLastCrawled' in item:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_authority_score(self, url: str) -> float:
        """Calculate authority score based on domain"""
        
        url = url.lower()
        
        # Government and regulatory sources
        if any(domain in url for domain in ['.gov', 'federalreserve', 'fdic.gov', 'cfpb.gov']):
            return 1.0
        
        # Major news outlets
        elif any(domain in url for domain in ['reuters.com', 'bloomberg.com', 'wsj.com', 'ft.com']):
            return 0.9
        
        # Financial industry sources
        elif any(domain in url for domain in ['americanbanker.com', 'bankingdive.com', 'paymentsdive.com']):
            return 0.8
        
        # Academic sources
        elif '.edu' in url:
            return 0.7
        
        # General news
        elif any(domain in url for domain in ['cnn.com', 'bbc.com', 'npr.org']):
            return 0.6
        
        else:
            return 0.4
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        
        text = text.lower()
        
        negative_words = ['fraud', 'breach', 'attack', 'stolen', 'compromised', 'threat', 'danger', 'risk']
        positive_words = ['secure', 'protected', 'safe', 'improved', 'better', 'reduced']
        
        negative_count = sum(1 for word in negative_words if word in text)
        positive_count = sum(1 for word in positive_words if word in text)
        
        if negative_count > positive_count + 1:
            return 'NEGATIVE'
        elif positive_count > negative_count:
            return 'POSITIVE'
        else:
            return 'NEUTRAL'
    
    def _extract_key_insights(self, text: str) -> List[str]:
        """Extract key insights from text"""
        
        insights = []
        
        # Look for statistical information
        stats_pattern = r'(\d+(?:\.\d+)?%|\$[\d,]+(?:\.\d+)?(?:[MBK])?)'
        stats = re.findall(stats_pattern, text)
        if stats:
            insights.append(f"Statistical data: {', '.join(stats[:3])}")
        
        # Look for trend indicators
        if any(word in text.lower() for word in ['increase', 'rise', 'surge', 'growing']):
            insights.append("Upward trend indicated")
        elif any(word in text.lower() for word in ['decrease', 'decline', 'falling', 'reduced']):
            insights.append("Downward trend indicated")
        
        # Look for urgency indicators
        if any(word in text.lower() for word in ['urgent', 'immediate', 'critical', 'emergency']):
            insights.append("Urgent action may be required")
        
        return insights[:3]  # Return top 3 insights
    
    def _extract_demographics(self, articles: List[NewsArticle]) -> List[str]:
        """Extract affected demographics from articles"""
        
        demographics = []
        demo_patterns = [
            r'(young|elderly|senior|millennial|gen z|boomer)',
            r'(high income|low income|middle class)',
            r'(urban|rural|suburban)',
            r'(small business|enterprise|consumer)'
        ]
        
        for article in articles:
            content = (article.title + ' ' + article.description).lower()
            for pattern in demo_patterns:
                matches = re.findall(pattern, content)
                demographics.extend(matches)
        
        return list(set(demographics))[:5]  # Return unique demographics
    
    def _extract_prevention_strategies(self, articles: List[NewsArticle]) -> List[str]:
        """Extract prevention strategies from articles"""
        
        strategies = [
            "Enhanced identity verification procedures",
            "Real-time transaction monitoring",
            "Multi-factor authentication implementation",
            "Regular security awareness training",
            "Advanced fraud detection algorithms"
        ]
        
        # Could be enhanced to actually parse strategies from article content
        return strategies[:3]
    
    def _summarize_trend_impact(self, articles: List[NewsArticle]) -> str:
        """Summarize the impact of a fraud trend"""
        
        impact_keywords = []
        for article in articles:
            content = article.title + ' ' + article.description
            
            if any(word in content.lower() for word in ['million', 'billion', 'widespread']):
                impact_keywords.append('significant financial impact')
            if any(word in content.lower() for word in ['consumer', 'customer', 'victim']):
                impact_keywords.append('consumer impact')
            if any(word in content.lower() for word in ['bank', 'financial institution']):
                impact_keywords.append('institutional impact')
        
        if impact_keywords:
            return f"Trend shows {', '.join(set(impact_keywords))} based on recent reports"
        else:
            return "Emerging trend requiring monitoring and assessment"
    
    def _convert_time_filter(self, time_filter: str) -> str:
        """Convert time filter to Bing API format"""
        
        mapping = {
            'day': 'Day',
            'week': 'Week', 
            'month': 'Month',
            'year': 'Year'
        }
        
        return mapping.get(time_filter, 'Month')
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return 'unknown'
    
    def _get_fallback_insights(self, query: str) -> List[Dict[str, Any]]:
        """Return fallback insights when API fails"""
        
        return [
            {
                'type': 'fallback_insight',
                'category': 'system_notice',
                'severity': 'LOW',
                'title': 'Market Research Unavailable',
                'summary': f'Unable to retrieve current market intelligence for "{query}". Using cached fraud prevention best practices.',
                'recommendation_priority': 'LOW',
                'fallback_recommendations': [
                    'Maintain standard fraud monitoring procedures',
                    'Review existing detection rules quarterly',
                    'Monitor industry publications for trend updates'
                ]
            }
        ]
    
    def _get_fallback_benchmarks(self, metric_type: str) -> Dict[str, Any]:
        """Return fallback benchmarks when API fails"""
        
        return {
            'metric_type': metric_type,
            'status': 'unavailable',
            'message': 'Industry benchmarks temporarily unavailable',
            'fallback_guidance': 'Use internal historical performance as baseline',
            'timestamp': datetime.now().isoformat()
        }
    
    def _process_benchmark_data(self, search_results: List[Dict[str, Any]], metric_type: str) -> Dict[str, Any]:
        """Process search results for benchmark data"""
        
        # Simplified processing - in real implementation would parse actual data
        return {
            'metric_type': metric_type,
            'industry_average': 'Data processing required',
            'percentiles': {
                '25th': 'TBD',
                '50th': 'TBD', 
                '75th': 'TBD'
            },
            'data_sources': len(search_results),
            'last_updated': datetime.now().isoformat()
        }
    
    def _process_regulatory_updates(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process regulatory update search results"""
        
        updates = []
        
        for result in search_results[:5]:  # Process top 5 results
            if result['relevance_score'] > 0.6:
                update = {
                    'title': result['title'],
                    'source': result['source'],
                    'url': result['url'],
                    'summary': result['description'][:200],
                    'published_date': result.get('published_date', ''),
                    'impact_level': 'MEDIUM',  # Could be enhanced with NLP analysis
                    'compliance_deadline': 'TBD',
                    'affected_areas': ['credit_reporting', 'consumer_protection']
                }
                updates.append(update)
        
        return updates
    
    def _analyze_economic_indicator(self, indicator: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze economic indicator from search results"""
        
        return {
            'indicator': indicator,
            'current_status': 'Analysis required',
            'trend': 'STABLE',  # Could be enhanced with actual data parsing
            'credit_risk_impact': 'MEDIUM',
            'confidence_level': len(search_results) * 0.1,
            'last_updated': datetime.now().isoformat()
        }
    
    def _generate_economic_assessment(self, economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall economic risk assessment"""
        
        return {
            'overall_risk_level': 'MEDIUM',
            'key_concerns': ['Economic uncertainty', 'Market volatility'],
            'positive_indicators': ['Stable employment', 'Consumer confidence'],
            'recommendations': [
                'Monitor economic indicators monthly',
                'Adjust risk models based on economic conditions',
                'Maintain conservative approach during uncertainty'
            ],
            'confidence_score': 0.75
        }
    
    def _get_fallback_economic_analysis(self) -> Dict[str, Any]:
        """Return fallback economic analysis"""
        
        return {
            'indicators': {},
            'overall_assessment': {
                'risk_level': 'MEDIUM',
                'recommendations': ['Use conservative risk assessment', 'Monitor manually'],
                'status': 'Data unavailable - using fallback analysis'
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    async def close(self):
        """Clean up plugin resources"""
        self._cache.clear()
        self.logger.info("MarketResearchPlugin closed")
    
    def __str__(self):
        return f"MarketResearchPlugin(max_results={self.max_results}, cache_size={len(self._cache)})"