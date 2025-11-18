"""
Base Agent Class
All documentation agents should inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Optional
import os
from dotenv import load_dotenv

from src.rate_limit.queue_manager import RequestQueue
from src.rate_limit.async_queue_manager import AsyncRequestQueue
from src.utils.template_engine import get_template_engine
from src.llm.base_provider import BaseLLMProvider
from src.llm.provider_factory import ProviderFactory
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.utils.error_handler import retry_with_backoff
import requests
import asyncio

logger = get_logger(__name__)


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
                elif provider_name == "ollama":
                    provider_kwargs["default_model"] = model_name
            
            self.llm_provider = ProviderFactory.create(
                provider_name=provider_name,
                api_key=api_key,
                **provider_kwargs
            )
        
        # Initialize rate limiter (share across instances if provided)
        settings = get_settings()
        self.rate_limiter = rate_limiter or RequestQueue(
            max_rate=settings.rate_limit_per_minute, 
            period=60,
            max_daily_requests=settings.rate_limit_per_day
        )
        
        # Initialize async rate limiter (lazy initialization)
        self._async_rate_limiter: Optional[AsyncRequestQueue] = None
        
        # Agent metadata
        self.agent_name = self.__class__.__name__
        self.model_name = self.llm_provider.get_default_model()
        self.provider_name = self.llm_provider.get_provider_name()
        
        # Get temperature from settings based on provider
        # Lower temperature for local models (better instruction following)
        # Higher temperature for cloud models (more creative, but still controlled)
        if self.provider_name == "ollama":
            self.default_temperature = settings.ollama_temperature
        elif self.provider_name == "gemini":
            self.default_temperature = settings.gemini_temperature
        elif self.provider_name == "openai":
            self.default_temperature = settings.openai_temperature
        else:
            self.default_temperature = settings.default_temperature
        
        logger.debug(f"{self.agent_name} initialized with provider: {self.provider_name}, model: {self.model_name}, temperature: {self.default_temperature}")
    
    def _get_async_rate_limiter(self) -> AsyncRequestQueue:
        """Get or create async rate limiter"""
        if self._async_rate_limiter is None:
            settings = get_settings()
            self._async_rate_limiter = AsyncRequestQueue(
                max_rate=settings.rate_limit_per_minute,
                period=60,
                max_daily_requests=settings.rate_limit_per_day
            )
        return self._async_rate_limiter
    
    @retry_with_backoff(
        max_retries=3,
        initial_delay=2.0,
        backoff_factor=2.0,
        exceptions=(
            ConnectionError,
            TimeoutError,
            requests.exceptions.RequestException,  # Catches all requests exceptions (Timeout, ConnectionError, etc.)
            RuntimeError,  # For provider-level transient errors (e.g., "rate limit", "temporary failure")
        )
    )
    def _call_llm(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        phase_number: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Call LLM with rate limiting and retry logic (protected method for subclasses)
        
        This method includes automatic retry with exponential backoff for transient errors:
        - Network errors (ConnectionError, TimeoutError)
        - HTTP errors (requests exceptions)
        - Transient runtime errors
        
        Non-retryable errors (e.g., ValueError, authentication errors) are immediately raised.
        
        Args:
            prompt: Input prompt
            model: Model name override (uses provider default if None)
            temperature: Sampling temperature (uses agent default from settings if None)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Model response text
            
        Raises:
            ConnectionError: If connection fails after all retries
            TimeoutError: If request times out after all retries
            ValueError: If input is invalid (not retried)
            RuntimeError: If API call fails after all retries
        """
        # Use agent's default temperature if not explicitly provided
        if temperature is None:
            temperature = self.default_temperature
        
        # Get model for phase if phase_number is provided and model not explicitly set
        if model is None and phase_number is not None:
            from src.utils.phase_model_config import get_model_for_phase
            phase_model = get_model_for_phase(phase_number, self.provider_name)
            if phase_model:
                model = phase_model
                logger.debug(f"{self.agent_name} using phase {phase_number} model: {model}")
        
        model_to_use = model or self.model_name
        logger.info(f"🚀 {self.agent_name} calling LLM (model: {model_to_use}, prompt length: {len(prompt)} chars, temperature: {temperature})")
        
        # Define make_request to accept prompt as parameter so cache key includes prompt content
        def make_request(prompt_str: str):
            return self.llm_provider.generate(
                prompt=prompt_str,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        try:
            # Pass prompt as argument so it's included in cache key generation
            # Rate limiter will handle rate limiting, retry decorator will handle transient errors
            response = self.rate_limiter.execute(make_request, prompt)
            logger.info(f"{self.agent_name} LLM call completed (response length: {len(response)} characters)")
            # Clean and validate response
            cleaned_response = self._clean_llm_response(response)
            return cleaned_response
        except (ValueError, KeyError, AttributeError) as e:
            # Don't retry validation errors - these are permanent and won't be fixed by retrying
            # These exceptions are raised BEFORE the retry decorator can handle them
            logger.error(f"{self.agent_name} LLM call failed with validation error (not retried): {str(e)}", exc_info=True)
            raise
        # All other exceptions (ConnectionError, TimeoutError, RuntimeError, requests exceptions)
        # will be caught by the @retry_with_backoff decorator and retried with exponential backoff
    
    @retry_with_backoff(
        max_retries=3,
        initial_delay=2.0,
        backoff_factor=2.0,
        exceptions=(
            ConnectionError,
            TimeoutError,
            requests.exceptions.RequestException,
            RuntimeError,
        )
    )
    async def _async_call_llm(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        phase_number: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Call LLM with rate limiting and retry logic (async version)
        
        This method includes automatic retry with exponential backoff for transient errors:
        - Network errors (ConnectionError, TimeoutError)
        - HTTP errors (requests exceptions)
        - Transient runtime errors
        
        Non-retryable errors (e.g., ValueError, authentication errors) are immediately raised.
        
        Args:
            prompt: Input prompt
            model: Model name override (uses provider default if None)
            temperature: Sampling temperature (uses agent default from settings if None)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Model response text
            
        Raises:
            ConnectionError: If connection fails after all retries
            TimeoutError: If request times out after all retries
            ValueError: If input is invalid (not retried)
            RuntimeError: If API call fails after all retries
        """
        # Use agent's default temperature if not explicitly provided
        if temperature is None:
            temperature = self.default_temperature
        
        # Get model for phase if phase_number is provided and model not explicitly set
        # Also check agent instance for _current_phase_number attribute
        if model is None:
            phase_to_use = phase_number
            if phase_to_use is None and hasattr(self, '_current_phase_number'):
                phase_to_use = self._current_phase_number
            
            if phase_to_use is not None:
                from src.utils.phase_model_config import get_model_for_phase
                phase_model = get_model_for_phase(phase_to_use, self.provider_name)
                if phase_model:
                    model = phase_model
                    logger.debug(f"{self.agent_name} using phase {phase_to_use} model: {model}")
        
        model_to_use = model or self.model_name
        logger.debug(f"{self.agent_name} calling LLM (async) (model: {model_to_use}, prompt length: {len(prompt)} chars)")
        
        # Define async make_request function
        async def make_request(prompt_str: str):
            try:
                result = await self.llm_provider.async_generate(
                    prompt=prompt_str,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                return result
            except Exception as e:
                logger.error(f"{self.agent_name} LLM call failed: {type(e).__name__}: {str(e)}", exc_info=True)
                raise
        
        try:
            # Use async rate limiter with timeout
            async_rate_limiter = self._get_async_rate_limiter()
            
            # Add timeout to prevent hanging (5 minutes max)
            import asyncio
            import time
            start_time = time.time()
            response = await asyncio.wait_for(
                async_rate_limiter.execute(make_request, prompt),
                timeout=300.0  # 5 minutes timeout
            )
            elapsed = time.time() - start_time
            logger.debug(f"{self.agent_name} LLM call completed in {elapsed:.2f}s (response: {len(response) if response else 0} chars)")
            
            cleaned_response = self._clean_llm_response(response)
            return cleaned_response
        except asyncio.TimeoutError:
            logger.error(f"❌ {self.agent_name} _async_call_llm: LLM call timed out after 5 minutes")
            raise TimeoutError(f"{self.agent_name} LLM call timed out after 5 minutes")
        except (ValueError, KeyError, AttributeError) as e:
            # Don't retry validation errors
            logger.error(f"❌ {self.agent_name} _async_call_llm: LLM call failed with validation error (not retried): {type(e).__name__}: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"❌ {self.agent_name} _async_call_llm: LLM call failed with unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise
        # All other exceptions will be caught by the @retry_with_backoff decorator
    
    def _clean_llm_response(self, response: str) -> str:
        """
        Clean LLM response by removing markdown code blocks and extra formatting
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned response text
        """
        if not response:
            return response
        
        # Remove markdown code block wrappers (```markdown ... ```)
        cleaned = response.strip()
        
        # Check if response is wrapped in markdown code block
        if cleaned.startswith("```"):
            # Find the closing ```
            lines = cleaned.split("\n")
            if len(lines) > 1:
                # Remove first line (```markdown or ```)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line if it's ```
                if len(lines) > 0 and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
        
        # Remove any leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Log if significant cleaning occurred
        if len(response) != len(cleaned) or response != cleaned:
            logger.debug(f"{self.agent_name} cleaned response (original: {len(response)} chars, cleaned: {len(cleaned)} chars)")
        
        return cleaned
    
    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        """
        Generate documentation (abstract method - must be implemented by subclasses)
        
        This is the synchronous version. Subclasses can implement async_generate() for
        better performance in async contexts.
        
        Args:
            *args: Positional arguments (varies by agent)
            **kwargs: Keyword arguments (varies by agent)
            
        Returns:
            Generated documentation content
        """
        pass
    
    async def async_generate(self, *args, **kwargs) -> str:
        """
        Generate documentation (async version)
        
        Default implementation runs sync generate() in a thread pool.
        Subclasses can override this for native async support to improve performance.
        
        Args:
            *args: Arguments passed to generate() method
            **kwargs: Keyword arguments passed to generate() method
            
        Returns:
            Generated documentation content
        """
        # Default: Run sync generate() in thread pool
        # Subclasses should override this to use _async_call_llm directly for better performance
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(*args, **kwargs)
        )
    
    def get_stats(self) -> dict:
        """Get agent and rate limiting statistics"""
        return {
            "agent_name": self.agent_name,
            "provider": self.provider_name,
            "model_name": self.model_name,
            **self.rate_limiter.get_stats()
        }
    
    async def async_get_stats(self) -> dict:
        """Get agent and rate limiting statistics (async version)"""
        async_rate_limiter = self._get_async_rate_limiter()
        stats = await async_rate_limiter.get_stats()
        return {
            "agent_name": self.agent_name,
            "provider": self.provider_name,
            "model_name": self.model_name,
            **stats
        }

