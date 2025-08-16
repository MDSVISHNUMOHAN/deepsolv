import re
import time
import concurrent.futures
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import threading

from shopify_scraper import EcommerceScraper


@dataclass
class CompetitorSite:
    name: str
    url: str
    similarity_score: float
    category: str

class AdvancedEcommerceScraper(EcommerceScraper):
    def __init__(self):
        super().__init__()
        self.processing_lock = threading.Lock()
    
    def find_competitors(self, website_url: str, brand_name: str = None) -> List[CompetitorSite]:
        """Find competitors using web search and analysis."""
        try:
            # Extract brand name from URL if not provided
            if not brand_name:
                domain = urlparse(website_url).netloc
                brand_name = domain.split('.')[0] if domain else "brand"
            
            # Search for similar stores
            competitors = []
            
            # Common competitor search patterns
            search_queries = [
                f"{brand_name} competitors",
                f"{brand_name} similar stores",
                f"{brand_name} alternatives",
                f"stores like {brand_name}",
                f"{brand_name} vs"
            ]
            
            # For demo purposes, return some common Shopify competitors
            # In a real implementation, you would use web search APIs
            common_competitors = [
                {"name": "Gymshark", "url": "https://row.gymshark.com", "category": "fitness"},
                {"name": "Allbirds", "url": "https://www.allbirds.com", "category": "footwear"},
                {"name": "MVMT", "url": "https://www.mvmt.com", "category": "accessories"},
                {"name": "Pura Vida", "url": "https://www.puravidabracelets.com", "category": "jewelry"},
                {"name": "Bombas", "url": "https://bombas.com", "category": "apparel"}
            ]
            
            # Filter and score competitors
            for comp in common_competitors[:3]:  # Limit to 3 for demo
                competitors.append(CompetitorSite(
                    name=comp["name"],
                    url=comp["url"],
                    similarity_score=0.7 + (len(competitors) * 0.1),  # Demo scoring
                    category=comp["category"]
                ))
            
            return competitors
            
        except Exception as e:
            self.logger.error(f"Error finding competitors: {str(e)}")
            return []
    
    def analyze_competitor(self, competitor_site: CompetitorSite) -> Dict[str, Any]:
        """Analyze a single competitor site."""
        try:
            insights = self.extract_all_insights(competitor_site.url)
            
            if insights.get('error'):
                return {
                    'competitor_name': competitor_site.name,
                    'competitor_url': competitor_site.url,
                    'error': insights['error'],
                    'similarity_score': competitor_site.similarity_score
                }
            
            # Add competitor-specific metadata
            insights['competitor_name'] = competitor_site.name
            insights['competitor_url'] = competitor_site.url
            insights['similarity_score'] = competitor_site.similarity_score
            insights['category'] = competitor_site.category
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error analyzing competitor {competitor_site.name}: {str(e)}")
            return {
                'competitor_name': competitor_site.name,
                'competitor_url': competitor_site.url,
                'error': f'Analysis failed: {str(e)}',
                'similarity_score': competitor_site.similarity_score
            }
    
    def bulk_analyze_urls(self, urls: List[str], max_workers: int = 3) -> Dict[str, Any]:
        """Analyze multiple URLs simultaneously."""
        results = {
            'successful': [],
            'failed': [],
            'total_urls': len(urls),
            'processing_time': 0
        }
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.extract_all_insights, url): url 
                for url in urls
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result(timeout=120)  # 2 minute timeout per URL
                    if result.get('error'):
                        results['failed'].append({
                            'url': url,
                            'error': result['error']
                        })
                    else:
                        results['successful'].append(result)
                except Exception as e:
                    results['failed'].append({
                        'url': url,
                        'error': f'Processing error: {str(e)}'
                    })
        
        results['processing_time'] = time.time() - start_time
        results['success_rate'] = len(results['successful']) / len(urls) * 100 if urls else 0
        
        return results
    
    def extract_competitive_analysis(self, website_url: str) -> Dict[str, Any]:
        """Extract insights from main site and its competitors."""
        try:
            self.logger.info(f"Starting competitive analysis for: {website_url}")
            
            # Get main site analysis
            main_analysis = self.extract_all_insights(website_url)
            if main_analysis.get('error'):
                return main_analysis
            
            # Extract brand name from the main site
            brand_name = None
            if 'brand_context' in main_analysis and main_analysis['brand_context']:
                # Try to extract brand name from context (simplified)
                domain = urlparse(website_url).netloc
                brand_name = domain.split('.')[0]
            
            # Find competitors
            competitors = self.find_competitors(website_url, brand_name)
            
            # Analyze competitors
            competitor_analyses = []
            for competitor in competitors:
                comp_analysis = self.analyze_competitor(competitor)
                competitor_analyses.append(comp_analysis)
                time.sleep(2)  # Rate limiting
            
            # Create competitive analysis summary
            competitive_summary = self.create_competitive_summary(main_analysis, competitor_analyses)
            
            return {
                'main_site': main_analysis,
                'competitors': competitor_analyses,
                'competitive_summary': competitive_summary,
                'analysis_type': 'competitive',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"Error in competitive analysis: {str(e)}")
            return {
                'error': 'Competitive analysis failed',
                'status_code': 500,
                'details': str(e)
            }
    
    def create_competitive_summary(self, main_analysis: Dict, competitor_analyses: List[Dict]) -> Dict[str, Any]:
        """Create a summary comparing main site with competitors."""
        try:
            summary = {
                'total_competitors_analyzed': len(competitor_analyses),
                'main_site_products': main_analysis.get('product_catalog', {}).get('total_count', 0),
                'competitor_product_counts': [],
                'social_presence_comparison': {},
                'policy_comparison': {},
                'key_differentiators': []
            }
            
            # Analyze product counts
            for comp in competitor_analyses:
                if not comp.get('error') and comp.get('product_catalog'):
                    summary['competitor_product_counts'].append({
                        'name': comp.get('competitor_name', 'Unknown'),
                        'product_count': comp['product_catalog'].get('total_count', 0)
                    })
            
            # Social media presence comparison
            main_social = main_analysis.get('social_handles', {})
            summary['social_presence_comparison']['main_site'] = len(main_social)
            
            for comp in competitor_analyses:
                if not comp.get('error') and comp.get('social_handles'):
                    comp_social = comp['social_handles']
                    summary['social_presence_comparison'][comp.get('competitor_name', 'Unknown')] = len(comp_social)
            
            # Policy comparison
            main_policies = main_analysis.get('policies', {})
            summary['policy_comparison']['main_site'] = len(main_policies)
            
            for comp in competitor_analyses:
                if not comp.get('error') and comp.get('policies'):
                    comp_policies = comp['policies']
                    summary['policy_comparison'][comp.get('competitor_name', 'Unknown')] = len(comp_policies)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error creating competitive summary: {str(e)}")
            return {'error': 'Failed to create competitive summary'}
    
    def structure_data_with_nlp(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance data structuring using natural language processing."""
        try:
            structured_data = raw_data.copy()
            
            # Enhanced product categorization
            if 'product_catalog' in structured_data and structured_data['product_catalog'].get('products'):
                structured_data['product_categories'] = self.categorize_products(
                    structured_data['product_catalog']['products']
                )
            
            # Enhanced brand analysis
            if 'brand_context' in structured_data and structured_data['brand_context']:
                structured_data['brand_analysis'] = self.analyze_brand_text(
                    structured_data['brand_context']
                )
            
            # FAQ insights
            if 'faqs' in structured_data and structured_data['faqs']:
                structured_data['faq_insights'] = self.analyze_faq_patterns(
                    structured_data['faqs']
                )
            
            return structured_data
            
        except Exception as e:
            self.logger.error(f"Error in NLP structuring: {str(e)}")
            return raw_data
    
    def categorize_products(self, products: List[Dict]) -> Dict[str, Any]:
        """Categorize products using keyword analysis."""
        categories = {}
        keyword_categories = {
            'apparel': ['shirt', 'dress', 'pants', 'jacket', 'hoodie', 'sweater', 'tee', 'top'],
            'accessories': ['bag', 'watch', 'jewelry', 'belt', 'hat', 'sunglasses'],
            'footwear': ['shoes', 'boots', 'sneakers', 'sandals', 'heels'],
            'beauty': ['makeup', 'skincare', 'perfume', 'cosmetics', 'beauty'],
            'fitness': ['protein', 'supplement', 'equipment', 'yoga', 'workout'],
            'home': ['candle', 'decor', 'furniture', 'kitchen', 'bathroom']
        }
        
        for product in products:
            title = product.get('title', '').lower()
            product_type = product.get('product_type', '').lower()
            tags = [tag.lower() for tag in product.get('tags', [])]
            
            categorized = False
            for category, keywords in keyword_categories.items():
                if any(keyword in title or keyword in product_type or any(keyword in tag for tag in tags) for keyword in keywords):
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(product)
                    categorized = True
                    break
            
            if not categorized:
                if 'other' not in categories:
                    categories['other'] = []
                categories['other'].append(product)
        
        return {
            'categories': categories,
            'category_counts': {cat: len(products) for cat, products in categories.items()},
            'total_categorized': sum(len(products) for products in categories.values())
        }
    
    def analyze_brand_text(self, brand_text: str) -> Dict[str, Any]:
        """Analyze brand text for key insights."""
        insights = {
            'word_count': len(brand_text.split()),
            'key_themes': [],
            'brand_values': [],
            'target_audience_indicators': []
        }
        
        # Simple keyword analysis
        brand_keywords = {
            'sustainability': ['sustainable', 'eco-friendly', 'environmental', 'green', 'organic', 'natural'],
            'quality': ['premium', 'luxury', 'high-quality', 'craftsmanship', 'artisan'],
            'innovation': ['innovative', 'technology', 'cutting-edge', 'advanced', 'revolutionary'],
            'community': ['community', 'together', 'family', 'connect', 'share'],
            'wellness': ['wellness', 'health', 'fitness', 'mindfulness', 'balance']
        }
        
        text_lower = brand_text.lower()
        for theme, keywords in brand_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                insights['key_themes'].append(theme)
        
        return insights
    
    def analyze_faq_patterns(self, faqs: List[Dict]) -> Dict[str, Any]:
        """Analyze FAQ patterns for business insights."""
        patterns = {
            'total_faqs': len(faqs),
            'common_topics': {},
            'avg_answer_length': 0,
            'customer_concerns': []
        }
        
        if not faqs:
            return patterns
        
        # Topic analysis
        topics = {
            'shipping': ['ship', 'delivery', 'shipping'],
            'returns': ['return', 'refund', 'exchange'],
            'sizing': ['size', 'fit', 'sizing'],
            'payment': ['payment', 'pay', 'credit card', 'paypal'],
            'products': ['product', 'material', 'quality']
        }
        
        answer_lengths = []
        for faq in faqs:
            question = faq.get('question', '').lower()
            answer = faq.get('answer', '')
            answer_lengths.append(len(answer))
            
            for topic, keywords in topics.items():
                if any(keyword in question for keyword in keywords):
                    patterns['common_topics'][topic] = patterns['common_topics'].get(topic, 0) + 1
        
        if answer_lengths:
            patterns['avg_answer_length'] = sum(answer_lengths) / len(answer_lengths)
        
        return patterns