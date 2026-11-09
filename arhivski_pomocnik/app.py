"""Sestava glavnega razreda iz ločenih funkcionalnih sklopov."""

from .mixins.core import CoreMixin
from .mixins.download import DownloadMixin
from .mixins.transcription import TranscriptionMixin
from .mixins.archive import ArchiveMixin
from .mixins.import_export import ImportExportMixin
from .mixins.merge import MergeMixin
from .mixins.live_database import LiveDatabaseMixin

from .version import VERSION


class MatriculaApp(
    CoreMixin,
    DownloadMixin,
    TranscriptionMixin,
    ArchiveMixin,
    ImportExportMixin,
    MergeMixin,
    LiveDatabaseMixin,
):
    """Glavna aplikacija; posamezni sklopi so v datotekah mixins/."""
    pass