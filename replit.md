# Shopify Insights Extractor

## Overview

A Flask-based web application that scrapes and analyzes Shopify stores to extract comprehensive business insights. The application takes a Shopify store URL as input and returns structured data including product catalogs, policies, contact information, social media handles, and other business intelligence without using the official Shopify API.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Chosen for its simplicity and rapid development capabilities
- **Single-threaded architecture**: Suitable for the scraping workload and demo requirements
- **Session management**: Uses Flask's built-in session handling with configurable secret keys

### Web Scraping Engine
- **ShopifyScraper class**: Custom scraper built with requests and BeautifulSoup
- **Session-based requests**: Maintains consistent headers and connection pooling
- **JSON endpoint extraction**: Leverages Shopify's `/products.json` API for structured product data
- **HTML parsing**: Uses BeautifulSoup for extracting unstructured content from web pages
- **Error handling**: Comprehensive exception handling with proper HTTP status codes

### Frontend Architecture
- **Server-side rendering**: Traditional HTML templates with Jinja2 templating
- **Bootstrap 5**: For responsive UI components and styling
- **AJAX interactions**: JavaScript for asynchronous API calls to prevent page refreshes
- **Single-page application feel**: Dynamic content updates without full page reloads

### API Design
- **RESTful endpoints**: Clean API structure with `/api/extract` for data extraction
- **JSON request/response**: Structured data exchange format
- **Error standardization**: Consistent error response format with status codes

### Data Processing
- **Real-time extraction**: No data persistence, processes requests on-demand
- **Structured output**: Organizes scraped data into categorized insights
- **Validation layer**: URL validation and sanitization before processing

### Logging and Monitoring
- **Python logging**: Built-in logging configuration for debugging and monitoring
- **Request tracking**: Error logging for failed requests and extraction issues

## External Dependencies

### Core Libraries
- **Flask**: Web application framework for routing and request handling
- **requests**: HTTP library for making web requests to Shopify stores
- **BeautifulSoup4**: HTML/XML parser for extracting content from web pages
- **urllib.parse**: URL manipulation and validation utilities

### Frontend Assets
- **Bootstrap 5**: CSS framework for responsive design and UI components
- **Font Awesome 6**: Icon library for user interface elements
- **jQuery**: JavaScript library for DOM manipulation and AJAX requests

### Development Tools
- **Python logging**: Built-in logging module for application monitoring
- **JSON**: Data serialization for API responses and Shopify endpoint parsing

### Target Platform
- **Shopify stores**: Application specifically designed to work with Shopify's URL structure and JSON endpoints
- **Public web content**: Scrapes publicly available information without authentication requirements