'''
This script extracts pose data and converts it to a CSV file
'''

import sqlite3
import os
import csv

from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from geometry_msgs.msg import PoseStamped

# === Configuration ===
bag_path = 'both_topics'
topic_name = '/pf/viz/inferred_pose'

# === Setup ===
db_path = os.path.join(bag_path, f'{bag_path}_0.db3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# === Get topic ID ===
cursor.execute("SELECT id FROM topics WHERE name = ?", (topic_name,))
topic_id_row = cursor.fetchone()

if not topic_id_row:
    print(f"[❌] Topic '{topic_name}' not found in bag!")
    exit(1)

topic_id = topic_id_row[0]
cursor.execute("SELECT timestamp, data FROM messages WHERE topic_id = ?", (topic_id,))
rows = cursor.fetchall()

print(f"[ℹ️] Extracting {len(rows)} PoseStamped messages...")

# === Write CSV ===
with open('pose_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # we only care about 3 labels: pos_x, pos_y, and w
    writer.writerow([
        'timestamp_sec',
        'pos_x', 'pos_y',
        'ori_w'
    ])

    for timestamp, data in rows:
        msg_type = get_message('geometry_msgs/msg/PoseStamped')
        pose_msg = deserialize_message(data, msg_type)

        t = pose_msg.header.stamp.sec + pose_msg.header.stamp.nanosec * 1e-9
        pos = pose_msg.pose.position
        ori = pose_msg.pose.orientation

        writer.writerow([
            f"{t:.9f}",
            pos.x, pos.y, ori.w
        ])

print("[✅] Saved poses to 'pose_data.csv'")
conn.close()
