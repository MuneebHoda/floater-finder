"""The patched Pillow release frozen for new real-image experiments."""

PILLOW_VERSION = "12.3.0"


def require_image_runtime():
    from PIL import __version__
    if __version__ != PILLOW_VERSION:
        raise RuntimeError(
            f"This image protocol requires Pillow {PILLOW_VERSION}; found {__version__}. "
            "Use the newly prepared private environment; preserve legacy artifacts."
        )
    return __version__
