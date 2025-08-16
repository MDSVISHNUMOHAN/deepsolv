import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import JSON
import json

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class AnalysisHistory(db.Model):
    __tablename__ = 'analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    website_url = db.Column(db.String(500), nullable=False, index=True)
    analysis_data = db.Column(JSON, nullable=False)
    analysis_type = db.Column(db.String(50), default='single')  # 'single', 'bulk', 'competitor'
    status = db.Column(db.String(20), default='completed')  # 'completed', 'failed', 'in_progress'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_time = db.Column(db.Float)  # in seconds
    error_message = db.Column(db.Text)
    
    # Extracted key metrics for quick access
    total_products = db.Column(db.Integer, default=0)
    has_social_handles = db.Column(db.Boolean, default=False)
    has_contact_info = db.Column(db.Boolean, default=False)
    has_policies = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<AnalysisHistory {self.id}: {self.website_url}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'website_url': self.website_url,
            'analysis_data': self.analysis_data,
            'analysis_type': self.analysis_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processing_time': self.processing_time,
            'error_message': self.error_message,
            'total_products': self.total_products,
            'has_social_handles': self.has_social_handles,
            'has_contact_info': self.has_contact_info,
            'has_policies': self.has_policies
        }

class CompetitorAnalysis(db.Model):
    __tablename__ = 'competitor_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    main_website = db.Column(db.String(500), nullable=False, index=True)
    competitor_website = db.Column(db.String(500), nullable=False, index=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis_history.id'), nullable=False)
    competitor_data = db.Column(JSON, nullable=False)
    similarity_score = db.Column(db.Float)  # 0-1 similarity score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    analysis = db.relationship('AnalysisHistory', backref='competitors')
    
    def __repr__(self):
        return f'<CompetitorAnalysis {self.id}: {self.main_website} vs {self.competitor_website}>'

class BulkProcessingJob(db.Model):
    __tablename__ = 'bulk_processing_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(200), nullable=False)
    total_urls = db.Column(db.Integer, nullable=False)
    completed_urls = db.Column(db.Integer, default=0)
    failed_urls = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='in_progress')  # 'in_progress', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<BulkProcessingJob {self.id}: {self.job_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_name': self.job_name,
            'total_urls': self.total_urls,
            'completed_urls': self.completed_urls,
            'failed_urls': self.failed_urls,
            'status': self.status,
            'progress_percentage': (self.completed_urls + self.failed_urls) / self.total_urls * 100 if self.total_urls > 0 else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }