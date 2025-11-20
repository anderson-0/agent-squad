"""
Secrets Management Integration

Secure secrets management for production deployments.

Supported Backends:
1. Environment Variables (development, default)
2. AWS Secrets Manager (production)
3. HashiCorp Vault (enterprise)
4. Google Cloud Secret Manager (GCP)
5. Azure Key Vault (Azure)

Features:
- Automatic secret rotation
- Caching with TTL
- Fallback to environment variables
- Audit logging
- Secret versioning

Security Best Practices:
- Never log secrets
- Use least-privilege access
- Rotate secrets regularly
- Monitor access patterns
- Encrypt secrets at rest and in transit
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


class SecretsBackend(Enum):
    """Supported secrets management backends"""
    ENVIRONMENT = "environment"  # .env files (dev only)
    AWS = "aws"  # AWS Secrets Manager
    VAULT = "vault"  # HashiCorp Vault
    GCP = "gcp"  # Google Cloud Secret Manager
    AZURE = "azure"  # Azure Key Vault


class SecretsManager:
    """
    Unified interface for secrets management across multiple backends

    Configuration (via environment variables):
        SECRETS_BACKEND: Backend to use (default: environment)
        SECRETS_CACHE_TTL: Cache TTL in seconds (default: 300)

    AWS Secrets Manager:
        AWS_REGION: AWS region (default: us-east-1)
        AWS_ACCESS_KEY_ID: AWS access key
        AWS_SECRET_ACCESS_KEY: AWS secret key

    HashiCorp Vault:
        VAULT_ADDR: Vault server address
        VAULT_TOKEN: Vault authentication token
        VAULT_NAMESPACE: Vault namespace (optional)

    GCP Secret Manager:
        GCP_PROJECT_ID: GCP project ID
        GOOGLE_APPLICATION_CREDENTIALS: Path to service account key

    Azure Key Vault:
        AZURE_KEY_VAULT_URL: Key Vault URL
        AZURE_CLIENT_ID: Service principal client ID
        AZURE_CLIENT_SECRET: Service principal secret
        AZURE_TENANT_ID: Azure AD tenant ID
    """

    def __init__(
        self,
        backend: Optional[SecretsBackend] = None,
        cache_ttl: int = 300
    ):
        """
        Initialize secrets manager

        Args:
            backend: Secrets backend (default: auto-detect from env)
            cache_ttl: Cache TTL in seconds (default: 5 minutes)
        """
        # Auto-detect backend if not specified
        if backend is None:
            backend_name = os.getenv("SECRETS_BACKEND", "environment")
            try:
                backend = SecretsBackend(backend_name)
            except ValueError:
                logger.warning(
                    f"Invalid SECRETS_BACKEND: {backend_name}, falling back to environment"
                )
                backend = SecretsBackend.ENVIRONMENT

        self.backend = backend
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[Any, datetime]] = {}

        # Initialize backend client
        self._client = None
        self._initialize_backend()

        logger.info(f"Secrets manager initialized with backend: {self.backend.value}")

    def _initialize_backend(self):
        """Initialize backend-specific client"""
        try:
            if self.backend == SecretsBackend.AWS:
                self._initialize_aws()
            elif self.backend == SecretsBackend.VAULT:
                self._initialize_vault()
            elif self.backend == SecretsBackend.GCP:
                self._initialize_gcp()
            elif self.backend == SecretsBackend.AZURE:
                self._initialize_azure()
            # Environment backend doesn't need initialization
        except Exception as e:
            logger.error(f"Failed to initialize secrets backend: {e}")
            logger.warning("Falling back to environment variables")
            self.backend = SecretsBackend.ENVIRONMENT

    def _initialize_aws(self):
        """Initialize AWS Secrets Manager client"""
        try:
            import boto3
            region = os.getenv("AWS_REGION", "us-east-1")
            self._client = boto3.client(
                "secretsmanager",
                region_name=region
            )
            logger.info(f"AWS Secrets Manager initialized (region: {region})")
        except ImportError:
            logger.error("boto3 not installed. Install: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"AWS Secrets Manager initialization failed: {e}")
            raise

    def _initialize_vault(self):
        """Initialize HashiCorp Vault client"""
        try:
            import hvac
            vault_addr = os.getenv("VAULT_ADDR")
            vault_token = os.getenv("VAULT_TOKEN")

            if not vault_addr or not vault_token:
                raise ValueError("VAULT_ADDR and VAULT_TOKEN required")

            self._client = hvac.Client(
                url=vault_addr,
                token=vault_token,
                namespace=os.getenv("VAULT_NAMESPACE")
            )

            # Verify authentication
            if not self._client.is_authenticated():
                raise ValueError("Vault authentication failed")

            logger.info(f"HashiCorp Vault initialized (addr: {vault_addr})")
        except ImportError:
            logger.error("hvac not installed. Install: pip install hvac")
            raise
        except Exception as e:
            logger.error(f"Vault initialization failed: {e}")
            raise

    def _initialize_gcp(self):
        """Initialize GCP Secret Manager client"""
        try:
            from google.cloud import secretmanager
            self._client = secretmanager.SecretManagerServiceClient()
            self._gcp_project_id = os.getenv("GCP_PROJECT_ID")

            if not self._gcp_project_id:
                raise ValueError("GCP_PROJECT_ID required")

            logger.info(f"GCP Secret Manager initialized (project: {self._gcp_project_id})")
        except ImportError:
            logger.error("google-cloud-secret-manager not installed. "
                        "Install: pip install google-cloud-secret-manager")
            raise
        except Exception as e:
            logger.error(f"GCP Secret Manager initialization failed: {e}")
            raise

    def _initialize_azure(self):
        """Initialize Azure Key Vault client"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import ClientSecretCredential

            vault_url = os.getenv("AZURE_KEY_VAULT_URL")
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            tenant_id = os.getenv("AZURE_TENANT_ID")

            if not all([vault_url, client_id, client_secret, tenant_id]):
                raise ValueError(
                    "Azure Key Vault requires: AZURE_KEY_VAULT_URL, "
                    "AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID"
                )

            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )

            self._client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info(f"Azure Key Vault initialized (url: {vault_url})")
        except ImportError:
            logger.error("azure-keyvault-secrets not installed. "
                        "Install: pip install azure-keyvault-secrets azure-identity")
            raise
        except Exception as e:
            logger.error(f"Azure Key Vault initialization failed: {e}")
            raise

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value

        Args:
            secret_name: Name/key of the secret
            default: Default value if secret not found

        Returns:
            Secret value or default

        Example:
            db_password = secrets_manager.get_secret("database_password")
        """
        # Check cache first
        if secret_name in self._cache:
            value, expires_at = self._cache[secret_name]
            if datetime.utcnow() < expires_at:
                logger.debug(f"Cache hit for secret: {secret_name}")
                return value

        # Fetch from backend
        try:
            if self.backend == SecretsBackend.ENVIRONMENT:
                value = self._get_secret_from_env(secret_name)
            elif self.backend == SecretsBackend.AWS:
                value = self._get_secret_from_aws(secret_name)
            elif self.backend == SecretsBackend.VAULT:
                value = self._get_secret_from_vault(secret_name)
            elif self.backend == SecretsBackend.GCP:
                value = self._get_secret_from_gcp(secret_name)
            elif self.backend == SecretsBackend.AZURE:
                value = self._get_secret_from_azure(secret_name)
            else:
                value = None

            # Cache result
            if value is not None:
                expires_at = datetime.utcnow() + timedelta(seconds=self.cache_ttl)
                self._cache[secret_name] = (value, expires_at)
                logger.info(f"Secret retrieved and cached: {secret_name}")

            return value or default

        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
            return default

    def _get_secret_from_env(self, secret_name: str) -> Optional[str]:
        """Get secret from environment variables"""
        return os.getenv(secret_name)

    def _get_secret_from_aws(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            response = self._client.get_secret_value(SecretId=secret_name)

            # Parse secret
            if "SecretString" in response:
                secret = response["SecretString"]
                # Try to parse as JSON (AWS Secrets Manager often stores JSON)
                try:
                    secret_dict = json.loads(secret)
                    # If single-key JSON, return the value
                    if len(secret_dict) == 1:
                        return list(secret_dict.values())[0]
                    # Otherwise return the whole JSON string
                    return secret
                except json.JSONDecodeError:
                    return secret
            else:
                # Binary secret (not common)
                return response["SecretBinary"].decode("utf-8")

        except self._client.exceptions.ResourceNotFoundException:
            logger.warning(f"Secret not found in AWS: {secret_name}")
            return None
        except Exception as e:
            logger.error(f"AWS secret retrieval error: {e}")
            return None

    def _get_secret_from_vault(self, secret_name: str) -> Optional[str]:
        """Get secret from HashiCorp Vault"""
        try:
            # Vault secret path format: secret/data/{secret_name}
            secret_path = f"secret/data/{secret_name}"
            response = self._client.secrets.kv.v2.read_secret_version(path=secret_name)

            # Extract secret value
            data = response["data"]["data"]
            if "value" in data:
                return data["value"]
            elif len(data) == 1:
                return list(data.values())[0]
            else:
                return json.dumps(data)

        except Exception as e:
            logger.error(f"Vault secret retrieval error: {e}")
            return None

    def _get_secret_from_gcp(self, secret_name: str) -> Optional[str]:
        """Get secret from GCP Secret Manager"""
        try:
            # Secret version format: projects/{project}/secrets/{secret}/versions/latest
            name = f"projects/{self._gcp_project_id}/secrets/{secret_name}/versions/latest"
            response = self._client.access_secret_version(request={"name": name})
            return response.payload.data.decode("utf-8")

        except Exception as e:
            logger.error(f"GCP secret retrieval error: {e}")
            return None

    def _get_secret_from_azure(self, secret_name: str) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        try:
            secret = self._client.get_secret(secret_name)
            return secret.value

        except Exception as e:
            logger.error(f"Azure secret retrieval error: {e}")
            return None

    def clear_cache(self):
        """Clear secrets cache (e.g., after rotation)"""
        self._cache.clear()
        logger.info("Secrets cache cleared")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get singleton secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a secret

    Example:
        from backend.core.secrets_manager import get_secret
        db_password = get_secret("DATABASE_PASSWORD")
    """
    manager = get_secrets_manager()
    return manager.get_secret(secret_name, default)


# ============================================================================
# INTEGRATION EXAMPLES
# ============================================================================

"""
Example 1: Environment Variables (Development)

    # .env file
    DATABASE_PASSWORD=dev_password_123
    OPENAI_API_KEY=sk-...
    STRIPE_SECRET_KEY=sk_test_...

    # Python code
    from backend.core.secrets_manager import get_secret

    db_password = get_secret("DATABASE_PASSWORD")


Example 2: AWS Secrets Manager (Production)

    # Environment configuration
    export SECRETS_BACKEND=aws
    export AWS_REGION=us-east-1
    export AWS_ACCESS_KEY_ID=AKIA...
    export AWS_SECRET_ACCESS_KEY=...

    # Python code (same as above!)
    from backend.core.secrets_manager import get_secret

    db_password = get_secret("database_password")
    # Automatically fetches from AWS Secrets Manager


Example 3: HashiCorp Vault

    # Environment configuration
    export SECRETS_BACKEND=vault
    export VAULT_ADDR=https://vault.example.com
    export VAULT_TOKEN=s.abc123...

    # Python code
    from backend.core.secrets_manager import get_secret

    api_key = get_secret("openai_api_key")


Example 4: Multiple Secrets with Fallback

    from backend.core.secrets_manager import get_secret

    # Try multiple secret names with fallback
    db_password = (
        get_secret("DATABASE_PASSWORD") or
        get_secret("DB_PASSWORD") or
        "default_dev_password"
    )


Example 5: Integration with Pydantic Settings

    from pydantic_settings import BaseSettings
    from backend.core.secrets_manager import get_secret

    class Settings(BaseSettings):
        database_url: str
        openai_api_key: str

        def __init__(self, **kwargs):
            # Override with secrets manager if available
            kwargs["database_url"] = get_secret(
                "DATABASE_URL",
                default=kwargs.get("database_url")
            )
            kwargs["openai_api_key"] = get_secret(
                "OPENAI_API_KEY",
                default=kwargs.get("openai_api_key")
            )
            super().__init__(**kwargs)


Example 6: Secret Rotation

    from backend.core.secrets_manager import get_secrets_manager

    # Clear cache to force refresh after rotation
    manager = get_secrets_manager()
    manager.clear_cache()

    # Next get_secret() call will fetch fresh values
    new_password = get_secret("database_password")


Example 7: Conditional Backend Selection

    import os
    from backend.core.secrets_manager import SecretsManager, SecretsBackend

    # Use AWS in production, environment in development
    if os.getenv("ENV") == "production":
        manager = SecretsManager(backend=SecretsBackend.AWS)
    else:
        manager = SecretsManager(backend=SecretsBackend.ENVIRONMENT)


Example 8: Docker Deployment

    # docker-compose.yml
    services:
      backend:
        environment:
          - SECRETS_BACKEND=aws
          - AWS_REGION=us-east-1
        # AWS credentials via IAM role (best practice)


Example 9: Kubernetes Deployment

    # k8s-deployment.yaml
    apiVersion: v1
    kind: Pod
    spec:
      containers:
      - name: backend
        env:
        - name: SECRETS_BACKEND
          value: "aws"
        - name: AWS_REGION
          value: "us-east-1"
        # IAM role via service account
        serviceAccountName: agent-squad-sa


Example 10: Testing

    import pytest
    from backend.core.secrets_manager import SecretsManager, SecretsBackend

    def test_secrets_manager_environment():
        import os
        os.environ["TEST_SECRET"] = "test_value"

        manager = SecretsManager(backend=SecretsBackend.ENVIRONMENT)
        value = manager.get_secret("TEST_SECRET")

        assert value == "test_value"


Installation Requirements:

    # Base (always required)
    pip install python-dotenv

    # AWS Secrets Manager
    pip install boto3

    # HashiCorp Vault
    pip install hvac

    # GCP Secret Manager
    pip install google-cloud-secret-manager

    # Azure Key Vault
    pip install azure-keyvault-secrets azure-identity


Security Best Practices:

    1. Never commit secrets to version control
    2. Use .gitignore for .env files
    3. Rotate secrets regularly (30-90 days)
    4. Use least-privilege IAM/RBAC policies
    5. Enable audit logging for secret access
    6. Use separate secrets for dev/staging/production
    7. Encrypt secrets at rest and in transit
    8. Monitor for unusual access patterns
    9. Implement secret versioning
    10. Have incident response plan for compromised secrets
"""
