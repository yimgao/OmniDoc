"""
Base LLM Provider Interface
Abstract base class for all LLM providers (Gemini, GPT, Claude, etc.)

Supports both sync and async operations.
For async support, implement async_generate() method.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import asyncio


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers (supports both sync and async)"""
    
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
        Generate text from prompt (synchronous)
        
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
    
    async def async_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text from prompt (asynchronous)
        
        Default implementation runs sync generate() in a thread pool.
        Override this method for native async support.
        
        Args:
            prompt: Input prompt
            model: Model name (if None, uses default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text response
        """
        # Default: Run sync generate() in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, model, temperature, max_tokens, **kwargs)
        )
    
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

