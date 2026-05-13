"""Application configuration."""
import os
from datetime import timedelta


class Config:
    """Main application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://taskuser:taskpass@db:3306/taskmanager',
    )
    DEBUG = True

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-me-jwt')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    RATELIMIT_ENABLED = True


class TestingConfig(Config):
    """Testing configuration — SQLite in-memory, no Redis."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = 'memory://'


config_map = {
    'default': Config,
    'testing': TestingConfig,
}
