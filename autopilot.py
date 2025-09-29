# Thin shim so tests can import `from autopilot import Autopilot`
from termnet.autopilot import Autopilot  # re-export

__all__ = ["Autopilot"]
