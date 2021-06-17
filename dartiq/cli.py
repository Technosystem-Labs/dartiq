#!/usr/bin/env python3
"""Command-line interface for DARTIQ script"""

import argparse
import os
import json
from dartiq import Dartiq
from dartiq import __version__


DEFAULT_IMAGE = "technosystem/dartiq:latest"

# https://stackoverflow.com/a/10551190
class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, help=None, **kwargs):
        if not default and envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        help = f"{help} (env. variable: {envvar})" if help else f"(env. variable: {envvar})"
        super(EnvDefault, self).__init__(default=default, required=required, help=help,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


def add_container_arguments(parser):
    parser.add_argument("--image", action=EnvDefault, envvar="DARTIQ_IMAGE", required=False,
        help="name of the ARTIQ image to use")
    parser.add_argument("-o", "--docker-option", dest="docker_options", action="append", default=[],
        required=False, help="option passed to Docker run, must be in quotes, may be given multiple\
         times")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, required=False,
        help="be more informative on what is going on")


def add_run_arguments(parser):
    parser.add_argument("--without-usb", action="store_true",
        default=False, help="do not add USB support to the container")
    parser.add_argument("--without-x", action="store_true",
        default=False, help="do not enable X apps in the container")
    parser.add_argument("--workspace", action=EnvDefault, envvar="DARTIQ_WORKSPACE", required=False,
        default="./", help="path to be used as a in-container user home directory (defaults to\
             Docker volume `dartiq_home`")
    parser.add_argument("--home-path", action=EnvDefault, envvar="DARTIQ_HOME_PATH", required=False,
        help="path to be used as a in-container user home directory (defaults to Docker volume\
             `dartiq_home`")
    parser.add_argument("-m", "--add-module", dest="python_modules", action="append", default=[],
        help="adds Python module under given path, may be given multiple times")
    parser.add_argument("-e", "--copy-env-var", action="append", default=[],
        help="copies environment variable of given name to the containers' environment, may be\
             given multiple times")
    parser.add_argument("-g", "--add-env-var", action="append", default=[],
        help="adds environment variables <VARIABLE>=<VALUE> to containers' environment, may be\
             given multiple times")
    parser.add_argument("--xilinx-vivado-path", action=EnvDefault, envvar="XILINX_VIVADO",
        required=False, help="use Xilinx Vivado installed under given path")
    parser.add_argument("--xilinx-ise-path", action=EnvDefault, envvar="XILINX_ISE", required=False,
        help="use Xilinx ISE installed under given path")
    parser.add_argument("-u", "--user-group", dest="user_group", required=False,
        help="user and group for the user in the container (e.g. 1000:1000), must be numeric,\
             defaults to current user")
    parser.add_argument("-c", "--config", required=False,
        help="Load configuration from a given JSON file. Command-line options override\
             configuration file settings or expand them (in case of additional modules, Docker\
             options and environment variables.")
    parser.add_argument("--ignore-config", action="store_true",
        default=False, help="ignore default `dartiq.json` configuration file")
    parser.add_argument("-f", "--add-mountpoint", dest="mountpoints", action="append", default=[],
        help="add mountpoint to /mountpoints, optionally give alias after ':'")
    parser.add_argument("--no-tty", action="store_true",
        default=False, help="do not allocate a pseudo-tty")
    parser.add_argument("--no-stdin", action="store_true",
        default=False, help="do not keep STDIN open even if not attached")


def add_subparsers(parser):
    subparsers = parser.add_subparsers(title="commands", dest="action")

    # Development shell
    dev_shell_parser = subparsers.add_parser("shell", help="open development shell")
    add_container_arguments(dev_shell_parser)
    add_run_arguments(dev_shell_parser)

    # Running command
    command_parser = subparsers.add_parser("run", help="run specified command in the container")
    add_container_arguments(command_parser)
    add_run_arguments(command_parser)
    command_parser.add_argument("command", nargs='+',
        help="command with arguments to be exected in the container")

    # Obtaining version information
    command_parser = subparsers.add_parser("version", help="display version information")
    add_container_arguments(command_parser)
    add_run_arguments(command_parser)


def main():
    parser = argparse.ArgumentParser()
    add_subparsers(parser)
    args = parser.parse_args()

    with_x = "DISPLAY" in os.environ

    settings = {
        "image": DEFAULT_IMAGE,
        "workspace": "./",
        "home_path": "~/.dartiq",
        "user_group": None,
        "xilinx_vivado_path": None,
        "xilinx_ise_path": None,
        "with_usb": True,
        "with_x": with_x,
        "no_stdin": False,
        "no_tty": False,
        "docker_options": [],
        "python_modules": [],
        "verbose": False,
        "environment": {},
        "mountpoints": [],
        "copy_env_var": [],
        "add_env_var": []
    }
    config_file = {}

    if os.path.exists("dartiq.json") and not args.ignore_config:
        with open("dartiq.json", 'r') as f:
            config_file = json.load(f)

    if getattr(args, "config", None):
        with open(args.config, 'r') as f:
            config_file = json.load(f)

    for key in [*settings.keys(), ]:
        if isinstance(settings[key], list):
            settings[key] += getattr(args, key, [])
            settings[key] += config_file.get(key, [])
        else:
            if config_file.get(key, None):
                settings[key] = config_file[key]
            if getattr(args, key, None):
                settings[key] = getattr(args, key)

    copy_env_var = settings.pop("copy_env_var")
    settings["environment"].update({k: os.environ[k] for k in copy_env_var})
    add_env_var = settings.pop("add_env_var")
    settings["environment"].update({k:v for k, v in [x.split("=") for x in add_env_var]})

    dartiq = Dartiq(**settings)

    if args.action == "shell":
        dartiq.run_development_shell()
    elif args.action == "run":
        retcode = dartiq.run_command(" ".join(args.command))
        exit(retcode)
    elif args.action == "version":
        print(f"DARTIQ Version: {__version__}\n")
        dartiq.run_command("version-info")
    else:
        parser.print_help()
