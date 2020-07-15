Dockerized ARTIQ
===

This repository provides tools to operate with ARTIQ in dockerized environment. It makes work with ARTIQ
more predictable and independent from external binary repositories.

What you get with the image is full ARTIQ installation that can be instantiated and used as a Docker container. Provided `dartiq` script acts as an interface between you and Docker and makes use of dockerized ARTIQ user-friendly. For example, to get a shell with ARTIQ installed just type `dartiq shell`. This will drop you in the shell with your current working directory mounted as `/workspace` directory in the container. It also makes container run in *privileged* mode (you were warned!) so that hardware access should not be the problem (there is also `/dev/bus/usb` mounted).

You can also run single command in Docker container by adding `run` option, e.g. `dartiq run artiq_run ./experiment.py`. Please note that if your command contains double-dash parameters it must be taken into quotes like that: `dartiq run "artiq_run --help"`.

**CAUTION:** In the container you'll act as `nixuser` of uid=1000 and gid=1000, so if your uid and gid happens to be the same (true in most single-user environment cases) you don't have to worry about permissions. If your uid and gid is different you're welcome to submit PR with appropriate patch ;-).

## Xilinx Vivado Support

If you source Xilinx Vivado `settings64.sh` prior to running `dartiq` a path under which Vivado is installed will be mounted in the container and your Vivado installation will be ready to use. 

You can pass a path to licencing information using either `--copy-env-var XILINXD_LICENSE_FILE` option which copies given variable to container environment or by adding new variable with `--add-env-var XILINXD_LICENSE_FILE=<...>`. 

## External Python Modules

It may happen that you want to add some Python module to be used inside the container. Notably, a slightly different version of ARTIQ, MiSoC or Migen may be of your interest. You can use it with `--add-module <MODULE PATH>` option. This will mount your module in `/modules` directory and add appropriate entry in the `PYTHONPATH`.

## Extracting ARTIQ

You may want to refer to the sources embedded within the image. They can be extracted using `extract_artiq` command. Refer to the command help for more options.

## Configuration file

It is possible to pass script configuration as a JSON file. This may be useful for defining per-project configurations. Configuration file path can be given by `--config` argument. Example configuration file contents with all respected parameters:

```json
{
    "image": "technosystem/dartiq:latest",
    "worksapce": "./",
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

Command-line options override configuration file settings or expand them in case of additional modules, Docker options and environment variables. 

## Image Building

Image tag should follow the following pattern: `technosystem/dartiq:<year>.<month>.<day>_<hour><minute><second>`. However, `dartiq` script refers to `technosystem/dartiq:latest`.
To generate image locally use: `build_image` script.

## Examples of Use

```bash
# Display help message
dartiq --help

# Running experiment
dartiq run artiq_run ./experiment.py

# Display artiq_run help message - note use of quotes to prevent displaying dartiq help message
dartiq run "artiq_run --help"

# Running shell with ARTIQ from specified directory
dartiq shell -m ~/repos/artiq/artiq
```
