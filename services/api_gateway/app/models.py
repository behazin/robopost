"""ORM models for the API gateway service.

The API gateway relies on a shared set of SQLAlchemy models that are
exposed through the ``robopost_models`` package.  Importing and
re-exporting them here keeps the service's codebase decoupled from the
exact location of the model definitions while providing a local module
path (``services.api_gateway.app.models``) for internal imports.
"""

from robopost_models import (
    Base,
    ArticleStatus,
    Platform,
    PublicationStatus,
    Source,
    Destination,
    SourceDestinationMap,
    Admin,
    AdminDestinationMap,
    Article,
    PublicationLog,
)

__all__ = [
    "Base",
    "ArticleStatus",
    "Platform",
    "PublicationStatus",
    "Source",
    "Destination",
    "SourceDestinationMap",
    "Admin",
    "AdminDestinationMap",
    "Article",
    "PublicationLog",
]