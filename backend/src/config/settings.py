"""
Settings and Configuration Management
Handles DEV and PROD environment separation
"""
import os
from enum import Enum
from typing import Optional
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Environment(str, Enum):
    """Application environment types"""
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


# Global environment state
_current_environment: Optional[Environment] = None


def get_environment() -> Environment:
    """
    Get current environment (DEV/PROD/TEST)
    
    Checks in order:
    1. Explicitly set environment (via set_environment)
    2. ENVIRONMENT environment variable
    3. Defaults to DEV
    
    Returns:
        Current Environment enum value
    """
    global _current_environment
    
    if _current_environment:
        return _current_environment
    
    env_str = os.getenv("ENVIRONMENT", "dev").lower()
    
    try:
        return Environment(env_str)
    except ValueError:
        # Invalid environment, default to DEV
        return Environment.DEV


def set_environment(env: Environment) -> None:
    """
    Explicitly set the environment
    
    Args:
        env: Environment to set
    """
    global _current_environment
    _current_environment = env


@dataclass
class Settings:
    """Application settings based on environment"""
    environment: Environment
    # Logging
    log_level: str
    log_format: str  # 'json' or 'text'
    log_dir: str
    enable_performance_logging: bool
    # File paths
    docs_dir: str
    # LLM Configuration
    default_llm_provider: str
    rate_limit_per_minute: int
    rate_limit_per_day: int
    # LLM Temperature Configuration
    default_temperature: float  # Default temperature for all providers
    ollama_temperature: float   # Temperature for Ollama (lower for better instruction following)
    gemini_temperature: float   # Temperature for Gemini
    openai_temperature: float   # Temperature for OpenAI
    # Performance
    enable_profiling: bool
    # Debug features
    debug_mode: bool
    verbose_output: bool


def get_settings() -> Settings:
    """
    Get settings for current environment
    
    Returns:
        Settings object with environment-specific configuration
    """
    env = get_environment()
    
    # Temperature configuration (lower for local models, higher for cloud models)
    default_temperature = float(os.getenv("TEMPERATURE", "0.3"))  # Default: 0.3 for better instruction following
    ollama_temperature = float(os.getenv("OLLAMA_TEMPERATURE", os.getenv("TEMPERATURE", "0.3")))  # Lower for local models
    gemini_temperature = float(os.getenv("GEMINI_TEMPERATURE", os.getenv("TEMPERATURE", "0.7")))  # Higher for cloud models
    openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", os.getenv("TEMPERATURE", "0.7")))  # Higher for cloud models
    
    if env == Environment.PROD:
        return Settings(
            environment=env,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),  # JSON for production
            log_dir=os.getenv("LOG_DIR", "logs"),
            enable_performance_logging=True,
            docs_dir=os.getenv("DOCS_DIR", "docs"),
            default_llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "2")),  # Gemini free tier: 2 RPM
            rate_limit_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "50")),  # Gemini free tier: 50 RPD
            default_temperature=default_temperature,
            ollama_temperature=ollama_temperature,
            gemini_temperature=gemini_temperature,
            openai_temperature=openai_temperature,
            enable_profiling=False,  # Disable profiling in prod
            debug_mode=False,
            verbose_output=False
        )
    elif env == Environment.TEST:
        return Settings(
            environment=env,
            log_level=os.getenv("LOG_LEVEL", "WARNING"),
            log_format=os.getenv("LOG_FORMAT", "text"),
            log_dir=os.getenv("LOG_DIR", "logs/test"),
            enable_performance_logging=False,
            docs_dir=os.getenv("DOCS_DIR", "docs/test"),
            default_llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "2")),  # Gemini free tier: 2 RPM
            rate_limit_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "50")),  # Gemini free tier: 50 RPD
            default_temperature=default_temperature,
            ollama_temperature=ollama_temperature,
            gemini_temperature=gemini_temperature,
            openai_temperature=openai_temperature,
            enable_profiling=False,
            debug_mode=True,
            verbose_output=False
        )
    else:  # DEV
        return Settings(
            environment=env,
            log_level=os.getenv("LOG_LEVEL", "DEBUG"),
            log_format=os.getenv("LOG_FORMAT", "text"),  # Text for dev (easier to read)
            log_dir=os.getenv("LOG_DIR", "logs"),
            enable_performance_logging=True,
            docs_dir=os.getenv("DOCS_DIR", "docs"),
            default_llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "2")),  # Gemini free tier: 2 RPM
            rate_limit_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "50")),  # Gemini free tier: 50 RPD
            default_temperature=default_temperature,
            ollama_temperature=ollama_temperature,
            gemini_temperature=gemini_temperature,
            openai_temperature=openai_temperature,
            enable_profiling=True,  # Enable profiling in dev
            debug_mode=True,
            verbose_output=True
        )


# Convenience functions
def is_dev() -> bool:
    """Check if running in DEV mode"""
    return get_environment() == Environment.DEV


def is_prod() -> bool:
    """Check if running in PROD mode"""
    return get_environment() == Environment.PROD


def is_test() -> bool:
    """Check if running in TEST mode"""
    return get_environment() == Environment.TEST


# Export convenience functions
__all__ = [
    'Environment',
    'get_environment',
    'set_environment',
    'Settings',
    'get_settings',
    'is_dev',
    'is_prod',
    'is_test'
]

