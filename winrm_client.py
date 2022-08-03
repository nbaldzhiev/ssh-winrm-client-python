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
from typing import List
from abc import ABCMeta, abstractmethod
import logging

import paramiko
import winrm

from enums import LinuxCommands, WindowsCommands, RegistryRootKey

logging.basicConfig(level=logging.INFO)


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

    def execute_command(self, command: str) -> List:
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
        List
            The output of the command as a list of strings.
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
        logging.info(
            'Successful execution of command "%s"!\n Command output: %s',
            command,
            stdout.readlines(),
        )

        return stdout.readlines()

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


class WinRMClient(BaseClient):
    """This class serves as an abstraction of a WinRM client.

    Note:
    """

    PROMPT_POLL_INTERVAL = 0.5  # seconds
    PROMPT_POLL_TIMEOUT = 10  # seconds
    WRONG_PASSWORD_TIMEOUT = 5  # seconds
    BYTES_TO_READ = 1024

    def __init__(self, ip_address: str, username: str, password: str):
        super().__init__(ip_address=ip_address, username=username, password=password)
        self.client = self.log_in()
        logging.info('Successfully logged in host %s!', self.ip_address)

    def log_in(self):
        """Logs in to the host via WinRM."""
        try:
            client = winrm.Session(self.ip_address, auth=(self.username, self.password))
        except Exception as e:
            logging.error('Could not log in host %s!', self.ip_address)
            raise e
        else:
            logging.info('Successfully logged in host %s!', self.ip_address)
            return client

    def execute_command(self, command: str, is_power_shell: bool = False) -> str:
        """Executes a command against the connected host. Raises an exception if the command
        execution was unsuccessful.

        Parameters
        ----------
        command : str
            A command to execute, i.e. 'ipconfig', 'date/T', 'time/T', etc.
        is_power_shell : bool
            Determines whether the command is a PowerShell one or not. Defaults to False.

        Returns
        -------
        str
            The output of the command as a decoded string.
        """
        if not is_power_shell:
            response = self.client.run_cmd(command)
        else:
            response = self.client.run_ps(command)
        # If the exit code is not 0, log an error message and raise an exception
        if response.status_code:
            logging.error(
                'The command "%s" was not successful and returned exit code %s!',
                command,
                response.status_code,
            )
            raise UserWarning(f'The command "{command}" was not successful!')
        logging.info(
            'Successful execution of command "%s"!\n Command output: %s',
            command,
            response.std_out.decode('UTF-8'),
        )

        return response.std_out.decode('UTF-8')

    def reboot(self, immediately: bool = False):
        """Reboots the host.

        Parameters
        ----------
        immediately : bool
            Set to true in order to trigger a reboot immediately as Windows machines have a
            1 minute delay before actually rebooting. Defaults to false.
        """
        command = WindowsCommands.REBOOT.value
        if immediately:
            command += ' -t 0'
        self.execute_command(command=command)
        logging.info('Successfully rebooted host %s!', self.ip_address)

    def shutdown(self, immediately: bool = False):
        """Shutdown the host.

        Parameters
        ----------
        immediately : bool
            Set to true in order to trigger a shut down immediately as Windows machines have a
            1 minute delay before actually shutting down. Defaults to false.
        """
        command = WindowsCommands.SHUTDOWN.value
        if immediately:
            command += ' -t 0'
        self.execute_command(command=command)

        logging.info('Successfully shut down host %s!', self.ip_address)

    def get_subkeys_and_entries_for_root_registry_key(self, root_key: RegistryRootKey) -> str:
        """Retrieves and returns the subkeys and entries for a given root registry key.

        Parameters
        ----------
        root_key : RegistryRootKey
            The root key to query for.

        Returns
        -------
        str
            All subkeys and entries for the given root key.
        """
        res = self.execute_command(WindowsCommands.REGISTER_QUERY.value + f' {root_key.value}')
        return res
