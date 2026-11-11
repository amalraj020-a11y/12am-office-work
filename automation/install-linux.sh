#!/usr/bin/env bash
set -euo pipefail
repo=/home/ubuntu/12pm-office-work
units=/home/ubuntu/.config/systemd/user
mkdir -p "$units"
install -m 0644 "$repo/automation/amala-cyber-guardian.service" "$units/amala-cyber-guardian.service"
install -m 0644 "$repo/automation/amala-cyber-guardian.timer" "$units/amala-cyber-guardian.timer"
chmod 0755 "$repo/automation/amala_cyber_guardian.py"
systemctl --user daemon-reload
systemctl --user enable --now amala-cyber-guardian.timer
sudo loginctl enable-linger ubuntu
systemctl --user status amala-cyber-guardian.timer --no-pager
