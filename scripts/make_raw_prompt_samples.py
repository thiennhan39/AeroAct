import json
import shutil
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np


ROOT = Path("/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s")
ANN_PATH = Path("/workspace/AeroAct_ws/DATA/data/aerialvln-s/train.json")
INSTR_PATH = Path(
    "/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/data/aerialvln-s/train_episode2instruction.json"
)
OUT = Path("/workspace/AeroAct_ws/capture_quality_test_outputs/raw_data_prompt_samples")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ann = json.load(open(ANN_PATH))["episodes"]
    ep_meta = {e["episode_id"]: e for e in ann}
    instr = json.load(open(INSTR_PATH))

    by_scene = defaultdict(list)
    for d in ROOT.iterdir():
        if not d.is_dir():
            continue
        ep = d.name
        meta = ep_meta.get(ep)
        if not meta:
            continue
        rgb = d / "rgb"
        frames = sorted(rgb.glob("frame_*.jpg")) if rgb.exists() else []
        if not frames:
            continue
        scene_id = meta.get("scene_id")
        by_scene[scene_id].append(
            {
                "ep": ep,
                "dir": d,
                "frames": frames,
                "done": (d / "done").exists(),
                "mtime": max(p.stat().st_mtime for p in frames),
            }
        )

    scenes = []
    for scene_id in [17, 12, 5]:
        if scene_id in by_scene:
            scenes.append(scene_id)
    for scene_id, items in sorted(by_scene.items(), key=lambda kv: len(kv[1]), reverse=True):
        if scene_id not in scenes:
            scenes.append(scene_id)
        if len(scenes) >= 4:
            break

    selected = []
    for scene_id in scenes:
        items = by_scene[scene_id]
        if scene_id == 17:
            items_sorted = sorted(items, key=lambda x: (-x["mtime"], not x["done"], x["ep"]))
        else:
            items_sorted = sorted(items, key=lambda x: (not x["done"], -x["mtime"], x["ep"]))
        selected.extend((scene_id, item) for item in items_sorted[:2])

    manifest = []
    md = [
        "# Raw Data Prompt Samples",
        "",
        f"Raw root: `{ROOT}`",
        f"Annotation: `{ANN_PATH}`",
        "",
    ]

    for idx, (scene_id, item) in enumerate(selected, 1):
        ep = item["ep"]
        epout = OUT / f"scene{scene_id}_{ep}"
        epout.mkdir(parents=True, exist_ok=True)
        frames = item["frames"]
        ids = sorted(set([0, len(frames) // 4, len(frames) // 2, (3 * len(frames)) // 4, len(frames) - 1]))
        copied = []
        imgs = []

        for frame_idx in ids:
            src = frames[frame_idx]
            dst = epout / src.name
            shutil.copy2(src, dst)
            copied.append(str(dst))

            img = cv2.imread(str(src), cv2.IMREAD_COLOR)
            if img is None:
                continue
            canvas = img.copy()
            cv2.rectangle(canvas, (0, 0), (224, 22), (0, 0, 0), -1)
            cv2.putText(
                canvas,
                src.stem,
                (5, 16),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            imgs.append(canvas)

        sheet_path = None
        if imgs:
            height = max(im.shape[0] for im in imgs)
            width = max(im.shape[1] for im in imgs)
            normalized = [
                cv2.resize(im, (width, height), interpolation=cv2.INTER_AREA)
                if im.shape[:2] != (height, width)
                else im
                for im in imgs
            ]
            sheet = np.concatenate(normalized, axis=1)
            sheet_path = epout / "contact_sheet.jpg"
            cv2.imwrite(str(sheet_path), sheet)

        meta = ep_meta[ep]
        entry = {
            "scene_id": scene_id,
            "episode_id": ep,
            "done": item["done"],
            "num_frames": len(frames),
            "raw_dir": str(item["dir"]),
            "contact_sheet": str(sheet_path) if sheet_path else None,
            "sample_frames": copied,
            "instruction": instr.get(ep, meta.get("instruction", "")),
            "start_position": meta.get("start_position"),
            "goals": meta.get("goals"),
        }
        manifest.append(entry)

        md.extend(
            [
                f"## {idx}. scene {scene_id} - `{ep}`",
                f"- done: `{item['done']}`",
                f"- frames: `{len(frames)}`",
                f"- raw: `{item['dir']}`",
                f"- contact sheet: `{sheet_path}`",
                f"- instruction: {entry['instruction']}",
                "",
            ]
        )

    with open(OUT / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    with open(OUT / "README.md", "w") as f:
        f.write("\n".join(md))

    print("output_dir=", OUT)
    print("selected_count=", len(selected))
    for entry in manifest:
        instruction = entry["instruction"]
        preview = instruction[:280] + ("..." if len(instruction) > 280 else "")
        print()
        print(
            "SCENE",
            entry["scene_id"],
            "EP",
            entry["episode_id"],
            "done=",
            entry["done"],
            "frames=",
            entry["num_frames"],
        )
        print("sheet=", entry["contact_sheet"])
        print("instruction=", preview)


if __name__ == "__main__":
    main()
