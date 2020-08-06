# Dockerfile to create an environment that contains the Nix package manager.
FROM alpine

ARG NIX_VERSION
ENV NIX_VERSION ${NIX_VERSION:-2.3.4}
ARG LANG
ENV LANG ${LANG:-"en_US.UTF-8"}

ARG ARTIQ_REV=master
ARG ARTIQ_REPO=https://github.com/m-labs/artiq.git
ARG NIX_SCRIPTS_REV=master
ARG NIX_SCRIPTS_REPO=https://git.m-labs.hk/M-Labs/nix-scripts.git

ARG BINARY_CACHE_PROXY="http://cache.nixos.org.rnd.ts http://nixbld.m-labs.hk.rnd.ts"

RUN addgroup -g 30000 -S nixbld \
    && for i in $(seq 1 30); do adduser -S -D -h /var/empty -g "Nix build user $i" -u $((30000 + i)) -G nixbld nixbld$i ; done \
    && adduser -D nixuser \
    && mkdir -m 0755 /nix && chown nixuser /nix \
    && apk add --no-cache bash xz git vim \
    && rm -rf /var/cache/apk/* \
    # sandboxing enabled by default since 2.2
    && mkdir -p /etc/nix && echo 'sandbox = false' > /etc/nix/nix.conf

# This one must be done before switching to nixuser
RUN mkdir /src && chown -R nixuser /src 

USER nixuser
ENV USER=nixuser
ENV HOME="/home/nixuser"

RUN cd && wget https://nixos.org/releases/nix/nix-$NIX_VERSION/nix-$NIX_VERSION-x86_64-linux.tar.xz \
    && tar xJf nix-*-x86_64-linux.tar.xz \
    && ~/nix-*-x86_64-linux/install \
    && rm -rf ~/nix-*-*

ENV ENV="/home/nixuser/.nix-profile/etc/profile.d/nix.sh"
RUN echo ". ${ENV}" >> ${HOME}/.profile
# All subsequent "RUN" will use a login shell
SHELL ["/usr/bin/env", "bash", "-l", "-c"]

RUN nix-channel --add https://nixos.org/channels/nixpkgs-20.03-darwin nixpkgs \
    && nix-channel --add https://nixbld.m-labs.hk/channel/custom/artiq/full/artiq-full \
    && nix-channel --update

# Propagate UTF8
# https://github.com/NixOS/nix/issues/599#issuecomment-153885553
# The same is hapenning with stack2nix
RUN nix-env -iA nixpkgs.glibcLocales

# Create bash profile
COPY --chown=nixuser:nixuser profile ${HOME}/.profile

RUN mkdir -p ~/.config/nix/ \
    && echo substituters = ${BINARY_CACHE_PROXY} https://cache.nixos.org https://nixbld.m-labs.hk >> ~/.config/nix/nix.conf \
    && echo trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= nixbld.m-labs.hk-1:5aSRVA5b320xbNvu30tqxVPXpld73bhtOeH6uAjRyHc= >> ~/.config/nix/nix.conf

RUN git clone ${ARTIQ_REPO} /src/artiq \
    && cd /src/artiq \
    && git checkout ${ARTIQ_REV} \
    && git submodule update --init

ADD nix-scripts.patch /src/nix-scripts.patch

RUN git clone ${NIX_SCRIPTS_REPO} /src/nix-scripts \
    && cd /src/nix-scripts \
    && git checkout ${NIX_SCRIPTS_REV} \
    && git submodule update --init \
    # Apply nix-scripts vivadoPath patch
    && git apply /src/nix-scripts.patch

RUN nix-shell -I artiqSrc=/src/artiq /src/nix-scripts/artiq-fast/shell-dev.nix --run exit

# Make sure to use "login" shell when running container
ENTRYPOINT ["/usr/bin/env", "bash", "-l", "-c"]
VOLUME ["/home/nixuser"]
VOLUME ["/workspace"]
