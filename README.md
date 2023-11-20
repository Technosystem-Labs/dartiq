> [!WARNING]
> **DARTIQ project is not developed anymore. Please use Nix flakes instead.**

Dockerized ARTIQ
===

This repository provides tools to operate with ARTIQ in dockerized environment. 
It makes work with ARTIQ independent from external binary repositories.

What you get with the image is a full ARTIQ installation that can be 
instantiated and used as a Docker container. `dartiq` script acts as an 
interface between you and Docker and makes use of dockerized ARTIQ 
user-friendly. 

## Installing

DARTIQ script is available on PyPI:

```bash
python3 -m pip install dartiq
```

## Running an ARTIQ-enabled shell

For example, to get a shell with ARTIQ installed just type `dartiq shell`. 
This will drop you in the shell with your current working directory mounted as 
`/workspace` directory in the container. It can be overridden using `--workspace`
option.

## Running single command

You can run a single command in Docker container by using `run` option, 
e.g. `dartiq run "artiq_run ./experiment.py"`. Please note that your command 
must be taken into quotes!

By default, inside the container, you'll act as a user of `uid` and `gid` of your 
own. It should prevent you from having permission problems. If you need to use 
different `uid` and `gid`, use `--user-group` option.

**CAUTION:** To be able to access USB devices inside the container, 
`/dev/bus/usb` is mounted and the container is run in **privileged** mode 
(You were warned!). This can be disabled by adding `--without-usb` option.


## Xilinx Vivado support

To be able to build ARTIQ firmware for Xilinx FPGAs, you'll need to have Xilinx
Vivado suite available inside the container. 
If you source Xilinx Vivado `settings64.sh` (you need to have Vivado installed
on your host system) prior to running `dartiq`, a path under which Vivado is 
installed will be mounted in the container and your Vivado installation will be 
ready to use.

If you need provide license information to the Xilinx Vivado, you can pass an 
appropriate information using either `--copy-env-var XILINXD_LICENSE_FILE` 
option, which copies given variable to container environment, or by adding new 
variable with `--add-env-var XILINXD_LICENSE_FILE=<...>`.

## External Python modules

It may happen that you want to add some Python module to be used inside the 
container. Notably, a slightly modified version of ARTIQ, MiSoC or Migen may be 
of your interest. You can do it with `--add-module <MODULE PATH>` option. 
This will mount your module in `/modules` directory and add appropriate entry 
in the `PYTHONPATH`.

**CAUTION:** If you want to use ARTIQ as an additional module, it is advised to use
commit used to build DARTIQ image as a base commit to avoid dependency problems.
You can always check ARTIQ commit used to build an image with `dartiq version`
command.

## Mounting files to container

If, during run time, you need files or directories that are not beneath current 
working directory (i.e. are not in your workspace), you can mount them using 
`-f` command line option. This will mount selected file/directory under 
`/mountpoints` inside the container. Additionally, in the container environment, 
a variable will be created named after file/directory basename with dots 
replaced with underscores and converted to uppercase. This variable will hold 
path to the mounted directory.

Option syntax is `-f <path to file/directory>[:alias]`. Alias is optional and 
can be used to mount file/directory under different name. For example 
`-f /home/john/foo:bar.a` will mount `/home/john/foo` under `/mountpoints/bar.a` 
and add `BAR_A=/mountpoints/bar.a` to the execution environment.

## Obtaining information on ARTIQ version

`dartiq version` can be used to get information on the source commit of DARTIQ
image: included ARTIQ commit and revision of Nix Scripts repository used to 
build DARTIQ image.

## Configuration file

It is possible to pass script configuration as a JSON file. This may be useful 
for defining per-project configurations. By default `dartiq.json` file from the
current directory is used. Configuration file path can be overridden using 
`--config` argument. 

Example configuration file contents with all supported parameters:

```json
{
    "image": "technosystem/dartiq:latest",
    "workspace": "./",
    "xilinx_vivado_path": null,
    "xilinx_ise_path": null,
    "with_usb": true,
    "docker_options": [
        "--privileged"
    ],
    "python_modules": [
        "modules/artiq",
        "modules/misoc"
    ],
    "verbose": false,
    "copy_env_var": [
        "XILINXD_LICENSE_FILE"
    ],
    "add_env_var": [
        "FOO=BAR"
    ]
}
```

Command-line options override configuration file settings or expand them in case
of additional modules, Docker options and environment variables.

## Device access from within the container

By default the container starts with USB support and in *privileged* mode. However, 
because in the container you act as a normal user (of your current `uid`), 
appropriate `udev` rules are required. The fact that you can access devices 
without `sudo` on your host system may not be enough for them to be accessible 
for the user in the container as that user is not a member of additional groups 
that may be available on your host (e.g. `plugdev`).

To give unconstrained access to devices most commonly used with ARTIQ you can 
create file `/etc/udev/rules.d/99-dartiq.rules` (tested on Ubuntu 18.04 host) 
with the following contents:

```
# FT232H Single HS USB-UART FIFO IC, aka Digilent HS-3 JTAG
ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", MODE="666"

# FT4232H Quad HS USB-UART/FIFO IC, found on Kasli, Sayma, Metlino
ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6011", MODE="666"
```

## Examples of Use

```bash
# Display help message
dartiq --help

# Run experiment
dartiq run "artiq_run ./experiment.py"

# Display artiq_run help message
dartiq run "artiq_run --help"

# Running shell with ARTIQ from specified directory
dartiq shell -m ~/repos/artiq/artiq
```
