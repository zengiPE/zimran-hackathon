"""All database tables, imported by app.db before create_all.

Person 1: put case/player/clue tables here too (or import your module below) so
create_all sees them.
"""

from app.events import Event  # noqa: F401
from app.payments.models import Payment  # noqa: F401
