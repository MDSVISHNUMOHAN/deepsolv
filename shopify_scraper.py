import requests
import json
import re
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging

class EcommerceScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = logging.getLogger(__name__)
    
    def _process_tags(self, tags):
        """Process tags field that can be either string or list."""
        if not tags:
            return []
        
        if isinstance(tags, list):
            return [str(tag).strip() for tag in tags if tag]
        
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        return []

    def validate_url(self, url: str) -> str:
        """Validate and normalize URL."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        return url

    def make_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Make HTTP request with error handling."""
        try:
            response = self.session.get(url, timeout=timeout)
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            return None

    def detect_currency(self, base_url: str) -> str:
        """Detect the currency used on the website."""
        response = self.make_request(base_url)
        if not response or response.status_code != 200:
            return 'USD'  # Default fallback
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        
        # Currency symbols and patterns
        currency_patterns = {
            'USD': [r'\$', r'usd', r'dollar', 'united states'],
            'EUR': [r'€', r'eur', r'euro'],
            'GBP': [r'£', r'gbp', r'pound', r'sterling'],
            'INR': [r'₹', r'inr', r'rupee', r'rs\.', r'rs ', 'india'],
            'CAD': [r'cad', r'c\$', 'canada'],
            'AUD': [r'aud', r'a\$', 'australia'],
            'JPY': [r'¥', r'jpy', r'yen', 'japan'],
            'CNY': [r'¥', r'cny', r'yuan', 'china'],
            'KRW': [r'₩', r'krw', r'won', 'korea'],
            'THB': [r'฿', r'thb', r'baht', 'thailand'],
            'SGD': [r'sgd', r's\$', 'singapore'],
            'MYR': [r'myr', r'rm', 'malaysia'],
            'PHP': [r'₱', r'php', r'peso', 'philippines'],
            'VND': [r'₫', r'vnd', r'dong', 'vietnam'],
            'BRL': [r'r\$', r'brl', r'real', 'brazil'],
            'MXN': [r'mxn', r'peso', 'mexico'],
            'ZAR': [r'zar', r'rand', 'south africa']
        }
        
        # Look for currency in meta tags and structured data
        currency_meta = soup.find('meta', {'name': 'currency'}) or soup.find('meta', {'property': 'product:price:currency'})
        if currency_meta and currency_meta.get('content'):
            return currency_meta['content'].upper()
        
        # Look for JSON-LD structured data
        json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    offers = data['offers']
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    if isinstance(offers, dict) and 'priceCurrency' in offers:
                        return offers['priceCurrency'].upper()
            except:
                continue
        
        # Pattern matching in page content
        for currency, patterns in currency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, page_text, re.IGNORECASE):
                    return currency
        
        return 'USD'  # Default fallback

    def extract_products_catalog(self, base_url: str) -> Dict[str, Any]:
        """Extract complete product catalog from any e-commerce website."""
        currency = self.detect_currency(base_url)
        
        # Try Shopify JSON endpoint first
        shopify_products = self._extract_shopify_products(base_url)
        if shopify_products['products']:
            shopify_products['currency'] = currency
            return shopify_products
        
        # Fallback to generic web scraping
        generic_products = self._extract_generic_products(base_url)
        generic_products['currency'] = currency
        return generic_products
    
    def _extract_shopify_products(self, base_url: str) -> Dict[str, Any]:
        """Extract products from Shopify JSON endpoint."""
        products_url = urljoin(base_url, '/products.json')
        response = self.make_request(products_url)
        
        if not response or response.status_code != 200:
            return {
                'products': [],
                'total_count': 0,
                'platform': 'unknown'
            }
        
        try:
            data = response.json()
            products = data.get('products', [])
            
            catalog = []
            for product in products:
                product_info = {
                    'id': product.get('id'),
                    'title': product.get('title'),
                    'handle': product.get('handle'),
                    'product_type': product.get('product_type'),
                    'vendor': product.get('vendor'),
                    'tags': self._process_tags(product.get('tags')),
                    'variants': [],
                    'images': [img.get('src') for img in product.get('images', [])],
                    'created_at': product.get('created_at'),
                    'updated_at': product.get('updated_at'),
                    'published_at': product.get('published_at'),
                    'status': product.get('status')
                }
                
                # Extract variant information
                for variant in product.get('variants', []):
                    variant_info = {
                        'id': variant.get('id'),
                        'title': variant.get('title'),
                        'price': variant.get('price'),
                        'compare_at_price': variant.get('compare_at_price'),
                        'sku': variant.get('sku'),
                        'inventory_quantity': variant.get('inventory_quantity'),
                        'available': variant.get('available')
                    }
                    product_info['variants'].append(variant_info)
                
                catalog.append(product_info)
            
            return {
                'products': catalog,
                'total_count': len(catalog),
                'platform': 'shopify'
            }
            
        except json.JSONDecodeError:
            return {
                'products': [],
                'total_count': 0,
                'platform': 'shopify',
                'error': 'Invalid JSON response from products endpoint'
            }
    
    def _extract_generic_products(self, base_url: str) -> Dict[str, Any]:
        """Extract products from any e-commerce website using web scraping."""
        response = self.make_request(base_url)
        
        if not response or response.status_code != 200:
            return {
                'products': [],
                'total_count': 0,
                'platform': 'generic',
                'error': 'Could not access website'
            }
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        
        # Common e-commerce product selectors
        product_selectors = [
            '.product-item', '.product-card', '.product',
            '[class*="product"]', '[data-product]',
            '.woocommerce-LoopProduct-link', '.product-wrap',
            '.grid-product', '.product-grid-item',
            '.item-product', '.product-list-item'
        ]
        
        for selector in product_selectors:
            product_elements = soup.select(selector)[:50]  # Limit to 50 products
            
            if len(product_elements) >= 3:  # If we found a good selector
                for elem in product_elements:
                    product_data = self._extract_product_data(elem, base_url)
                    if product_data and product_data['title']:
                        products.append(product_data)
                break
        
        # If no products found with selectors, try to find any product-like content
        if not products:
            products = self._extract_fallback_products(soup, base_url)
        
        return {
            'products': products,
            'total_count': len(products),
            'platform': self._detect_platform(soup)
        }
    
    def _extract_product_data(self, element, base_url: str) -> Dict[str, Any]:
        """Extract data from a single product element."""
        product = {
            'title': '',
            'price': '',
            'image': '',
            'url': '',
            'description': '',
            'availability': 'unknown'
        }
        
        # Extract title
        title_selectors = ['h1', 'h2', 'h3', 'h4', '[class*="title"]', '[class*="name"]', 'a']
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                product['title'] = title_elem.get_text(strip=True)[:200]
                break
        
        # Extract price
        price_selectors = [
            '[class*="price"]', '[class*="cost"]', '[class*="amount"]',
            '.money', '.currency', '[data-price]'
        ]
        for selector in price_selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract price with currency symbols
                price_match = re.search(r'[\$£€₹¥₩฿₱₫]?[\d,.]+(\.[\d]{2})?', price_text)
                if price_match:
                    product['price'] = price_match.group(0)
                    break
        
        # Extract image
        img_elem = element.select_one('img')
        if img_elem and img_elem.get('src'):
            product['image'] = urljoin(base_url, img_elem['src'])
        elif img_elem and img_elem.get('data-src'):  # Lazy loading
            product['image'] = urljoin(base_url, img_elem['data-src'])
        
        # Extract URL
        link_elem = element.select_one('a')
        if link_elem and link_elem.get('href'):
            product['url'] = urljoin(base_url, link_elem['href'])
        
        # Extract description
        desc_selectors = ['.description', '.summary', '[class*="desc"]']
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                product['description'] = desc_elem.get_text(strip=True)[:500]
                break
        
        return product
    
    def _extract_fallback_products(self, soup, base_url: str) -> List[Dict[str, Any]]:
        """Fallback method to extract products when standard selectors fail."""
        products = []
        
        # Look for any elements with prices
        price_elements = soup.find_all(text=re.compile(r'[\$£€₹¥₩฿₱₫][\d,.]+(\.[\d]{2})?'))
        
        for price_elem in price_elements[:20]:  # Limit to 20
            parent = price_elem.parent
            if parent:
                # Try to find title near the price
                title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
                if title_elem and len(title_elem.get_text(strip=True)) > 5:
                    product = {
                        'title': title_elem.get_text(strip=True)[:200],
                        'price': price_elem.strip(),
                        'image': '',
                        'url': '',
                        'description': ''
                    }
                    
                    # Try to find image
                    img_elem = parent.find('img')
                    if img_elem and img_elem.get('src'):
                        product['image'] = urljoin(base_url, img_elem['src'])
                    
                    products.append(product)
        
        return products
    
    def _detect_platform(self, soup) -> str:
        """Detect the e-commerce platform being used."""
        page_text = soup.get_text().lower()
        
        # Platform detection patterns
        if 'shopify' in page_text or soup.find(attrs={'name': 'shopify-checkout-api-token'}):
            return 'shopify'
        elif 'woocommerce' in page_text or soup.find(class_=re.compile(r'woocommerce')):
            return 'woocommerce'
        elif 'magento' in page_text:
            return 'magento'
        elif 'bigcommerce' in page_text:
            return 'bigcommerce'
        elif 'prestashop' in page_text:
            return 'prestashop'
        elif 'opencart' in page_text:
            return 'opencart'
        else:
            return 'generic'

    def extract_hero_products(self, base_url: str) -> List[Dict[str, str]]:
        """Extract hero products from homepage."""
        response = self.make_request(base_url)
        
        if not response or response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        hero_products = []
        
        # Common selectors for hero/featured products
        selectors = [
            '.hero-product',
            '.featured-product',
            '.product-card',
            '.product-item',
            '[class*="hero"]',
            '[class*="featured"]',
            '.slider .product',
            '.carousel .product'
        ]
        
        for selector in selectors:
            products = soup.select(selector)
            for product in products[:6]:  # Limit to first 6 found
                product_info = {}
                
                # Extract product title
                title_elem = product.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or product.find(class_=re.compile(r'title|name'))
                if title_elem:
                    product_info['title'] = title_elem.get_text(strip=True)
                
                # Extract product link
                link_elem = product.find('a') or product.find_parent('a')
                if link_elem and link_elem.get('href'):
                    product_info['url'] = urljoin(base_url, link_elem['href'])
                
                # Extract product image
                img_elem = product.find('img')
                if img_elem and img_elem.get('src'):
                    product_info['image'] = urljoin(base_url, img_elem['src'])
                
                # Extract price
                price_elem = product.find(class_=re.compile(r'price|cost|amount'))
                if price_elem:
                    product_info['price'] = price_elem.get_text(strip=True)
                
                if product_info and product_info not in hero_products:
                    hero_products.append(product_info)
        
        return hero_products

    def extract_policies(self, base_url: str) -> Dict[str, str]:
        """Extract privacy policy, return/refund policies."""
        policies = {}
        
        # Common policy page URLs
        policy_urls = {
            'privacy_policy': ['/pages/privacy-policy', '/privacy-policy', '/privacy'],
            'return_policy': ['/pages/return-policy', '/return-policy', '/returns', '/pages/returns'],
            'refund_policy': ['/pages/refund-policy', '/refund-policy', '/refunds', '/pages/refunds'],
            'terms_of_service': ['/pages/terms-of-service', '/terms-of-service', '/terms', '/pages/terms'],
            'shipping_policy': ['/pages/shipping-policy', '/shipping-policy', '/shipping', '/pages/shipping']
        }
        
        for policy_name, urls in policy_urls.items():
            for url_path in urls:
                full_url = urljoin(base_url, url_path)
                response = self.make_request(full_url)
                
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                        element.decompose()
                    
                    # Extract main content
                    content_selectors = ['.main-content', '.content', '.policy-content', 'main', '.page-content']
                    content = None
                    
                    for selector in content_selectors:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            content = content_elem.get_text(separator=' ', strip=True)
                            break
                    
                    if not content:
                        content = soup.get_text(separator=' ', strip=True)
                    
                    if content and len(content) > 100:  # Only store if substantial content
                        policies[policy_name] = content[:2000]  # Limit content length
                        break
        
        return policies

    def extract_faqs(self, base_url: str) -> List[Dict[str, str]]:
        """Extract FAQs from the website."""
        faqs = []
        
        # Common FAQ page URLs
        faq_urls = ['/pages/faq', '/faq', '/pages/frequently-asked-questions', '/help']
        
        for url_path in faq_urls:
            full_url = urljoin(base_url, url_path)
            response = self.make_request(full_url)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for FAQ structures
                faq_selectors = [
                    '.faq-item',
                    '.question',
                    '.accordion-item',
                    '[class*="faq"]',
                    '.qa-pair'
                ]
                
                for selector in faq_selectors:
                    faq_items = soup.select(selector)
                    
                    for item in faq_items:
                        question_elem = item.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or item.find(class_=re.compile(r'question|q\b'))
                        answer_elem = item.find(class_=re.compile(r'answer|a\b')) or item.find('p')
                        
                        if question_elem and answer_elem:
                            question = question_elem.get_text(strip=True)
                            answer = answer_elem.get_text(strip=True)
                            
                            if question and answer and len(question) > 5 and len(answer) > 5:
                                faqs.append({
                                    'question': question,
                                    'answer': answer
                                })
                
                if faqs:
                    break
        
        return faqs[:20]  # Limit to 20 FAQs

    def extract_social_handles(self, base_url: str) -> Dict[str, str]:
        """Extract social media handles."""
        response = self.make_request(base_url)
        
        if not response or response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        social_handles = {}
        
        # Social media patterns
        social_patterns = {
            'instagram': [r'instagram\.com/([^/\s"\']+)', r'@([a-zA-Z0-9_.]+)'],
            'facebook': [r'facebook\.com/([^/\s"\']+)', r'fb\.com/([^/\s"\']+)'],
            'twitter': [r'twitter\.com/([^/\s"\']+)', r'x\.com/([^/\s"\']+)'],
            'tiktok': [r'tiktok\.com/@([^/\s"\']+)'],
            'youtube': [r'youtube\.com/(?:channel/|user/|c/)?([^/\s"\']+)'],
            'linkedin': [r'linkedin\.com/(?:company/|in/)?([^/\s"\']+)'],
            'pinterest': [r'pinterest\.com/([^/\s"\']+)']
        }
        
        # Find all links
        links = soup.find_all('a', href=True)
        page_text = soup.get_text()
        
        for platform, patterns in social_patterns.items():
            for pattern in patterns:
                # Check in links
                for link in links:
                    href = link.get('href', '')
                    match = re.search(pattern, href)
                    if match:
                        social_handles[platform] = match.group(1)
                        break
                
                # Check in page text
                if platform not in social_handles:
                    match = re.search(pattern, page_text)
                    if match:
                        social_handles[platform] = match.group(1)
                
                if platform in social_handles:
                    break
        
        return social_handles

    def extract_contact_details(self, base_url: str) -> Dict[str, Any]:
        """Extract contact details like emails and phone numbers."""
        response = self.make_request(base_url)
        
        if not response or response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        contact_info = {
            'emails': [],
            'phones': [],
            'address': []
        }
        
        page_text = soup.get_text()
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)
        contact_info['emails'] = list(set(emails))[:5]  # Limit to 5 unique emails
        
        # Extract phone numbers
        phone_patterns = [
            r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'(\+\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            r'(\+\d{1,3}[-.\s]?)?\d{10,}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, page_text)
            contact_info['phones'].extend(phones)
        
        contact_info['phones'] = list(set(contact_info['phones']))[:5]
        
        # Try to find contact page for more details
        contact_urls = ['/pages/contact', '/contact', '/contact-us', '/pages/contact-us']
        
        for url_path in contact_urls:
            full_url = urljoin(base_url, url_path)
            response = self.make_request(full_url)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract address information
                address_selectors = ['.address', '.contact-address', '[class*="address"]']
                for selector in address_selectors:
                    address_elem = soup.select_one(selector)
                    if address_elem:
                        address = address_elem.get_text(strip=True)
                        if len(address) > 10:
                            contact_info['address'].append(address)
                
                break
        
        return contact_info

    def extract_brand_context(self, base_url: str) -> str:
        """Extract brand context and about information."""
        about_urls = ['/pages/about', '/about', '/pages/about-us', '/about-us', '/pages/our-story', '/our-story']
        
        for url_path in about_urls:
            full_url = urljoin(base_url, url_path)
            response = self.make_request(full_url)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                    element.decompose()
                
                # Extract main content
                content_selectors = ['.main-content', '.content', '.about-content', 'main', '.page-content']
                
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        content = content_elem.get_text(separator=' ', strip=True)
                        if len(content) > 100:
                            return content[:1500]  # Limit content length
                
                # Fallback to body content
                body_content = soup.get_text(separator=' ', strip=True)
                if len(body_content) > 100:
                    return body_content[:1500]
        
        return ""

    def extract_important_links(self, base_url: str) -> Dict[str, str]:
        """Extract important links like order tracking, contact us, blogs."""
        response = self.make_request(base_url)
        
        if not response or response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        important_links = {}
        
        # Define patterns for important links
        link_patterns = {
            'order_tracking': [r'track', r'order.*track', r'track.*order'],
            'contact_us': [r'contact', r'contact.*us'],
            'blog': [r'blog', r'news', r'articles'],
            'support': [r'support', r'help', r'customer.*service'],
            'store_locator': [r'store.*locat', r'find.*store', r'locations'],
            'size_guide': [r'size.*guide', r'sizing', r'fit.*guide']
        }
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link_type, patterns in link_patterns.items():
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, href, re.IGNORECASE):
                        full_url = urljoin(base_url, href)
                        important_links[link_type] = full_url
                        break
                
                if link_type in important_links:
                    break
        
        return important_links

    def extract_all_insights(self, website_url: str) -> Dict[str, Any]:
        """Extract all insights from any e-commerce website."""
        try:
            # Validate URL
            website_url = self.validate_url(website_url)
            
            # Check if website is accessible
            response = self.make_request(website_url)
            if not response:
                return {
                    'error': 'Website not accessible or does not exist',
                    'status_code': 401
                }
            
            if response.status_code == 404:
                return {
                    'error': 'Website not found',
                    'status_code': 404
                }
            
            if response.status_code != 200:
                return {
                    'error': f'Website returned status code {response.status_code}',
                    'status_code': response.status_code
                }
            
            self.logger.info(f"Starting extraction for: {website_url}")
            
            # Initialize results
            insights = {
                'website_url': website_url,
                'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }
            
            # Extract all data
            try:
                insights['product_catalog'] = self.extract_products_catalog(website_url)
                time.sleep(1)  # Rate limiting
                
                insights['hero_products'] = self.extract_hero_products(website_url)
                time.sleep(1)
                
                insights['policies'] = self.extract_policies(website_url)
                time.sleep(1)
                
                insights['faqs'] = self.extract_faqs(website_url)
                time.sleep(1)
                
                insights['social_handles'] = self.extract_social_handles(website_url)
                time.sleep(1)
                
                insights['contact_details'] = self.extract_contact_details(website_url)
                time.sleep(1)
                
                insights['brand_context'] = self.extract_brand_context(website_url)
                time.sleep(1)
                
                insights['important_links'] = self.extract_important_links(website_url)
                
                self.logger.info(f"Successfully extracted insights for: {website_url}")
                return insights
                
            except Exception as e:
                self.logger.error(f"Error during data extraction: {str(e)}")
                return {
                    'error': 'Error occurred during data extraction',
                    'status_code': 500,
                    'details': str(e)
                }
            
        except ValueError as e:
            return {
                'error': f'Invalid URL: {str(e)}',
                'status_code': 400
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return {
                'error': 'Internal server error',
                'status_code': 500,
                'details': str(e)
            }
