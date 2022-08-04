# Acronis Interview Task - WinRM/SSH client

A repository containing my solution to the home coding interview task given as part of the Senior Python Developer in Test (Advanced Management) position:

## Task Description

Python home task:

 We have a windows-based machine with enabled WinRM and a linux-based machine with enabled ssh. Need to create base class which have IP address property and child classes which will manage machines over ssh or WinRM with the following

•    Power off/restart

•    command line interface to execute command via ssh/powershell on remote machine

•    Get Windows Defender parameters

•    Get windows registry key

## Solution explanation

Three modules are created:
* base_client.py contains a base class for any inheriting clients. Implemented as an abstract class, it requires any inheriting classes to implement its methods. It has four abstract classes: `log_in()`, `execute_command()`, `reboot()`, and `shutdown()`.
* ssh_client.py contains a class implementation of a SSH client. It uses external package `paramiko` for an SSH implementation in Python. The class is written as a context-manager, so it needs to be used like that in order to ensure that sessions are opened and closed properly.
* winrm_client.py contains a class implementation of a WinRM client. It uses external package `pywinrm` for a WinRM implementation in Python. It is not written as a context-manager as closing of the sessions seems to be done automatically by `pywinrm`

> **_NOTE:_**  The SSH client was implemented by testing against a Ubuntu 18.04.5 LTS machine and the WinRM client - against a Windows 7 Ultimate 6.1.7601 SP 1 Build 7601 machine, so there could be differences in how the clients work against other versions/distributions of Linux and Windows. I have aimed to create the commands as generic as possible to ensure they'll run on any version of Linux/Windows.

## Usage

It's recommended to create a python virtual environment using Python 3.7.9+ and install the dependencies in the file requirements.txt to ensure that all required packages are available. The projects uses two external packages:

* [paramiko](https://www.paramiko.org/) - providing an SSH client implementation in python;
* [pywinrm](https://github.com/diyan/pywinrm) - providing a WinRM client implementation in python.

