"""
Ollama LLM Provider
Implements BaseLLMProvider for local Ollama API
Supports both sync and async operations
"""
import os
import time
from typing import Optional
import requests
from requests.exceptions import ConnectionError, RequestException
import aiohttp
import asyncio
from src.llm.base_provider import BaseLLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM API provider"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Ollama provider
        
        Args:
            api_key: API key (not required for Ollama, kept for compatibility)
            default_model: Default model to use (e.g., 'dolphin3')
                          If None, loads from OLLAMA_DEFAULT_MODEL env var
            base_url: Ollama API base URL (e.g., 'http://localhost:11434')
                     If None, loads from OLLAMA_BASE_URL env var
            **kwargs: Additional Ollama-specific config
        """
        # Ollama doesn't require API key, but we keep it for base class compatibility
        super().__init__(api_key=api_key, **kwargs)
        
        # Get default model from env or parameter
        if default_model is None:
            default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "dolphin3")
        
        # Get base URL from env or parameter
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        self.default_model_name = default_model
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        
        # Get timeout from environment or use default
        # Default: 600 seconds (10 minutes) for long document generation
        # For very long documents, increase this value
        self.request_timeout = int(os.getenv("OLLAMA_TIMEOUT", "600"))
        
        # Async HTTP session (lazy initialization)
        self._async_session: Optional[aiohttp.ClientSession] = None
        
        # Test connection to Ollama server
        try:
            self._test_connection()
        except ConnectionError:
            logger.warning(
                f"Could not connect to Ollama server at {self.base_url}. "
                "Make sure Ollama is running. You can start it with: ollama serve"
            )
    
    async def _get_async_session(self) -> aiohttp.ClientSession:
        """Get or create async HTTP session"""
        if self._async_session is None or self._async_session.closed:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            self._async_session = aiohttp.ClientSession(timeout=timeout)
        return self._async_session
    
    async def _close_async_session(self):
        """Close async HTTP session"""
        if self._async_session and not self._async_session.closed:
            await self._async_session.close()
            self._async_session = None
    
    def _test_connection(self):
        """Test connection to Ollama server"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to Ollama server at {self.base_url}. "
                "Please ensure Ollama is running."
            ) from e
        except RequestException as e:
            raise RuntimeError(f"Error connecting to Ollama server: {str(e)}") from e
    
    def validate_config(self) -> bool:
        """
        Validate provider configuration
        Ollama doesn't require API key, so we override this to always return True
        if the server is reachable
        
        Returns:
            True if configuration is valid (server is reachable)
        """
        try:
            self._test_connection()
            return True
        except (ConnectionError, RequestException):
            return False
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama API
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (defaults to 8192 if not provided)
                       This ensures longer outputs similar to Gemini's default behavior
            **kwargs: Additional Ollama parameters (e.g., top_p, top_k)
            
        Returns:
            Generated text
            
        Raises:
            ConnectionError: If Ollama server is not running
            RuntimeError: If API call fails
        """
        model_name = model or self.default_model_name
        
        # Prepare request payload
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        # Set default max_tokens if not provided
        # Ollama's default num_predict is very low (~512), which causes short outputs
        # We set a higher default (8192 tokens) to match Gemini's behavior
        # This allows for ~32,000 characters of output (4 chars per token average)
        if max_tokens is None:
            # Use default from config or environment, otherwise 8192
            default_max_tokens = os.getenv("OLLAMA_MAX_TOKENS")
            if default_max_tokens:
                max_tokens = int(default_max_tokens)
            else:
                max_tokens = 8192  # Default to 8192 tokens for longer outputs
        
        # Add max_tokens (Ollama uses num_predict)
        payload["options"]["num_predict"] = max_tokens
        
        # Calculate dynamic timeout based on max_tokens and model
        # Different models have different generation speeds:
        # - Fast models (dolphin3, 8B): ~20-50 tokens/sec
        # - Medium models (llama2, 7B-13B): ~10-30 tokens/sec  
        # - Slow models (mixtral, 47B): ~5-15 tokens/sec
        # 
        # Conservative estimate: assume 10 tokens/second (worst case for large models)
        # Add 60s buffer for network and processing overhead
        tokens_per_second = 10  # Conservative estimate for large models
        estimated_generation_time = int(max_tokens / tokens_per_second) + 60
        
        # Use the larger of: configured timeout or estimated time
        # But cap at reasonable maximum (30 minutes) to prevent excessive waits
        request_timeout = min(
            max(self.request_timeout, estimated_generation_time),
            1800  # Max 30 minutes
        )
        
        logger.debug(
            f"Calculated timeout: {request_timeout}s "
            f"(configured: {self.request_timeout}s, estimated: {estimated_generation_time}s, "
            f"max_tokens: {max_tokens})"
        )
        
        # Add any additional options from kwargs
        if "top_p" in kwargs:
            payload["options"]["top_p"] = kwargs.pop("top_p")
        if "top_k" in kwargs:
            payload["options"]["top_k"] = kwargs.pop("top_k")
        
        # Add any remaining kwargs as options
        if kwargs:
            payload["options"].update(kwargs)
        
        # Retry configuration for transient errors (500, 503, etc.)
        max_retries = 2  # Retry up to 2 times for server errors
        retry_delay = 2.0  # Wait 2 seconds between retries
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(
                    f"Calling Ollama API (model: {model_name}, max_tokens: {max_tokens}, "
                    f"timeout: {request_timeout}s, prompt length: {len(prompt)} chars, "
                    f"attempt: {attempt + 1}/{max_retries + 1})"
                )
                
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=request_timeout  # Dynamic timeout based on max_tokens
                )
                
                # Check for HTTP errors
                if response.status_code >= 400:
                    # Try to extract error details from response
                    error_details = None
                    try:
                        error_response = response.json()
                        if "error" in error_response:
                            error_details = error_response["error"]
                        elif "message" in error_response:
                            error_details = error_response["message"]
                    except Exception:
                        error_details = response.text[:200] if response.text else None
                    
                    # Handle 500/503 errors with retry
                    if response.status_code in [500, 503] and attempt < max_retries:
                        error_msg = (
                            f"Ollama API server error ({response.status_code}): {error_details or 'Internal server error'}. "
                            f"Retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries + 1})..."
                        )
                        logger.warning(error_msg)
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                        continue
                    
                    # For other errors or after retries exhausted, raise immediately
                    error_msg = (
                        f"Ollama API error ({response.status_code}): {error_details or response.reason}. "
                        f"Model: {model_name}, URL: {self.base_url}/api/chat"
                    )
                    
                    # Provide specific suggestions based on error code
                    if response.status_code == 404:
                        error_msg += (
                            f"\nModel '{model_name}' not found. "
                            f"Available models: {', '.join(self.get_available_models())}. "
                            f"Try: ollama pull {model_name}"
                        )
                    elif response.status_code == 500:
                        error_msg += (
                            f"\nOllama server internal error. Possible causes: "
                            f"1) Model '{model_name}' failed to load (check memory), "
                            f"2) Server out of memory, 3) Model file corruption. "
                            f"Try: ollama run {model_name} (to test model), or use a smaller model like 'dolphin3'"
                        )
                    elif response.status_code == 503:
                        error_msg += (
                            f"\nOllama server temporarily unavailable. "
                            f"Wait a few seconds and try again, or check if Ollama is running: ollama list"
                        )
                    
                    logger.error(error_msg)
                    response.raise_for_status()  # This will raise HTTPError with full details
                
                # Success - parse response
                result = response.json()
                
                # Extract message content from response
                if "message" in result and "content" in result["message"]:
                    content = result["message"]["content"]
                    logger.debug(f"Ollama API response received ({len(content)} characters)")
                    return content
                elif "response" in result:
                    # Fallback for /api/generate endpoint format
                    content = result["response"]
                    logger.debug(f"Ollama API response received ({len(content)} characters)")
                    return content
                else:
                    raise RuntimeError(f"Unexpected Ollama API response format: {result}")
                    
            except requests.exceptions.Timeout as e:
                error_msg = (
                    f"Ollama API request timed out after {request_timeout} seconds. "
                    f"This may happen with large models (like {model_name}) or long prompts. "
                    f"Consider: 1) Increasing OLLAMA_TIMEOUT in .env, 2) Using a faster model, "
                    f"3) Reducing max_tokens, or 4) Using Gemini for complex documents."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            except requests.exceptions.HTTPError as e:
                # This is raised by response.raise_for_status() for 4xx/5xx errors
                # We've already handled retries above, so if we get here, retries are exhausted
                error_msg = (
                    f"Ollama API HTTP error after {max_retries + 1} attempts: {str(e)}. "
                    f"Model: {model_name}. Check Ollama server logs for details."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            except ConnectionError as e:
                raise ConnectionError(
                    f"Cannot connect to Ollama server at {self.base_url}. "
                    "Please ensure Ollama is running: ollama serve"
                ) from e
            except requests.exceptions.RequestException as e:
                # For other request errors, retry once
                if attempt < max_retries:
                    logger.warning(
                        f"Ollama API request error: {str(e)}. "
                        f"Retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries + 1})..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                raise RuntimeError(f"Ollama API error: {str(e)}") from e
            except Exception as e:
                # For unexpected errors, don't retry
                raise RuntimeError(f"Unexpected error calling Ollama API: {str(e)}") from e
        
        # Should not reach here, but just in case
        raise RuntimeError(f"Ollama API call failed after {max_retries + 1} attempts")
    
    def get_available_models(self) -> list:
        """
        Get list of available Ollama models
        
        Returns:
            List of model names available locally
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract model names from response
            if "models" in result:
                return [model["name"] for model in result["models"]]
            else:
                logger.warning("Unexpected response format from Ollama /api/tags")
                return [self.default_model_name]
                
        except ConnectionError:
            logger.warning(
                f"Cannot connect to Ollama server at {self.base_url}. "
                "Returning default model only."
            )
            return [self.default_model_name]
        except RequestException as e:
            logger.warning(f"Error fetching Ollama models: {str(e)}")
            return [self.default_model_name]
        except Exception as e:
            logger.warning(f"Unexpected error fetching Ollama models: {str(e)}")
            return [self.default_model_name]
    
    def get_default_model(self) -> str:
        """Get default Ollama model"""
        return self.default_model_name
    
    async def async_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama API (async version)
        
        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (defaults to 8192 if not provided)
            **kwargs: Additional Ollama parameters
        
        Returns:
            Generated text
        """
        model_name = model or self.default_model_name
        
        # Prepare request payload (same as sync version)
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        # Set default max_tokens if not provided
        if max_tokens is None:
            default_max_tokens = os.getenv("OLLAMA_MAX_TOKENS")
            if default_max_tokens:
                max_tokens = int(default_max_tokens)
            else:
                max_tokens = 8192
        
        payload["options"]["num_predict"] = max_tokens
        
        # Calculate dynamic timeout
        tokens_per_second = 10
        estimated_generation_time = int(max_tokens / tokens_per_second) + 60
        request_timeout = min(
            max(self.request_timeout, estimated_generation_time),
            1800
        )
        
        # Add additional options from kwargs
        if "top_p" in kwargs:
            payload["options"]["top_p"] = kwargs.pop("top_p")
        if "top_k" in kwargs:
            payload["options"]["top_k"] = kwargs.pop("top_k")
        if kwargs:
            payload["options"].update(kwargs)
        
        # Retry configuration
        max_retries = 2
        retry_delay = 2.0
        
        session = await self._get_async_session()
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(
                    f"Calling Ollama API (async) (model: {model_name}, max_tokens: {max_tokens}, "
                    f"timeout: {request_timeout}s, attempt: {attempt + 1}/{max_retries + 1})"
                )
                
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=request_timeout)
                ) as response:
                    # Check for HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        error_details = None
                        try:
                            error_response = await response.json()
                            if "error" in error_response:
                                error_details = error_response["error"]
                            elif "message" in error_response:
                                error_details = error_response["message"]
                        except Exception:
                            error_details = error_text[:200] if error_text else None
                        
                        # Handle 500/503 errors with retry
                        if response.status in [500, 503] and attempt < max_retries:
                            error_msg = (
                                f"Ollama API server error ({response.status}): {error_details or 'Internal server error'}. "
                                f"Retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries + 1})..."
                            )
                            logger.warning(error_msg)
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 1.5
                            continue
                        
                        # For other errors, raise immediately
                        error_msg = (
                            f"Ollama API error ({response.status}): {error_details or response.reason}. "
                            f"Model: {model_name}, URL: {self.base_url}/api/chat"
                        )
                        
                        if response.status == 404:
                            error_msg += (
                                f"\nModel '{model_name}' not found. "
                                f"Try: ollama pull {model_name}"
                            )
                        elif response.status == 500:
                            error_msg += (
                                f"\nOllama server internal error. "
                                f"Try: ollama run {model_name} (to test model)"
                            )
                        elif response.status == 503:
                            error_msg += (
                                f"\nOllama server temporarily unavailable. "
                                f"Wait a few seconds and try again."
                            )
                        
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)
                    
                    # Success - parse response
                    result = await response.json()
                    
                    # Extract message content from response
                    if "message" in result and "content" in result["message"]:
                        content = result["message"]["content"]
                        logger.debug(f"Ollama API response received (async) ({len(content)} characters)")
                        return content
                    elif "response" in result:
                        content = result["response"]
                        logger.debug(f"Ollama API response received (async) ({len(content)} characters)")
                        return content
                    else:
                        raise RuntimeError(f"Unexpected Ollama API response format: {result}")
                        
            except asyncio.TimeoutError as e:
                error_msg = (
                    f"Ollama API request timed out after {request_timeout} seconds. "
                    f"Consider: 1) Increasing OLLAMA_TIMEOUT, 2) Using a faster model, "
                    f"3) Reducing max_tokens"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            except aiohttp.ClientError as e:
                if attempt < max_retries:
                    logger.warning(
                        f"Ollama API request error: {str(e)}. "
                        f"Retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries + 1})..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                raise RuntimeError(f"Ollama API error: {str(e)}") from e
            except Exception as e:
                raise RuntimeError(f"Unexpected error calling Ollama API: {str(e)}") from e
        
        # Should not reach here
        raise RuntimeError(f"Ollama API call failed after {max_retries + 1} attempts")

