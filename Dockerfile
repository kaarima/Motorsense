# MotorSense dev image: one environment for local work and CI.
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
# Check https://github.com/renode/renode/releases for the latest version.
ARG RENODE_VERSION=1.15.3

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake ninja-build git curl ca-certificates \
        gcc-arm-none-eabi libnewlib-arm-none-eabi gdb-multiarch openocd \
        cppcheck clang-format clang-tidy \
        python3 python3-dev python3-venv python3-pip \
        mono-complete \
    && rm -rf /var/lib/apt/lists/*

# Renode (virtual board / digital twin)
RUN curl -fsSL -o /tmp/renode.tar.gz \
        https://github.com/renode/renode/releases/download/v${RENODE_VERSION}/renode-${RENODE_VERSION}.linux-portable.tar.gz \
    && mkdir -p /opt/renode \
    && tar -xzf /tmp/renode.tar.gz -C /opt/renode --strip-components=1 \
    && rm /tmp/renode.tar.gz
ENV PATH="/opt/renode:${PATH}"

# Python environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:${PATH}"
RUN pip install --no-cache-dir -r /opt/renode/tests/requirements.txt
COPY ml/requirements.txt ml/requirements-dev.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt -r /tmp/requirements-dev.txt

WORKDIR /workspace
