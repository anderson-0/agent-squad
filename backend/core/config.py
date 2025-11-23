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

    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes
    CACHE_PREFIX: str = "agent_squad"
    # Cache TTLs (seconds) - Data-driven: adjust based on cache_metrics
    CACHE_USER_TTL: int = 300  # 5 minutes
    CACHE_ORG_TTL: int = 600  # 10 minutes
    CACHE_SQUAD_TTL: int = 300  # 5 minutes
    CACHE_TASK_TTL: int = 30  # 30 seconds (agents may complete tasks quickly)
    CACHE_EXECUTION_STATUS_TTL: int = 10  # 10 seconds

    # Cache Metrics Configuration
    CACHE_METRICS_ENABLED: bool = True  # Track cache performance metrics
    CACHE_METRICS_WINDOW: int = 3600  # Track metrics for last 1 hour

    # SSE Configuration
    SSE_QUEUE_SIZE: int = Field(default=1000, ge=100, le=10000)  # SSE queue size per connection
    SSE_HEARTBEAT_INTERVAL: int = Field(default=15, ge=10, le=120)  # Heartbeat interval in seconds

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

    # Groq (optional)
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")

    # Ollama (local LLM - recommended for development)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="llama3.2", env="OLLAMA_MODEL")

    # GitHub Integration (for MCP tools)
    GITHUB_TOKEN: str = Field(default="", env="GITHUB_TOKEN")

    # Jira Integration (for MCP tools)
    JIRA_URL: str = Field(default="", env="JIRA_URL")
    JIRA_USERNAME: str = Field(default="", env="JIRA_USERNAME")
    JIRA_API_TOKEN: str = Field(default="", env="JIRA_API_TOKEN")

    # E2B Sandbox (for secure code execution)
    E2B_API_KEY: str = Field(default="", env="E2B_API_KEY")

    # Git Sandbox Configuration (E2B-based git operations)
    GIT_SANDBOX_TIMEOUT: int = 300  # 5 minutes
    GIT_SANDBOX_MAX_RETRIES: int = 3  # Max retry attempts for push
    GIT_SANDBOX_TTL: int = 3600  # 1 hour sandbox TTL
    GITHUB_DEFAULT_BRANCH: str = "main"  # Default branch for operations

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

    # Agent Framework Configuration
    USE_AGNO_AGENTS: bool = True  # Deprecated: Agno is now the only agent implementation

    # Message Bus Configuration
    MESSAGE_BUS: str = "nats"  # Options: "memory" or "nats" (default: nats for production)
    NATS_URL: str = "nats://localhost:4222"
    NATS_STREAM_NAME: str = "agent-messages"
    NATS_MAX_MSGS: int = 1_000_000  # 1M messages
    NATS_MAX_AGE_DAYS: int = 7  # 7 days retention
    NATS_CONSUMER_NAME: str = "agent-processor"

    # MCP Tools Configuration
    MCP_TOOLS_ENABLED: bool = True  # Enable/disable MCP tools globally
    MCP_CONFIG_PATH: str = ""  # Custom path to mcp_tool_mapping.yaml (optional)
    MCP_LOG_LEVEL: str = "INFO"  # MCP-specific logging level

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Create global settings instance
settings = Settings()
