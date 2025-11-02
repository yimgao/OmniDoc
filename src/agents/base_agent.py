"""
Base Agent Class
All documentation agents should inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Optional
import os
from dotenv import load_dotenv

from src.rate_limit.queue_manager import RequestQueue
from src.llm.base_provider import BaseLLMProvider
from src.llm.provider_factory import ProviderFactory


class BaseAgent(ABC):
    """Base class for all documentation generation agents"""
    
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        rate_limiter: Optional[RequestQueue] = None,
        api_key: Optional[str] = None,
        **provider_kwargs
    ):
        """
        Initialize base agent
        
        Args:
            llm_provider: Pre-configured LLM provider instance (if None, creates from provider_name)
            provider_name: Name of provider ("gemini", "openai", etc.) - uses env var if None
            model_name: Model name override (provider-specific)
            rate_limiter: Rate limiting queue (if None, creates new one)
            api_key: API key (if None, loads from env vars)
            **provider_kwargs: Additional provider-specific configuration
        
        Examples:
            >>> # Use default (Gemini from env)
            >>> agent = RequirementsAnalyst()
            
            >>> # Use OpenAI explicitly
            >>> agent = RequirementsAnalyst(provider_name="openai")
            
            >>> # Use custom Gemini model
            >>> agent = RequirementsAnalyst(
            ...     provider_name="gemini",
            ...     default_model="gemini-2.5-pro"
            ... )
            
            >>> # Use pre-configured provider
            >>> provider = GeminiProvider(api_key="...")
            >>> agent = RequirementsAnalyst(llm_provider=provider)
        """
        load_dotenv()
        
        # Initialize LLM provider
        if llm_provider is not None:
            # Use provided provider
            self.llm_provider = llm_provider
        else:
            # Create provider from factory
            if model_name:
                # Pass model_name as provider-specific config
                if provider_name == "gemini" or provider_name is None:
                    provider_kwargs["default_model"] = model_name
                elif provider_name == "openai":
                    provider_kwargs["default_model"] = model_name
            
            self.llm_provider = ProviderFactory.create(
                provider_name=provider_name,
                api_key=api_key,
                **provider_kwargs
            )
        
        # Initialize rate limiter (share across instances if provided)
        self.rate_limiter = rate_limiter or RequestQueue(max_rate=60, period=60)
        
        # Agent metadata
        self.agent_name = self.__class__.__name__
        self.model_name = self.llm_provider.get_default_model()
        self.provider_name = self.llm_provider.get_provider_name()
    
    def _call_llm(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Call LLM with rate limiting (protected method for subclasses)
        
        Args:
            prompt: Input prompt
            model: Model name override (uses provider default if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Model response text
        """
        def make_request():
            return self.llm_provider.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        return self.rate_limiter.execute(make_request)
    
    @abstractmethod
    def generate(self, input_data: str) -> str:
        """
        Generate documentation (abstract method - must be implemented by subclasses)
        
        Args:
            input_data: Input to process (user idea, requirements, etc.)
            
        Returns:
            Generated documentation content
        """
        pass
    
    def get_stats(self) -> dict:
        """Get agent and rate limiting statistics"""
        return {
            "agent_name": self.agent_name,
            "provider": self.provider_name,
            "model_name": self.model_name,
            **self.rate_limiter.get_stats()
        }

