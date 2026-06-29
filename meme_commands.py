try:
    from .meme_studio.commands import *  # noqa: F401,F403
except ImportError:
    from meme_studio.commands import *  # noqa: F401,F403
