"""
AI Client Module
Unified interface for multiple AI providers (Anthropic, OpenAI, Google, Ollama, xAI).
"""

import os
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIClient:
    """Unified AI client that supports multiple providers."""

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize AI client with specified provider.

        Args:
            provider: AI provider name ('anthropic', 'openai', 'google', 'ollama', 'xai')
                     If None, reads from AI_PROVIDER environment variable
        """
        self.provider = provider or os.getenv('AI_PROVIDER')
        if not self.provider:
            raise ValueError(
                "AI_PROVIDER environment variable is required. "
                "Please set it to one of: anthropic, openai, google, ollama, xai"
            )
        self.provider = self.provider.lower()
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate AI client based on provider."""
        if self.provider == 'anthropic':
            self._init_anthropic()
        elif self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'google':
            self._init_google()
        elif self.provider == 'ollama':
            self._init_ollama()
        elif self.provider == 'xai':
            self._init_xai()
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

    def _init_anthropic(self):
        """Initialize Anthropic Claude client."""
        try:
            from anthropic import Anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            self.client = Anthropic(api_key=api_key)
            logger.info("Initialized Anthropic client")
        except ImportError:
            raise ImportError("anthropic package not installed. Run: uv add anthropic")

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)
            logger.info("Initialized OpenAI client")
        except ImportError:
            raise ImportError("openai package not installed. Run: uv add openai")

    def _init_google(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            genai.configure(api_key=api_key)
            model_name = os.getenv('GOOGLE_MODEL', 'gemini-1.5-pro')
            self.client = genai.GenerativeModel(model_name)
            logger.info(f"Initialized Google Gemini client with model {model_name}")
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: uv add google-generativeai")

    def _init_ollama(self):
        """Initialize Ollama client."""
        try:
            from ollama import Client
            base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.client = Client(host=base_url)
            logger.info(f"Initialized Ollama client at {base_url}")
        except ImportError:
            raise ImportError("ollama package not installed. Run: uv add ollama")

    def _init_xai(self):
        """Initialize xAI (Grok) client - uses OpenAI-compatible API."""
        try:
            from openai import OpenAI
            api_key = os.getenv('XAI_API_KEY')
            if not api_key:
                raise ValueError("XAI_API_KEY not found in environment variables")
            base_url = os.getenv('XAI_BASE_URL', 'https://api.x.ai/v1')
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info("Initialized xAI (Grok) client")
        except ImportError:
            raise ImportError("openai package not installed. Run: uv add openai")

    def generate(self, prompt: str, max_tokens: int = 4096, temperature: float = 0.7) -> Dict[str, any]:
        """
        Generate response from AI provider.

        Args:
            prompt: The prompt to send to the AI
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            {
                'success': bool,
                'text': str,
                'provider': str,
                'model': str,
                'error': str
            }
        """
        try:
            if self.provider == 'anthropic':
                return self._generate_anthropic(prompt, max_tokens, temperature)
            elif self.provider == 'openai':
                return self._generate_openai(prompt, max_tokens, temperature)
            elif self.provider == 'google':
                return self._generate_google(prompt, max_tokens, temperature)
            elif self.provider == 'ollama':
                return self._generate_ollama(prompt, max_tokens, temperature)
            elif self.provider == 'xai':
                return self._generate_xai(prompt, max_tokens, temperature)
        except Exception as e:
            logger.error(f"Error generating response from {self.provider}: {str(e)}")
            return {
                'success': False,
                'text': '',
                'provider': self.provider,
                'model': '',
                'error': str(e)
            }

    def _generate_anthropic(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, any]:
        """Generate response using Anthropic Claude."""
        model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')

        message = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            'success': True,
            'text': message.content[0].text,
            'provider': 'anthropic',
            'model': model,
            'error': ''
        }

    def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, any]:
        """Generate response using OpenAI."""
        model = os.getenv('OPENAI_MODEL', 'gpt-4o')

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            'success': True,
            'text': response.choices[0].message.content,
            'provider': 'openai',
            'model': model,
            'error': ''
        }

    def _generate_google(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, any]:
        """Generate response using Google Gemini."""
        model_name = os.getenv('GOOGLE_MODEL', 'gemini-1.5-pro')

        generation_config = {
            'max_output_tokens': max_tokens,
            'temperature': temperature,
        }

        response = self.client.generate_content(
            prompt,
            generation_config=generation_config
        )

        return {
            'success': True,
            'text': response.text,
            'provider': 'google',
            'model': model_name,
            'error': ''
        }

    def _generate_ollama(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, any]:
        """Generate response using Ollama."""
        model = os.getenv('OLLAMA_MODEL', 'llama3.1')

        response = self.client.generate(
            model=model,
            prompt=prompt,
            options={
                'num_predict': max_tokens,
                'temperature': temperature,
            }
        )

        return {
            'success': True,
            'text': response['response'],
            'provider': 'ollama',
            'model': model,
            'error': ''
        }

    def _generate_xai(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, any]:
        """Generate response using xAI Grok."""
        model = os.getenv('XAI_MODEL', 'grok-beta')

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            'success': True,
            'text': response.choices[0].message.content,
            'provider': 'xai',
            'model': model,
            'error': ''
        }
