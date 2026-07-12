'''
This script extracts raw camera images from a ROS2 bag file and 
convert them to PNG format.

You can run it as-is on the car.
'''

import sqlite3
import os
import numpy as np
import cv2

from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from sensor_msgs.msg import Image

# === Configuration ===
bag_path = './both_topics'  			# path of bag file to access
topic_name = '/camera/color/image_raw' 	# name of topic from RealSense camera

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

os.makedirs('extracted_images', exist_ok=True)
print(f"[ℹ️ ] Extracting {len(rows)} images from topic '{topic_name}'...")

# === Helper to convert ROS image encoding to OpenCV dtype ===
def decode_ros_image(img_msg):
    dtype = None
    channels = 1

    if img_msg.encoding == 'mono8':
        dtype = np.uint8
        channels = 1
    elif img_msg.encoding == 'bgr8' or img_msg.encoding == 'rgb8':
        dtype = np.uint8
        channels = 3
    else:
        raise NotImplementedError(f"Unsupported encoding: {img_msg.encoding}")

    img_data = np.frombuffer(img_msg.data, dtype=dtype)
    image = img_data.reshape((img_msg.height, img_msg.width, channels)) if channels > 1 else img_data.reshape((img_msg.height, img_msg.width))

    if img_msg.encoding == 'rgb8':
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    return image

# === Process and save images ===
for i, (timestamp, data) in enumerate(rows):
    try:
        msg_type = get_message('sensor_msgs/msg/Image')
        img_msg = deserialize_message(data, msg_type)
        cv_image = decode_ros_image(img_msg)

        filename = f"extracted_images/frame_{i:04d}_{timestamp}.png"
        cv2.imwrite(filename, cv_image)
        print(f"[✅] Saved: {filename}")
    except Exception as e:
        print(f"[⚠️] Failed to decode frame {i}: {e}")

conn.close()
print("[🎉] Done!")

