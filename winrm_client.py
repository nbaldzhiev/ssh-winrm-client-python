"""This class contains the implementation of the WinRM client."""
from __future__ import annotations
import logging

import winrm

from base_client import BaseClient
from enums import WindowsCommands, RegistryRootKey

logging.basicConfig(level=logging.INFO)


class WinRMClient(BaseClient):
    """This class serves as an abstraction of a WinRM client.

    Note: The commands in this class are tested against Windows 7 Ultimate 6.1.7601 SP 1 Build 7601
    so there could be differences with other Windows versions.
    """

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


# Example calls
winrm_client = WinRMClient(ip_address='192.168.100.4', username='Gaming', password='nenko9000')
ipconfig_output = winrm_client.execute_command('ipconfig')
winrm_client.execute_command('WmiObject Win32_ComputerSystem', is_power_shell=True)
# winrm_client.reboot()
winrm_client.shutdown(immediately=True)

