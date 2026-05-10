#!/bin/bash
# Setup AeroAct on a fresh server from scratch.
# Run as: bash scripts/setup_new_server.sh
set -e

WORKSPACE="/workspace/AeroAct_ws"
REPO_GITHUB="https://github.com/return-sleep/AeroAct.git"
REPO_HF="tntnhan32/aeroact-data"

echo "=== Step 1: Clone code from GitHub ==="
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"
git clone "$REPO_GITHUB" AeroAct
cd AeroAct

echo "=== Step 2: Install Python dependencies ==="
pip install huggingface_hub -q

echo "=== Step 3: Login to Hugging Face (enter token when prompted) ==="
huggingface-cli login

echo "=== Step 4: Download large files from Hugging Face ==="
# ENVs (~38 GB) — skip with --exclude if already have them
huggingface-cli download "$REPO_HF" \
    --repo-type dataset \
    --local-dir "$WORKSPACE/AeroAct" \
    --local-dir-use-symlinks False

echo "=== Step 5: Regenerate train_merged_triple.json (from train.json + idx_merge) ==="
python3 scripts/generate_train_merged_triple.py

echo "=== Step 6: Verify ENVs and data ==="
echo "ENVs:"    && ls AirVLN/ENVs/ | head -5
echo "Raw_data:" && ls Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s/ | wc -l && echo "episodes collected"
echo "Triples:" && python3 -c "import json; d=json.load(open('Dataset/AerialVLN-Dataset/data/aerialvln-s/train_merged_triple.json')); print(len(d), 'entries')"

echo ""
echo "=== Setup complete! ==="
echo "To collect more data:"
echo "  cd AirVLN && bash collect.sh"
echo ""
echo "To start the AirsimServer:"
echo "  cd AirVLN && python3 -m airsim_plugin.AirVLNSimulatorServerTool"
