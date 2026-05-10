"""
Upload large files to Hugging Face dataset repo.

Usage:
  1. Login once:  huggingface-cli login
  2. Run:         python3 scripts/upload_to_huggingface.py

What gets uploaded (all to tntnhan32/aeroact-data):
  - AirVLN/ENVs/          → ENVs/           (~38 GB, UE4 environments)
  - Dataset/AerialVLN-Dataset/Raw_data/  → Raw_data/  (collected frames)
  - Dataset/AerialVLN-Dataset/data/      → data/      (annotation JSONs)

Download on a new server:
  huggingface-cli download tntnhan32/aeroact-data --repo-type dataset --local-dir /workspace/AeroAct_ws/AeroAct
"""

import os
import sys
from huggingface_hub import HfApi, create_repo

REPO_ID = "tntnhan32/aeroact-data"
BASE = "/workspace/AeroAct_ws/AeroAct"

UPLOAD_DIRS = [
    ("AirVLN/ENVs",                                 "ENVs"),
    ("Dataset/AerialVLN-Dataset/Raw_data",          "Raw_data"),
    ("Dataset/AerialVLN-Dataset/data",              "data"),
]


def main():
    api = HfApi()

    # Create repo if it doesn't exist
    try:
        create_repo(REPO_ID, repo_type="dataset", exist_ok=True)
        print(f"Repo ready: https://huggingface.co/datasets/{REPO_ID}")
    except Exception as e:
        print(f"Warning creating repo: {e}")

    for local_rel, hf_path in UPLOAD_DIRS:
        local_abs = os.path.join(BASE, local_rel)
        if not os.path.exists(local_abs):
            print(f"Skipping (not found): {local_abs}")
            continue

        print(f"\nUploading {local_rel}/ → {hf_path}/ ...")
        api.upload_folder(
            folder_path=local_abs,
            path_in_repo=hf_path,
            repo_id=REPO_ID,
            repo_type="dataset",
        )
        print(f"  Done: {local_rel}")

    print("\nAll uploads complete.")
    print(f"View at: https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
