"""
Configuration management using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    ENV: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Agent Squad"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # BetterAuth (optional for development)
    BETTERAUTH_SECRET: str = Field(default="", env="BETTERAUTH_SECRET")

    # Stripe (optional for development)
    STRIPE_SECRET_KEY: str = Field(default="", env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str = Field(default="", env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", env="STRIPE_WEBHOOK_SECRET")
    STRIPE_STARTER_PRICE_ID: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""

    # OpenAI (optional for development)
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_ORG_ID: str = ""

    # Anthropic (optional)
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")

    # Pinecone (optional for development)
    PINECONE_API_KEY: str = Field(default="", env="PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = Field(default="", env="PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: str = "agent-squad"

    # Inngest (optional for development)
    INNGEST_EVENT_KEY: str = Field(default="", env="INNGEST_EVENT_KEY")
    INNGEST_SIGNING_KEY: str = Field(default="", env="INNGEST_SIGNING_KEY")

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    def get_allowed_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS if isinstance(self.ALLOWED_ORIGINS, list) else [self.ALLOWED_ORIGINS]

    # MCP Servers
    MCP_GIT_SERVER_URL: str = "http://localhost:5001"
    MCP_JIRA_SERVER_URL: str = "http://localhost:5002"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Monitoring
    ENABLE_METRICS: bool = True
    SENTRY_DSN: str = ""

    # Feature Flags
    ENABLE_CLI: bool = False
    ENABLE_WEBHOOKS: bool = True

    # Message Bus Configuration
    MESSAGE_BUS: str = "memory"  # Options: "memory" or "nats"
    NATS_URL: str = "nats://localhost:4222"
    NATS_STREAM_NAME: str = "agent-messages"
    NATS_MAX_MSGS: int = 1_000_000  # 1M messages
    NATS_MAX_AGE_DAYS: int = 7  # 7 days retention
    NATS_CONSUMER_NAME: str = "agent-processor"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Create global settings instance
settings = Settings()
