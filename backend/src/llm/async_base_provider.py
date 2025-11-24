"""
Async Base LLM Provider Interface
Abstract base class for async LLM providers
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AsyncBaseLLMProvider(ABC):
    """Abstract base class for async LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize async LLM provider
        
        Args:
            api_key: API key for the provider
            **kwargs: Provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text from prompt (async)
        
        Args:
            prompt: Input prompt
            model: Model name (if None, uses default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def get_available_models(self) -> list:
        """
        Get list of available models for this provider (async)
        
        Returns:
            List of model names
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """
        Get default model name for this provider (sync, can be cached)
        
        Returns:
            Default model name
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate provider configuration (sync)
        
        Returns:
            True if configuration is valid
        """
        return self.api_key is not None
    
    def get_provider_name(self) -> str:
        """Get provider name (e.g., 'gemini', 'openai', 'anthropic')"""
        return self.__class__.__name__.replace('Async', '').replace('Provider', '').lower()

