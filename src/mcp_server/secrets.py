import os
import google.auth
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)

class GCPSecretManagerClient:
    """
    GCP Secret Manager Client using Object-Oriented design.
    Implicitly resolves project_id using Google Application Default Credentials (ADC).
    """
    def __init__(self) -> None:
        try:
            # google.auth.default() implicitly resolves credentials and project_id from ADC
            self.credentials, self.project_id = google.auth.default()
            if not self.project_id:
                # Fallback to local environment check if not returned by ADC default
                self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
            
            if not self.project_id:
                raise ValueError("Could not resolve Project ID from Application Default Credentials or environment variables.")
                
            self.client = secretmanager.SecretManagerServiceClient(credentials=self.credentials)
            logger.info(f"Initialized GCPSecretManagerClient for Project ID: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize GCPSecretManagerClient: {e}")
            raise

    def get_secret(self, secret_id: str, version_id: str = "latest") -> str:
        """
        Retrieves the secret value from Secret Manager.
        """
        try:
            secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
            response = self.client.access_secret_version(name=secret_name)
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id} (version {version_id}): {e}")
            raise
