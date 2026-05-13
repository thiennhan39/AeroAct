#!/bin/bash
# collect.sh — Sinh raw RGB frames từ AirVLN simulator cho AeroAct training.
#
# Tác dụng:
#   1. Khởi động AirVLN Simulator Server (background, headless qua Xvfb)
#   2. Chạy collect mode trong train.py (đã được sửa) để bay drone theo
#      ground-truth trajectory, chụp ảnh tại mỗi bước và lưu thành JPEG.
#
# Output:
#   Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s/{episode_id}/rgb/frame_XXX.jpg
#
# Yêu cầu:
#   - Đã cài Xvfb (apt-get install -y xvfb)
#   - Conda env "aeroact" đã được setup
#   - Chạy script này từ thư mục AirVLN/  (cd AirVLN && bash collect.sh)

set -e  # dừng ngay nếu có lỗi

# ── Cấu hình ──────────────────────────────────────────────────────────────────
CONDA_ENV="aeroact"
# GPU IDs sẽ dùng (server có 3x RTX 3060: gpu 0, 1, 2)
GPUS="0,1,2"
# Tên experiment — dùng để đặt tên thư mục log/output
EXP_NAME="AeroAct-collect"
# Số episode xử lý song song (batch_size).
# Mỗi env cần ~1 GB VRAM; 3 GPU × 12 GB = 36 GB tổng → an toàn với batch 8-12.
BATCH_SIZE=8
# ─────────────────────────────────────────────────────────────────────────────

echo "[collect.sh] Kiểm tra vị trí thư mục..."
# Script phải được chạy từ trong AirVLN/
if [ ! -f "airsim_plugin/AirVLNSimulatorServerTool.py" ]; then
    echo "LỖI: Chạy script này từ thư mục AirVLN/  (cd AirVLN && bash collect.sh)"
    exit 1
fi

# ── 1. Khởi động virtual display (Xvfb) ─────────────────────────────────────
# Unreal Engine cần màn hình để render kể cả khi chạy headless trên server.
echo "[collect.sh] Khởi động Xvfb virtual display trên :1 ..."
# Dừng display cũ nếu còn chạy (tránh conflict)
pkill Xvfb 2>/dev/null || true
sleep 1
Xvfb :1 -screen 0 1280x720x24 &
XVFB_PID=$!
export DISPLAY=:1
echo "[collect.sh] Xvfb PID=$XVFB_PID, DISPLAY=$DISPLAY"
sleep 2

# ── 2. Khởi động AirVLN Simulator Server ─────────────────────────────────────
# Server tool mở các Unreal Engine environment và lắng nghe lệnh từ client.
# Chạy nền (nohup) và redirect log ra file để tiện theo dõi.
echo "[collect.sh] Khởi động AirVLN Simulator Server (background)..."
# [QUAN TRỌNG] Server tool tính đường dẫn ENVs/ bằng:
#   PROJECT_ROOT_DIR = os.getcwd().parent
# → phải chạy từ airsim_plugin/ để parent = AirVLN/ (chứa ENVs/)
# Không chạy từ AirVLN/ vì sẽ tìm ENVs/ ở AeroAct/ → AssertionError
(cd ./airsim_plugin && nohup \
    /workspace/AeroAct_ws/miniconda3/envs/aeroact/bin/python -u \
    AirVLNSimulatorServerTool.py --gpus "$GPUS" \
    > /tmp/airvln_server.log 2>&1) &
SERVER_PID=$!
echo "[collect.sh] Simulator server PID=$SERVER_PID"
echo "[collect.sh] Log server: /tmp/airvln_server.log"

# Đợi server khởi động xong trước khi gọi client
echo "[collect.sh] Đợi 30 giây cho simulator server sẵn sàng..."
sleep 30

# ── 3. Chạy collect mode ──────────────────────────────────────────────────────
# train.py đã được sửa để lưu raw JPEG frames ra:
#   Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s/{episode_id}/rgb/frame_XXX.jpg
# thay vì chỉ lưu DNN feature vectors vào LMDB như code gốc AirVLN.
echo "[collect.sh] Bắt đầu collect data..."
conda run --no-capture-output -n "$CONDA_ENV" python -u ./src/vlnce_src/train.py \
    --run_type collect \
    --policy_type seq2seq \
    --collect_type TF \
    --name "$EXP_NAME" \
    --batchSize "$BATCH_SIZE"

echo "[collect.sh] Collect hoàn tất."

# ── Dọn dẹp ──────────────────────────────────────────────────────────────────
echo "[collect.sh] Tắt simulator server và Xvfb..."
kill "$SERVER_PID" 2>/dev/null || true
kill "$XVFB_PID"  2>/dev/null || true
echo "[collect.sh] Done."
