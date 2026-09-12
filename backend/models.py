from enum import Enum

class ApplianceState(str, Enum):
    RUNNING = "RUNNING"
    OFF = "OFF"
    ShED = "SHED"