# Overview

The Shopify Store Insights Fetcher is a Python web application that extracts comprehensive brand information from Shopify stores without using official APIs. It scrapes product catalogs, policies, contact information, social media handles, and other brand data, then structures this information using OpenAI's GPT-4o model. The application provides a FastAPI-based REST API with a demo web interface for analyzing any Shopify store URL.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **FastAPI**: Modern Python web framework chosen for automatic API documentation, type hints integration, and high performance
- **Async/await support**: Handles concurrent scraping operations efficiently
- **Pydantic models**: Provides data validation and serialization for all API requests and responses

## Data Extraction Pipeline
- **Multi-stage scraping**: Uses BeautifulSoup for HTML parsing and requests for HTTP operations
- **JSON endpoint extraction**: Leverages Shopify's `/products.json` endpoint for structured product data
- **Content extraction**: Uses Trafilatura library for clean text extraction from web pages
- **Rate limiting and error handling**: Implements session management and timeout controls

## AI-Powered Data Processing
- **OpenAI GPT-4o integration**: Cleans and structures scraped data into consistent formats
- **Content deduplication**: Removes duplicate products and normalizes inconsistent data
- **Text summarization**: Condenses lengthy descriptions and content into manageable sizes
- **Data categorization**: Automatically classifies and organizes extracted information

## Service Layer Architecture
- **ShopifyService**: Main orchestrator that coordinates scraping and processing
- **ShopifyScraper**: Handles all web scraping operations with error recovery
- **LLMProcessor**: Manages AI-powered data cleaning and structuring
- **Modular design**: Each component has single responsibility and clear interfaces

## Data Models
- **Product**: Complete product information including variants, pricing, and metadata
- **BrandInsights**: Comprehensive brand data container
- **FAQ, SocialHandle, ContactInfo**: Specialized models for different data types
- **Response models**: Structured API responses with proper error handling

## Web Interface
- **Static file serving**: Bootstrap-based demo UI served through FastAPI
- **Interactive forms**: Real-time API interaction for testing store analysis
- **Responsive design**: Mobile-friendly interface with modern styling

# External Dependencies

## AI Services
- **OpenAI API**: GPT-4o model for data cleaning and structuring
- **API key authentication**: Secure environment variable configuration

## Web Scraping Libraries
- **requests**: HTTP client for web page fetching
- **BeautifulSoup4**: HTML parsing and navigation
- **trafilatura**: Content extraction and text cleaning

## Web Framework
- **FastAPI**: Core web framework with automatic documentation
- **uvicorn**: ASGI server for running the application
- **Pydantic**: Data validation and settings management

## Frontend Assets
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for enhanced UI
- **Static file hosting**: Integrated through FastAPI's StaticFiles

## Utilities
- **urllib.parse**: URL validation and manipulation
- **re (regex)**: Text pattern matching and cleaning
- **logging**: Application monitoring and debugging
