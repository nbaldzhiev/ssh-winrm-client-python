"""
This module contains the implementation of the following task:

    We have a windows-based machine with enabled WinRM and a linux-based machine with enabled ssh.
    Need to create base class which have IP address property and child classes which will manage
    machines over ssh or WinRM with the following

    •    Power off/restart

    •    command line interface to execute command via ssh/powershell on remote machine

    •    Get Windows Defender parameters

    •    Get windows registry key
"""
from abc import ABCMeta, abstractmethod

import paramiko


class BaseClient(metaclass=ABCMeta):
    """This class serves as the base one for any inheriting clients, such as a SSH or WinRM one.
    It is an abstract class, meaning that the method log_in must be implemented in all inheriting
    classes."""

    def __init__(self, ip_address: str):
        self.ip_address = ip_address

    @abstractmethod
    def log_in(self, ip_address: str, username: str, password: str):
        pass


class SSHClient(BaseClient):
    """"""

    CLIENT = paramiko.SSHClient()

    def log_in(
        self, ip_address: str, username: str, password: str, port: int = 22, timeout: int = 60
    ):
        """

        Parameters
        ----------
        ip_address
        username
        password
        port
        timeout

        Returns
        -------

        """
        type(self).CLIENT.connect(
            hostname=ip_address,
            username=username,
            password=password,
            port=port,
            timeout=timeout,
        )

