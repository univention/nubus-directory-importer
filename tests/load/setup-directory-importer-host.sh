#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

apt install -y nload htop python3-pip
pip3 install ldap3

# Install docker
curl -fsSL https://get.docker.com -o get-docker.sh
bash get-docker.sh

# Check total memory in GB
total_mem=$(free -g | awk '/^Mem:/ {print $2}')

# Exit if total memory is less than 11GB
if [[ "$total_mem" -lt 11 ]]; then
    echo "Error: System does not have enough total memory. At least 12GB is required for a 100k user test."
    exit 1
fi
