"""
Base LLM Provider Interface
Abstract base class for all LLM providers (Gemini, GPT, Claude, etc.)
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize LLM provider
        
        Args:
            api_key: API key for the provider
            **kwargs: Provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text from prompt
        
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
    def get_available_models(self) -> list:
        """
        Get list of available models for this provider
        
        Returns:
            List of model names
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """
        Get default model name for this provider
        
        Returns:
            Default model name
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate provider configuration
        
        Returns:
            True if configuration is valid
        """
        return self.api_key is not None
    
    def get_provider_name(self) -> str:
        """Get provider name (e.g., 'gemini', 'openai', 'anthropic')"""
        return self.__class__.__name__.replace('Provider', '').lower()

