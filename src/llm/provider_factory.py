"""
LLM Provider Factory
Creates and manages LLM provider instances
"""
import os
from typing import Optional, Dict, Type
from src.llm.base_provider import BaseLLMProvider
from src.llm.gemini_provider import GeminiProvider
from src.llm.openai_provider import OpenAIProvider


class ProviderFactory:
    """Factory for creating LLM provider instances"""
    
    # Registry of available providers
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMProvider]):
        """
        Register a new provider type
        
        Args:
            name: Provider name (e.g., "anthropic", "cohere")
            provider_class: Provider class that inherits from BaseLLMProvider
        """
        cls._providers[name.lower()] = provider_class
    
    @classmethod
    def create(
        cls,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create LLM provider instance
        
        Args:
            provider_name: Name of provider ("gemini", "openai", etc.)
                          If None, reads from LLM_PROVIDER env var or defaults to "gemini"
            api_key: API key (if None, loads from env vars)
            **kwargs: Provider-specific configuration
        
        Returns:
            LLM provider instance
        
        Examples:
            >>> # Use Gemini (default)
            >>> provider = ProviderFactory.create()
            
            >>> # Use OpenAI
            >>> provider = ProviderFactory.create("openai")
            
            >>> # Use custom model
            >>> provider = ProviderFactory.create("gemini", default_model="gemini-2.5-pro")
        """
        # Determine provider name
        if provider_name is None:
            provider_name = os.getenv("LLM_PROVIDER", "gemini").lower()
        else:
            provider_name = provider_name.lower()
        
        # Get provider class
        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available providers: {available}"
            )
        
        provider_class = cls._providers[provider_name]
        
        # Create instance
        return provider_class(api_key=api_key, **kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of registered provider names"""
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_config_from_env(cls) -> Dict:
        """
        Get provider configuration from environment variables
        
        Returns:
            Dict with provider_name and any other config
        """
        return {
            "provider_name": os.getenv("LLM_PROVIDER", "gemini"),
            "model": os.getenv("LLM_MODEL"),  # Optional model override
        }

