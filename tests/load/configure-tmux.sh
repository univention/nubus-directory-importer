#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

if [[ -z "$TMUX" ]]; then
  tmux new-session -d -s my_session
fi

tmux split-window
tmux split-window

tmux send-keys -t my_session:0.1 'while true; do docker stats --no-stream --format "{{.Name}}: {{.MemUsage}}" directory-importer-udm-directory-connector-1 | xargs -I {} echo "$(date '"'"'+%Y-%m-%d %H:%M:%S'"'"') {}" | tee -a container_memory.log; sleep 1; done' C-m

tmux send-keys -t my_session:0.2 'nload eth0' C-m

# Send command to the third pane WITHOUT executing it
tmux send-keys -t my_session:0.2 'docker compose up --build'

# Select the third pane
tmux select-pane -t my_session:0.2

# Attach to the session (directly in the third pane)
tmux attach-session -t my_session
