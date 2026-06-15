"""Rules that prevent silent local-to-cloud data transfer."""

from diskwise.ai.schemas import ProviderType


class CloudConsentRequiredError(PermissionError):
    """Raised when cloud use was not explicitly authorized."""


def require_cloud_consent(
    provider_type: ProviderType,
    cloud_consent: bool,
) -> None:
    """Reject cloud calls unless the caller records explicit consent."""
    if (
        provider_type is ProviderType.OPENAI_COMPATIBLE
        and not cloud_consent
    ):
        raise CloudConsentRequiredError(
            "云端调用必须由用户显式授权，不能从本地模型自动回退"
        )

