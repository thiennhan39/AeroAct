"""
Upload Raw_data frames to HuggingFace incrementally.
Chạy một lần: python3 scripts/upload_rawdata_hf.py
Chạy mỗi giờ: watch -n 3600 python3 scripts/upload_rawdata_hf.py
"""
import os
from huggingface_hub import HfApi

TOKEN = os.environ.get("HF_TOKEN", "")
REPO_ID = "Nhan32/aeroact-data"
BASE = "/workspace/AeroAct_ws/AeroAct"

api = HfApi(token=TOKEN)

collected = len(os.listdir(f"{BASE}/Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s"))
print(f"Episodes collected: {collected} / 10113")
print("Uploading Raw_data to HuggingFace (skips already-uploaded files)...")

api.upload_folder(
    folder_path=f"{BASE}/Dataset/AerialVLN-Dataset/Raw_data",
    path_in_repo="Raw_data",
    repo_id=REPO_ID,
    repo_type="dataset",
)

print("Done! View at: https://huggingface.co/datasets/Nhan32/aeroact-data")
