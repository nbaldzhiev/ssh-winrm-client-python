from enum import Enum


class LinuxCommands(Enum):
    """Constants for Linux commands. Please note that these commands were tested on
    Ubuntu 18.04.5 LTS and there could be differences in other distributions/versions."""
    REBOOT = 'sudo reboot'
    SHUTDOWN = 'sudo shutdown -h now'
