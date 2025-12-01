"""Git operation implementations. Token-efficient exports."""
from .clone import CloneOperation
from .status import StatusOperation
from .diff import DiffOperation
from .pull import PullOperation
from .push import PushOperation

__all__ = [
    "CloneOperation",
    "StatusOperation",
    "DiffOperation",
    "PullOperation",
    "PushOperation",
]
