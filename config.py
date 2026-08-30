import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sih26032-smart-farmer-super-secret-key-2026')
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Rahul@940153')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'smart_farmer')
    
    # App Information
    APP_NAME = 'Smart Farmer Procurement & Queue System'
    PROBLEM_STATEMENT = 'SIH26032'
    MINISTRY = 'Ministry of Agriculture & Farmers Welfare, Govt of India'
    
    # Smart Queue Prediction Defaults
    DEFAULT_AVG_PROCESSING_MINS = 15
    LOW_CONGESTION_MAX_MINS = 20
    MED_CONGESTION_MAX_MINS = 45
