#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

if [[ -z "$TMUX" ]]; then
  tmux new-session -d -s load-test
fi

tmux split-window
tmux split-window

# shellcheck disable=SC2016
tmux send-keys -t load-test:0.1 'while true; do docker stats --no-stream --format "{{.Name}}: {{.MemUsage}}" directory-importer-directory-importer-1 | xargs -I {} echo "$(date '"'"'+%Y-%m-%d %H:%M:%S'"'"') {}" | tee -a container_memory.log; sleep 1; done' C-m

tmux send-keys -t load-test:0.2 'nload eth0' C-m

# Send command to the third pane WITHOUT executing it
tmux send-keys -t load-test:0.2 'cd ../ docker compose up --build'

# Select the third pane
tmux select-pane -t load-test:0.0

# Attach to the session
tmux attach-session -t load-test
