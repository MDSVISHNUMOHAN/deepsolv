import os
import time
import logging
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

from models import db, AnalysisHistory, CompetitorAnalysis, BulkProcessingJob
from shopify_scraper import EcommerceScraper
from advanced_scraper import AdvancedEcommerceScraper

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_12345")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Fallback to SQLite for local development
    database_url = "sqlite:///local_shopify_insights.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Initialize scrapers
scraper = EcommerceScraper()
advanced_scraper = AdvancedEcommerceScraper()

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Render the main page with the URL input form."""
    # Get recent analyses for dashboard
    recent_analyses = AnalysisHistory.query.order_by(AnalysisHistory.created_at.desc()).limit(5).all()
    
    # Get some statistics
    stats = {
        'total_analyses': AnalysisHistory.query.count(),
        'successful_analyses': AnalysisHistory.query.filter_by(status='completed').count(),
        'total_competitors_found': CompetitorAnalysis.query.count(),
        'bulk_jobs': BulkProcessingJob.query.count()
    }
    
    return render_template('index.html', recent_analyses=recent_analyses, stats=stats)

@app.route('/api/extract', methods=['POST'])
def extract_insights():
    """API endpoint to extract insights from a Shopify website."""
    try:
        data = request.get_json()
        if not data or 'website_url' not in data:
            return jsonify({
                'error': 'Missing website_url in request body',
                'status_code': 400
            }), 400
        
        website_url = data['website_url'].strip()
        if not website_url:
            return jsonify({
                'error': 'Website URL cannot be empty',
                'status_code': 400
            }), 400
        
        analysis_type = data.get('analysis_type', 'single')
        start_time = time.time()
        
        # Extract insights based on type
        if analysis_type == 'competitive':
            insights = advanced_scraper.extract_competitive_analysis(website_url)
        else:
            insights = advanced_scraper.structure_data_with_nlp(
                scraper.extract_all_insights(website_url)
            )
        
        processing_time = time.time() - start_time
        
        if insights.get('error'):
            # Save failed analysis
            save_analysis_to_db(website_url, insights, analysis_type, 'failed', processing_time, insights['error'])
            status_code = insights.get('status_code', 500)
            return jsonify(insights), status_code
        
        # Save successful analysis
        analysis_id = save_analysis_to_db(website_url, insights, analysis_type, 'completed', processing_time)
        insights['analysis_id'] = analysis_id
        
        return jsonify(insights), 200
        
    except Exception as e:
        app.logger.error(f"Unexpected error in extract_insights: {str(e)}")
        return jsonify({
            'error': 'Internal server error occurred',
            'status_code': 500,
            'details': str(e)
        }), 500

@app.route('/extract', methods=['POST'])
def extract_form():
    """Handle form submission from the web interface."""
    try:
        website_url = request.form.get('website_url', '').strip()
        analysis_type = request.form.get('analysis_type', 'single')
        
        if not website_url:
            return render_template('index.html', 
                                 error='Website URL cannot be empty')
        
        start_time = time.time()
        
        # Extract insights based on analysis type
        if analysis_type == 'competitive':
            insights = advanced_scraper.extract_competitive_analysis(website_url)
        else:
            insights = advanced_scraper.structure_data_with_nlp(
                scraper.extract_all_insights(website_url)
            )
        
        processing_time = time.time() - start_time
        
        if insights.get('error'):
            # Save failed analysis
            save_analysis_to_db(website_url, insights, analysis_type, 'failed', processing_time, insights['error'])
            return render_template('index.html', 
                                 error=insights['error'],
                                 website_url=website_url)
        
        # Save successful analysis
        analysis_id = save_analysis_to_db(website_url, insights, analysis_type, 'completed', processing_time)
        insights['analysis_id'] = analysis_id
        
        return render_template('results.html', 
                             insights=insights,
                             website_url=website_url,
                             analysis_type=analysis_type)
        
    except Exception as e:
        app.logger.error(f"Unexpected error in extract_form: {str(e)}")
        return render_template('index.html', 
                             error=f'An unexpected error occurred: {str(e)}',
                             website_url=request.form.get('website_url', ''))

# New routes for advanced features
@app.route('/bulk-analysis')
def bulk_analysis_page():
    """Render bulk analysis page."""
    recent_jobs = BulkProcessingJob.query.order_by(BulkProcessingJob.created_at.desc()).limit(10).all()
    return render_template('bulk_analysis.html', recent_jobs=recent_jobs)

@app.route('/api/bulk-analyze', methods=['POST'])
def bulk_analyze():
    """API endpoint for bulk URL analysis."""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        job_name = data.get('job_name', f'Bulk Analysis {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        # Create bulk processing job
        job = BulkProcessingJob(
            job_name=job_name,
            total_urls=len(urls),
            status='in_progress'
        )
        db.session.add(job)
        db.session.commit()
        
        # Process URLs in background (simplified for demo)
        def process_bulk_job():
            results = advanced_scraper.bulk_analyze_urls(urls, max_workers=2)
            
            # Save results
            for result in results['successful']:
                save_analysis_to_db(
                    result['website_url'], 
                    result, 
                    'bulk', 
                    'completed',
                    results['processing_time'] / len(urls)
                )
            
            # Update job status
            job.completed_urls = len(results['successful'])
            job.failed_urls = len(results['failed'])
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            db.session.commit()
        
        # Start background processing (in production, use Celery or similar)
        import threading
        thread = threading.Thread(target=process_bulk_job)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job.id,
            'message': 'Bulk analysis started',
            'status': 'in_progress'
        })
        
    except Exception as e:
        app.logger.error(f"Error in bulk analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/job/<int:job_id>/status')
def get_job_status(job_id):
    """Get status of a bulk processing job."""
    job = BulkProcessingJob.query.get_or_404(job_id)
    return jsonify(job.to_dict())

@app.route('/history')
def analysis_history():
    """Show analysis history."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    analyses = AnalysisHistory.query.order_by(
        AnalysisHistory.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('history.html', analyses=analyses)

@app.route('/analysis/<int:analysis_id>')
def view_analysis(analysis_id):
    """View detailed analysis results."""
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    return render_template('analysis_detail.html', analysis=analysis)

@app.route('/api/analysis/<int:analysis_id>')
def get_analysis(analysis_id):
    """Get analysis data as JSON."""
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    return jsonify(analysis.to_dict())

@app.route('/competitors/<int:analysis_id>')
def view_competitors(analysis_id):
    """View competitor analysis results."""
    analysis = AnalysisHistory.query.get_or_404(analysis_id)
    competitors = CompetitorAnalysis.query.filter_by(analysis_id=analysis_id).all()
    return render_template('competitors.html', analysis=analysis, competitors=competitors)

def save_analysis_to_db(website_url, insights, analysis_type='single', status='completed', processing_time=0, error_message=None):
    """Save analysis results to database."""
    try:
        # Extract key metrics
        total_products = 0
        has_social_handles = False
        has_contact_info = False
        has_policies = False
        
        if not insights.get('error'):
            product_catalog = insights.get('product_catalog', {})
            total_products = product_catalog.get('total_count', 0)
            has_social_handles = bool(insights.get('social_handles'))
            has_contact_info = bool(insights.get('contact_details', {}).get('emails') or 
                                  insights.get('contact_details', {}).get('phones'))
            has_policies = bool(insights.get('policies'))
        
        analysis = AnalysisHistory(
            website_url=website_url,
            analysis_data=insights,
            analysis_type=analysis_type,
            status=status,
            processing_time=processing_time,
            error_message=error_message,
            total_products=total_products,
            has_social_handles=has_social_handles,
            has_contact_info=has_contact_info,
            has_policies=has_policies
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        # Save competitor data if it's a competitive analysis
        if analysis_type == 'competitive' and not insights.get('error'):
            competitors = insights.get('competitors', [])
            for competitor in competitors:
                if not competitor.get('error'):
                    comp_analysis = CompetitorAnalysis(
                        main_website=website_url,
                        competitor_website=competitor.get('competitor_url', ''),
                        analysis_id=analysis.id,
                        competitor_data=competitor,
                        similarity_score=competitor.get('similarity_score', 0)
                    )
                    db.session.add(comp_analysis)
            
            db.session.commit()
        
        return analysis.id
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving analysis to database: {str(e)}")
        return None

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'error': 'Endpoint not found',
        'status_code': 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'error': 'Internal server error',
        'status_code': 500
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
