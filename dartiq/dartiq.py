"""Implementation of Dartiq class"""

import os
import sys
import subprocess
from pprint import pprint


class Dartiq:
    """Dartiq Class

    This class can be used in 3rd party scripts that need to use ARTIQ.
    """

    def __init__(self,
                 image,
                 workspace,
                 home_path="~/.dartiq",
                 user_group=None,
                 xilinx_vivado_path=None,
                 xilinx_ise_path=None,
                 with_usb=True,
                 with_x=False,
                 no_stdin=True,
                 no_tty=False,
                 docker_options=None,
                 python_modules=None,
                 verbose=False,
                 environment=None,
                 mountpoints=None):
        """
        Args:
            image (str): DARTIQ image name.
            workspace (str): Path to the directory to be used as a workspace.
            home_path (str): Path to the directory to be used as containers' user home,
                defaults to `~/.dartiq`.
            user_group (str, optional): <user_id>:<group_id>, if none provided will
                default to current user data.
            xilinx_vivado_path (str, optional): Path to Xilinx Vivado. When given,
                adds specified directory as a read-only volume to the container
                and `settings64.sh` under `/opt/Xilinx/Vivado/settings64.sh`.
            xilinx_ise_path (str, optional): Path to Xilinx ISE. When given,
                adds specified directory as a read-only volume to the container.
            with_usb (bool, optional): Run container with USB support. Defaults to True.
                Adds `/dev/bus/usb` mountpoint and runs container in a priviledged mode.
            with_x (bool, optional): Run container with X support. Defaults to False.
                Adds `/tmp/.X11-unix` mountpoint and copies `DISPLAY` environment variable.
            no_stdin (bool, optional): Do not keep stdin open. Defaults to True.
            no_tty (bool, optional): Do not allocate pseudo-tty. Defaults to False.
            docker_options (list[str], optional): List of additional Docker options.
            python_modules (list[str], optional): List of paths to Python modules to be
                added to the containers' Python environemnt.
            verbose (bool, optional): Print final command running container.
                Defaults to False.
            environment (dict, optional): Dictionary with environment variables to be added
                to the container environment.
            mountpoints (list[str], optional): List of strings defining additional mountpoints
                to be added to the container.
        """
        if docker_options is None:
            docker_options = []
        if python_modules is None:
            python_modules = []
        if environment is None:
            environment = {}
        if mountpoints is None:
            mountpoints = []

        self.image = image
        self.environment = {**environment}
        self.python_path = ["/workspace"]
        self.volumes = ["/tmp:/tmp"]
        self.verbose = verbose
        self.artiq_src_set = False

        if user_group is None:
            user_group = f"{os.getuid()}:{os.getgid()}"

        for python_module in python_modules:
            self.add_python_module(python_module)

        for mountpoint in mountpoints:
            self.add_mountpoint(mountpoint)

        self.docker_options = [
            "--tty",
            "--rm",
            "--init",
            "--network=host",
            f"-u {user_group}",
            *docker_options
        ]

        if not no_stdin:
            self.docker_options.append("-i")
        if not no_tty:
            self.docker_options.append("-t")

        if workspace:
            workspace_abs = os.path.abspath(workspace)
            self.volumes.append(f"{workspace_abs}:/workspace")
        self.docker_options.append("--workdir /workspace")

        home_path = os.path.abspath(os.path.expanduser(home_path))
        if not os.path.exists(home_path):
            os.makedirs(home_path)
        self.volumes.append(f"{home_path}:/home")

        if xilinx_vivado_path:
            self.volumes.append(f"{xilinx_vivado_path}:{xilinx_vivado_path}:ro")
            self.volumes.append(
                f"{xilinx_vivado_path}/settings64.sh:/opt/Xilinx/Vivado/settings64.sh")
        if xilinx_ise_path:
            self.volumes.append(f"{xilinx_ise_path}:{xilinx_ise_path}:ro")

        if with_usb:
            self.volumes.append("/dev/bus/usb:/dev/bus/usb")
            self.docker_options.append("--privileged")

        if with_x:
            self.environment["DISPLAY"] = os.environ["DISPLAY"]
            self.volumes.append("/tmp/.X11-unix:/tmp/.X11-unix")

    def add_mountpoint(self, mountpoint):
        """Adds mountpoint to the container

        Mountpoints are passed in <directory>:<alias> form. If <directory> is not
        an absolute path, it is converted to one. <alias> is a nume under which
        directory will be mounted under `/mountpoints`.

        Args:
            mountpoint (str): mountpoint definition
        """
        if ":" in mountpoint:
            path, alias = mountpoint.split(":")
        else:
            path, alias = mountpoint, os.path.basename(mountpoint)
        if os.path.isabs(alias):
            self.volumes.append(f"{os.path.abspath(path)}:{alias}")
        else:
            self.volumes.append(f"{os.path.abspath(path)}:/mountpoints/{alias}")
            envvar_name = alias.replace(".", "_").upper()
            self.environment[envvar_name] = f"/mountpoints/{alias}"

    def add_python_module(self, module_path):
        """Adds Python module to the Python environment inside the container

        Module given by `module_path` is added to PYTHONPATH environment
        variable inside the container and `module_path` is added to container
        mountpoints.

        Args:
            module_path (str): path to the module

        Raises:
            ValueError: if module_path does not exist
        """
        module_path_norm = os.path.abspath(os.path.normpath(module_path))
        module_path, module_name = os.path.split(module_path_norm)
        if not os.path.exists(module_path_norm):
            raise ValueError(f"Path for module {module_name} does not exist ({module_path_norm})")
        self.volumes.append(f"{module_path_norm}:/modules/{module_name}")
        self.python_path.append(f"/modules/{module_name}")

    def _run_docker(self, stdin, stdout, stderr, run_command=None):
        self.environment["PYTHONPATH"] = ":".join(self.python_path)
        command = ["docker", "run", *self.docker_options]
        command += [
            f"--env {var_name}={var_value}" for var_name, var_value in self.environment.items()
        ]
        command += [f"-v {vol}" for vol in self.volumes]
        command += [self.image]
        final_command = []
        for element in command:
            final_command += element.split()
        if run_command is not None:
            final_command += ["-c", run_command]

        if self.verbose:
            pprint(final_command)

        ret = subprocess.run(final_command, stderr=stderr, stdin=stdin, stdout=stdout, check=False)
        return ret.returncode

    def run_development_shell(self):
        """Runs container with development shell active"""
        self._run_docker(stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

    def run_command(self, command, stdin=sys.stderr, stdout=sys.stdout, stderr=sys.stderr):
        """Runs specified command within the DARTIQ container

        By giving additional `stdin`, `stdout` and `stderr` arguments one can communicate with
        a process that is being run inside the container.

        Args:
            command (str): command to be run along with arguments
            stdin (file-like object, optional): Object acting as stdin. Defaults to sys.stderr.
            stdout (file-like object, optional): Object acting as stout. Defaults to sys.stdout.
            stderr (file-like object, optional): Object acting as sterr. Defaults to sys.stderr.

        Returns:
            int: exit code returned by process run inside the container
        """
        return self._run_docker(stdin=stdin, stdout=stdout, stderr=stderr, run_command=command)
