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
from __future__ import annotations
import time
import re
from typing import Tuple
from abc import ABCMeta, abstractmethod
import logging

import paramiko

from enums import LinuxCommands

logging.basicConfig(level=logging.INFO)


class BaseClient(metaclass=ABCMeta):
    """This class serves as the base one for any inheriting clients, such as a SSH or WinRM one.
    It is an abstract class, meaning that the method log_in must be implemented in all inheriting
    classes."""

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


class SSHClient(BaseClient):
    """This class serves as an abstraction of a SSH client.

    Note: The shell commands in this class are tested on Ubuntu 18.04.5 LTS and the behaviour of
    the prompt is based on that distribution, so there could be some differences in other
    distributions, even though the regular expressions used should be general enough to ensure
    they run on all distros.
    """

    PROMPT_POLL_INTERVAL = 0.5  # seconds
    PROMPT_POLL_TIMEOUT = 10  # seconds
    WRONG_PASSWORD_TIMEOUT = 5  # seconds
    BYTES_TO_READ = 1024

    def __init__(self, ip_address: str, username: str, password: str):
        super().__init__(ip_address=ip_address, username=username, password=password)

    def __enter__(self) -> SSHClient:
        """Creates the SSH client, logs in the host and returns the class instance upon entering
        the context manager"""
        self.client = paramiko.SSHClient()
        # Load host keys from the system's "known hosts" file
        self.client.load_system_host_keys()
        self.log_in()
        self.shell = self.client.invoke_shell()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the SSH connection upon exiting the context manager."""
        if self.client:
            self.client.close()
            logging.info('Successfully closed the SSH session.')

    def _wait_for_shell_password_prompt(self):
        """Waits for the password prompt in the shell."""
        t_now = time.time()
        # Wait PROMPT_POLL_TIMEOUT until the password prompt message appears.
        while time.time() < t_now + type(self).PROMPT_POLL_TIMEOUT:
            if not self.shell.recv_ready():
                time.sleep(type(self).PROMPT_POLL_INTERVAL)
            elif not re.match(r'.*password.*', str(self.shell.recv(type(self).BYTES_TO_READ))):
                time.sleep(type(self).PROMPT_POLL_INTERVAL)
            else:
                break
            continue
        else:
            raise UserWarning('No password prompt!')

    def _wait_for_shell_password_return_prompt(self):
        """Waits for the shell to return to the caller after entering the password."""
        t_now = time.time()
        # Wait for up to WRONG_PASSWORD_TIMEOUT seconds to make sure the prompt does not return a
        # "wrong password" message, which in most Linux distros is simply returning the prompt again
        while time.time() < t_now + type(self).WRONG_PASSWORD_TIMEOUT:
            if not self.shell.recv_ready():
                time.sleep(type(self).PROMPT_POLL_INTERVAL)
                continue
            elif re.match(r'.*password.*', str(self.shell.recv(type(self).BYTES_TO_READ)).lower()):
                raise UserWarning('Incorrect sudo password!')

            time.sleep(type(self).PROMPT_POLL_INTERVAL)

        # Wait until the command finishes to prevent closing the session prematurely in __exit__
        self.shell.status_event.wait(timeout=type(self).PROMPT_POLL_TIMEOUT)


    def log_in(self, port: int = 22, timeout: int = 60):
        """Logs in the host via SSH."""
        if not self.client.get_transport() or not self.client.get_transport().is_alive():
            try:
                self.client.connect(
                    hostname=self.ip_address,
                    username=self.username,
                    password=self.password,
                    port=port,
                    timeout=timeout,
                )
            except Exception as e:
                logging.error('Could not log in host %s!', self.ip_address)
                raise e
            else:
                if self.client.get_transport():
                    if self.client.get_transport().is_alive():
                        logging.info('Successfully logged in host %s!', self.ip_address)

    def execute_command(self, command: str) -> Tuple:
        """Executes a command against the connected host. Raises an exception if the command
        execution was unsuccessful.
        Note: this method is for non-interactive commands, which do not prompt the user for input,
        such as 'ls', 'pwd', etc.

        Parameters
        ----------
        command : str
            A non-interactive command to execute, i.e. 'ls', 'pwd', 'date', etc.

        Returns
        -------
        Tuple
            A tuple containing the stdin, stdout and stderr channels in this order.
        """
        stdin, stdout, stderr = self.client.exec_command(command)
        # If the exit code is not 0, log an error message and raise an exception
        if stdout.channel.recv_exit_status():
            logging.error(
                'The command "%s" was not successful and returned exit code %s!',
                command,
                stdout.channel.recv_exit_status(),
            )
            raise UserWarning(f'The command "{command}" was not successful!')
        logging.info('Successful execution of command "%s"!', command)

        return stdin, stdout, stderr

    def reboot(self):
        """Reboots the host."""
        self.shell.send(str.encode(f'{LinuxCommands.REBOOT.value}\n'))
        self._wait_for_shell_password_prompt()
        # Enter password
        self.shell.send(str.encode(f'{self.password}\n'))
        self._wait_for_shell_password_return_prompt()

        logging.info('Successfully rebooted host %s!', self.ip_address)

    def shutdown(self):
        """Shuts down the host."""
        self.shell.send(str.encode(f'{LinuxCommands.SHUTDOWN.value}\n'))
        self._wait_for_shell_password_prompt()
        # Enter password
        self.shell.send(str.encode(f'{self.password}\n'))
        self._wait_for_shell_password_return_prompt()

        logging.info('Successfully shut down host %s!', self.ip_address)
