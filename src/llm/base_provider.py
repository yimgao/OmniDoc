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
        # Default: Run sync generate() in thread pool with timeout
        from src.utils.logger import get_logger
        import time
        logger = get_logger(__name__)
        logger.debug(f"BaseLLMProvider.async_generate: prompt length: {len(prompt)}, model: {model}")
        
        loop = asyncio.get_event_loop()
        start_time = time.time()
        try:
            # Add timeout to prevent hanging (4 minutes for the sync call)
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.generate(prompt, model, temperature, max_tokens, **kwargs)
                ),
                timeout=240.0  # 4 minutes timeout
            )
            elapsed = time.time() - start_time
            logger.debug(f"BaseLLMProvider.async_generate completed in {elapsed:.2f}s (result: {len(result) if result else 0} chars)")
            return result
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"LLM generation timed out after {elapsed:.2f}s (4 minutes)")
            raise TimeoutError(f"LLM generation timed out after 4 minutes")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"LLM generation failed after {elapsed:.2f}s: {type(e).__name__}: {str(e)}", exc_info=True)
            raise
    
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

