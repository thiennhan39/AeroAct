"""
Generate train_merged_triple.json from train.json + train_episodes2idx_merge.json.

Format of each entry:
  {"episode": "EPISODE_ID", "timestep": T, "action": "The next action is ...", "next_timestep": T2}

Where T and T2 are consecutive keyframe indices from idx_merge,
and "action" is the natural-language description of the action(s) taken between them.

Action units (from AirsimActionSettings):
  FORWARD_STEP_SIZE = 5, UP_DOWN_STEP_SIZE = 2, LEFT_RIGHT_STEP_SIZE = 5, TURN_ANGLE = 15
"""

import json
import os
import sys

TRAIN_JSON = "/workspace/AeroAct_ws/AeroAct/AirVLN/AirVLN-Dataset/data/aerialvln-s/train.json"
IDX_MERGE_JSON = "/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/data/aerialvln-s/train_episodes2idx_merge.json"
OUT_JSON = "/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/data/aerialvln-s/train_merged_triple.json"


def action_to_text(action_id: int, count: int) -> str:
    if action_id == 0:
        return "The next action is stop."
    elif action_id == 1:
        return f"The next action is move forward {count * 5} units."
    elif action_id == 2:
        return f"The next action is turn left {count * 15} degrees."
    elif action_id == 3:
        return f"The next action is turn right {count * 15} degrees."
    elif action_id == 4:
        return f"The next action is ascend {count * 2} units."
    elif action_id == 5:
        return f"The next action is descend {count * 2} units."
    elif action_id == 6:
        return f"The next action is move left {count * 5} units."
    elif action_id == 7:
        return f"The next action is move right {count * 5} units."
    else:
        return f"The next action is unknown (id={action_id}, count={count})."


def main():
    print("Loading train.json ...")
    with open(TRAIN_JSON) as f:
        train_data = json.load(f)
    # Build lookup: episode_id -> action list
    ep2actions = {ep["episode_id"]: ep["actions"] for ep in train_data["episodes"]}
    print(f"  Loaded {len(ep2actions)} episodes from train.json")

    print("Loading train_episodes2idx_merge.json ...")
    with open(IDX_MERGE_JSON) as f:
        idx_merge = json.load(f)
    print(f"  Loaded {len(idx_merge)} episodes from idx_merge")

    triples = []
    skipped = 0
    warn_count = 0

    common_eps = set(ep2actions.keys()) & set(idx_merge.keys())
    print(f"  Episodes in both files: {len(common_eps)}")

    for ep_id in sorted(common_eps):
        actions = ep2actions[ep_id]
        keyframes = idx_merge[ep_id]

        # Generate triples for consecutive keyframe pairs
        for i in range(len(keyframes) - 1):
            t_cur = keyframes[i]
            t_next = keyframes[i + 1]

            if t_next > len(actions):
                # idx_merge references beyond action list length — skip
                skipped += 1
                continue

            seg_actions = actions[t_cur:t_next]
            if not seg_actions:
                skipped += 1
                continue

            # All actions in segment should be the same (merge groups same actions)
            unique = set(seg_actions)
            if len(unique) > 1 and warn_count < 10:
                print(f"  WARNING: episode {ep_id} keyframes {t_cur}-{t_next} has mixed actions: {seg_actions}")
                warn_count += 1

            primary_action = seg_actions[0]
            count = len(seg_actions)
            text = action_to_text(primary_action, count)

            triples.append({
                "episode": ep_id,
                "timestep": t_cur,
                "action": text,
                "next_timestep": t_next,
            })

    print(f"\nGenerated {len(triples)} triple entries ({skipped} segments skipped)")
    print(f"Saving to {OUT_JSON} ...")
    with open(OUT_JSON, "w") as f:
        json.dump(triples, f, ensure_ascii=False, indent=None, separators=(",", ":"))
    print("Done.")

    # Verify against known sample
    sample = [
        {'episode': '3I33IC7ZWO0NVOKGK1L43MTEXSA2A5', 'timestep': 0, 'action': 'The next action is ascend 2 units.', 'next_timestep': 1},
        {'episode': '3I33IC7ZWO0NVOKGK1L43MTEXSA2A5', 'timestep': 1, 'action': 'The next action is turn right 45 degrees.', 'next_timestep': 4},
    ]
    # Check generated triples for this episode
    ep_triples = [t for t in triples if t["episode"] == "3I33IC7ZWO0NVOKGK1L43MTEXSA2A5"][:2]
    print("\nVerification (first 2 triples for 3I33IC7ZWO0NVOKGK1L43MTEXSA2A5):")
    for got, want in zip(ep_triples, sample):
        match = "OK" if got == want else "MISMATCH"
        print(f"  [{match}] got={got}")
        if got != want:
            print(f"         want={want}")


if __name__ == "__main__":
    main()
