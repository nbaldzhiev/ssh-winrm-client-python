from enum import Enum


class LinuxCommands(Enum):
    """Constants for Linux commands. Please note that these commands were tested on
    Ubuntu 18.04.5 LTS and there could be differences in other distributions/versions."""
    REBOOT = 'sudo reboot'
    SHUTDOWN = 'sudo shutdown -h now'


class WindowsCommands(Enum):
    REBOOT = 'shutdown -r'
    SHUTDOWN = 'shutdown -s'
    REGISTER_QUERY = 'reg query'


class RegistryRootKey(Enum):
    HKEY_CLASSES_ROOT = 'HKER'
    HKEY_CURRENT_USER = 'HKCU'
    HKEY_LOCAL_MACHINE = 'HKLM'
    HKEY_USERS = 'HKU'
    HKEY_CURRENT_CONFIG = 'HKCC'
