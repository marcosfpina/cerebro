"""
Phantom Core GCP - Unified Google Cloud Platform integrations
"""

from .auth import get_credentials, get_project_id, validate_setup
from .billing import BillingAuditor
from .datastores import DataStoreManager
from .dialogflow import DialogflowCXManager
from .search import VertexAISearch

__all__ = [
    "BillingAuditor",
    "DataStoreManager",
    "DialogflowCXManager",
    "VertexAISearch",
    "get_credentials",
    "get_project_id",
    "validate_setup",
]
