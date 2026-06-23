"""Application service interfaces."""

from ai_stock.services.local_mock_ingestion import LocalMockIngestionService
from ai_stock.services.data_persistence import LocalDataPersistenceService

__all__ = ["LocalDataPersistenceService", "LocalMockIngestionService"]
