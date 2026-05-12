"""ORM models. Import here so Base.metadata sees every model on first import."""

from tikko.models.device import Device

__all__ = ["Device"]
