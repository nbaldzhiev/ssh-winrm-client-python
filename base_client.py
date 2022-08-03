"""This module contains the implementation of the base client."""
from __future__ import annotations
from abc import ABCMeta, abstractmethod


class BaseClient(metaclass=ABCMeta):
    """Base class for any inheriting clients, such as a SSH or WinRM one."""

    def __init__(self, ip_address: str, username: str, password: str):
        self.ip_address = ip_address
        self.username = username
        self.password = password

    @abstractmethod
    def log_in(self):
        pass

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass
