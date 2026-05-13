# AeroAct Server Runbook

This file records the commands used to set up and run the AirVLN simulator/data
collection workflow on a fresh server.

## What Is A Symlink?

A symlink is a filesystem shortcut. For example:

```bash
ln -sfn /real/path/to/data /path/code/expects
```

After this, code that opens `/path/code/expects` is actually reading
`/real/path/to/data`. AeroAct uses this because some scripts expect dataset and
utility paths inside `AirVLN/`, while the real folders may live elsewhere.

## 1. Clone The Project

```bash
mkdir -p /workspace/AeroAct_ws
cd /workspace/AeroAct_ws
git clone https://github.com/thiennhan39/AeroAct.git
cd AeroAct
```

## 2. Create The Conda Environment

Install Miniconda first if the server does not already have it. Then:

```bash
conda create -n aeroact python=3.10 -y
conda activate aeroact
pip install --upgrade pip
bash environment_setup.sh
```

If later commands complain about missing packages, install them inside the same
`aeroact` environment.

## 3. Download Large Data Separately

GitHub does not store the large simulator environments or raw RGB frames.
Download them from the Hugging Face dataset storage:

```bash
conda activate aeroact
pip install huggingface_hub
huggingface-cli login
huggingface-cli download tntnhan32/aeroact-data \
  --repo-type dataset \
  --local-dir /workspace/AeroAct_ws/AeroAct \
  --local-dir-use-symlinks False
```

Expected large paths after download:

```text
/workspace/AeroAct_ws/AeroAct/AirVLN/ENVs
/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/Raw_data
/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/data
```

## 4. Create Required Symlinks

```bash
cd /workspace/AeroAct_ws/AeroAct
ln -sfn /workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset AirVLN/AirVLN-Dataset
ln -sfn /workspace/AeroAct_ws/AeroAct/AirVLN/src AirVLN/AirVLN_src
ln -sfn /workspace/AeroAct_ws/AeroAct/AirVLN/utils AirVLN/AirVLN_utils
```

If you keep a separate shared data folder at `/workspace/AeroAct_ws/DATA`, add:

```bash
ln -sfn /workspace/AeroAct_ws/DATA /workspace/AeroAct_ws/AeroAct/DATA
```

## 5. Prepare Display And Permissions

Unreal needs a display, even in offscreen mode. Use Xvfb:

```bash
tmux new -d -s aeroact_xvfb 'Xvfb :1 -screen 0 1024x768x24 -ac'
```

Make sure the simulator environment files can run as user `airvln`:

```bash
sudo chown -R airvln:airvln /workspace/AeroAct_ws/AeroAct/AirVLN/ENVs
```

If the server has no `airvln` user, create it or adjust the simulator scripts to
use the available runtime user.

## 6. Start The Simulator Server

Use one tmux session for the simulator server:

```bash
tmux new -s aeroact_server
export DISPLAY=:1
cd /workspace/AeroAct_ws/AeroAct/AirVLN/airsim_plugin
source /workspace/AeroAct_ws/miniconda3/etc/profile.d/conda.sh
conda activate aeroact
python -u AirVLNSimulatorServerTool.py --gpus 0,1,2
```

Detach from tmux without stopping it:

```text
Ctrl+B, then D
```

## 7. Run Data Collection

Use a second tmux session for collection:

```bash
tmux new -s aeroact_collect
export DISPLAY=:1
cd /workspace/AeroAct_ws/AeroAct/AirVLN
source /workspace/AeroAct_ws/miniconda3/etc/profile.d/conda.sh
conda activate aeroact
python -u src/vlnce_src/train.py \
  --run_type collect \
  --policy_type seq2seq \
  --collect_type TF \
  --name collect_full \
  --batchSize 6 \
  --EVAL_NUM -1
```

For the final few leftover episodes, use a smaller batch to avoid mixed-scene
reopen overhead:

```bash
python -u src/vlnce_src/train.py \
  --run_type collect \
  --policy_type seq2seq \
  --collect_type TF \
  --name collect_full \
  --batchSize 1 \
  --EVAL_NUM -1
```

## 8. Useful Monitoring Commands

```bash
tmux attach -t aeroact_server
tmux attach -t aeroact_collect
nvidia-smi
ps -ef | grep -E 'AirVLN-Linux-Shipping|AirVLNSimulatorServerTool|src/vlnce_src/train.py'
```

Count collected episodes:

```bash
find /workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s \
  -maxdepth 2 -name done | wc -l
```

## 9. Training Exclusion List

Some episodes are known bad or too short for raw-image training. Use this file to
filter them out during training:

```text
Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s/excluded_for_training.json
```

The audit report is here:

```text
Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s/raw_data_quality_audit.md
```

Regenerate the audit after collecting new data:

```bash
conda activate aeroact
python scripts/audit_raw_data_quality.py
```

Create prompt/contact-sheet samples for manual raw-image review:

```bash
conda activate aeroact
python scripts/make_raw_prompt_samples.py
```

## 10. Common Notes

- `Failed to open scenes` appears in the client log even when opening succeeds;
  check for `Connected!`, `END reopen_scenes`, and active
  `AirVLN-Linux-Shipping` processes.
- `pid is not int` is a noisy port/PID check message and is usually not fatal.
- Do not commit `AirVLN/ENVs/` or full `Raw_data/` to GitHub; keep them in
  Hugging Face or separate storage.
