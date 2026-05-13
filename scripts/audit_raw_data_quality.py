import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np


# [MODIFIED] Audit raw RGB collection quality and persist bad episode list for
# collect/train filtering. This script does not change collected images.
ANNOTATION_PATH = Path("/workspace/AeroAct_ws/DATA/data/aerialvln-s/train.json")
RAW_ROOT = Path("/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s")
OUT_DIR = Path("/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s")


def image_stats(path):
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        return None
    return {
        "mean": float(np.mean(img)),
        "std": float(np.std(img)),
        "min": int(np.min(img)),
        "max": int(np.max(img)),
    }


def first_mid_last(frames):
    if not frames:
        return []
    idxs = sorted(set([0, len(frames) // 2, len(frames) - 1]))
    return [frames[i] for i in idxs]


def main():
    episodes = json.load(open(ANNOTATION_PATH))["episodes"]
    total = len(episodes)

    bad_episodes = []
    partial_episodes = []
    done_episodes = []
    frame_counts = []
    quality_flags = []

    for item in episodes:
        episode_id = item["episode_id"]
        scene_id = item.get("scene_id")
        episode_dir = RAW_ROOT / episode_id
        rgb_dir = episode_dir / "rgb"
        done = (episode_dir / "done").exists()
        frames = sorted(rgb_dir.glob("frame_*.jpg")) if rgb_dir.exists() else []
        num_frames = len(frames)

        record = {
            "episode_id": episode_id,
            "scene_id": scene_id,
            "num_frames": num_frames,
            "folder_exists": episode_dir.exists(),
            "done": done,
        }

        if not done:
            bad_episodes.append(record)
            if episode_dir.exists() or num_frames > 0:
                partial_episodes.append(record)
            continue

        done_episodes.append(record)
        frame_counts.append(num_frames)

        flags = []
        if num_frames == 0:
            flags.append("done_but_no_frames")
        elif num_frames < 5:
            flags.append("very_short_lt5")
        elif num_frames < 10:
            flags.append("short_lt10")

        stats = []
        for frame in first_mid_last(frames):
            s = image_stats(frame)
            if s is not None:
                stats.append({"frame": frame.name, **s})

        if stats:
            means = [s["mean"] for s in stats]
            stds = [s["std"] for s in stats]
            if max(means) < 8:
                flags.append("very_dark_sample")
            if min(means) > 247:
                flags.append("very_bright_sample")
            if max(stds) < 2:
                flags.append("low_variance_sample")

        if len(frames) >= 2:
            first = cv2.imread(str(frames[0]), cv2.IMREAD_COLOR)
            last = cv2.imread(str(frames[-1]), cv2.IMREAD_COLOR)
            if first is not None and last is not None and first.shape == last.shape:
                diff = float(np.mean(np.abs(first.astype(np.float32) - last.astype(np.float32))))
                if diff < 1.0 and num_frames >= 10:
                    flags.append("first_last_nearly_identical")

        if flags:
            quality_flags.append({**record, "flags": flags, "sample_stats": stats})

    bad_path = OUT_DIR / "bad_episodes.json"
    audit_path = OUT_DIR / "raw_data_quality_audit.json"
    report_path = OUT_DIR / "raw_data_quality_audit.md"
    excluded_path = OUT_DIR / "excluded_for_training.json"

    with open(bad_path, "w") as f:
        json.dump(
            {
                "source_annotation": str(ANNOTATION_PATH),
                "reason": "Episodes not successfully collected after retry; do not use for raw-image training.",
                "count": len(bad_episodes),
                "episodes": bad_episodes,
            },
            f,
            indent=2,
        )

    summary = {
        "total_annotation_episodes": total,
        "done_count": len(done_episodes),
        "bad_count": len(bad_episodes),
        "partial_bad_count": len(partial_episodes),
        "done_by_scene": dict(sorted(Counter(e["scene_id"] for e in done_episodes).items())),
        "bad_by_scene": dict(sorted(Counter(e["scene_id"] for e in bad_episodes).items())),
        "frame_count_min": min(frame_counts) if frame_counts else 0,
        "frame_count_max": max(frame_counts) if frame_counts else 0,
        "frame_count_mean": float(np.mean(frame_counts)) if frame_counts else 0.0,
        "done_lt5_count": sum(1 for n in frame_counts if n < 5),
        "done_lt10_count": sum(1 for n in frame_counts if n < 10),
        "done_lt20_count": sum(1 for n in frame_counts if n < 20),
        "quality_flag_count": len(quality_flags),
    }

    with open(audit_path, "w") as f:
        json.dump(
            {
                "summary": summary,
                "bad_episodes": bad_episodes,
                "partial_bad_episodes": partial_episodes,
                "quality_flags": quality_flags,
            },
            f,
            indent=2,
        )

    # [MODIFIED] Build a conservative training exclusion list:
    # - episodes that never collected successfully
    # - done episodes with too few frames for meaningful visual learning
    # - done episodes whose sampled frames are extremely dark
    excluded = {}
    for item in bad_episodes:
        excluded[item["episode_id"]] = {
            **item,
            "reasons": ["bad_not_collected"],
        }
    for item in quality_flags:
        reasons = []
        if item["num_frames"] < 10:
            reasons.append("too_few_frames_lt10")
        if "very_dark_sample" in item["flags"]:
            reasons.append("very_dark_sample")
        if not reasons:
            continue
        if item["episode_id"] in excluded:
            excluded[item["episode_id"]]["reasons"].extend(reasons)
        else:
            excluded[item["episode_id"]] = {
                "episode_id": item["episode_id"],
                "scene_id": item["scene_id"],
                "num_frames": item["num_frames"],
                "folder_exists": item["folder_exists"],
                "done": item["done"],
                "reasons": reasons,
            }

    excluded_items = sorted(excluded.values(), key=lambda e: (e["scene_id"], e["episode_id"]))
    with open(excluded_path, "w") as f:
        json.dump(
            {
                "source_annotation": str(ANNOTATION_PATH),
                "source_audit": str(audit_path),
                "policy": {
                    "exclude_bad_not_collected": True,
                    "exclude_done_num_frames_lt": 10,
                    "exclude_very_dark_sample": True,
                },
                "count": len(excluded_items),
                "episodes": excluded_items,
            },
            f,
            indent=2,
        )

    flag_counts = Counter(flag for item in quality_flags for flag in item["flags"])
    shortest_done = sorted(done_episodes, key=lambda e: e["num_frames"])[:30]

    lines = [
        "# Raw Data Quality Audit",
        "",
        f"- total annotation episodes: `{total}`",
        f"- done episodes: `{len(done_episodes)}`",
        f"- bad/skipped episodes: `{len(bad_episodes)}`",
        f"- partial bad episodes: `{len(partial_episodes)}`",
        f"- frame count min/max/mean: `{summary['frame_count_min']}` / `{summary['frame_count_max']}` / `{summary['frame_count_mean']:.2f}`",
        f"- done episodes <5 frames: `{summary['done_lt5_count']}`",
        f"- done episodes <10 frames: `{summary['done_lt10_count']}`",
        f"- done episodes <20 frames: `{summary['done_lt20_count']}`",
        f"- quality flagged episodes: `{len(quality_flags)}`",
        "",
        "## Bad Episodes By Scene",
        "",
        "```json",
        json.dumps(summary["bad_by_scene"], indent=2),
        "```",
        "",
        "## Quality Flag Counts",
        "",
        "```json",
        json.dumps(dict(sorted(flag_counts.items())), indent=2),
        "```",
        "",
        "## Shortest Done Episodes",
        "",
    ]
    for item in shortest_done:
        lines.append(
            f"- scene `{item['scene_id']}` episode `{item['episode_id']}` frames `{item['num_frames']}`"
        )

    lines.extend(
        [
            "",
            "## Files",
            "",
            f"- bad list: `{bad_path}`",
            f"- training exclusion list: `{excluded_path}`",
            f"- full audit JSON: `{audit_path}`",
        ]
    )

    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    print("bad_path=", bad_path)
    print("excluded_path=", excluded_path)
    print("audit_path=", audit_path)
    print("report_path=", report_path)
    print(json.dumps(summary, indent=2))
    print("flag_counts=", json.dumps(dict(sorted(flag_counts.items())), indent=2))


if __name__ == "__main__":
    main()
