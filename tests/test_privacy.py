import sqlite3

import pytest
from pydantic import SecretStr

from diskwise.ai.schemas import ProviderType
from diskwise.config.settings import AppSettings
from diskwise.database.migrations import initialize_database
from diskwise.safety.privacy_policy import (
    CloudConsentRequiredError,
    require_cloud_consent,
)


def test_cloud_requires_explicit_consent():
    with pytest.raises(CloudConsentRequiredError):
        require_cloud_consent(ProviderType.OPENAI_COMPATIBLE, False)


def test_api_key_is_not_written_to_database(tmp_path):
    secret = "not-for-storage"
    settings = AppSettings(
        cloud_enabled=True,
        cloud_base_url="https://example.test/v1",
        cloud_api_key=SecretStr(secret),
    )
    database_path = tmp_path / "diskwise.db"
    initialize_database(database_path)

    assert secret not in repr(settings)
    with sqlite3.connect(database_path) as connection:
        dump = "\n".join(connection.iterdump())
    assert secret not in dump

