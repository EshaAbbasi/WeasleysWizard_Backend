from .base import BaseModel

# Import model modules so all tables are registered for Alembic autogeneration.
from . import user
from . import shop
from . import product
from . import order
from . import item
from . import review

__all__ = ["BaseModel"]