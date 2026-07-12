import sqlit010e3
import os
import csv
import rclpy
from rclpy.serialization import deserialize_message
from ackermann_msgs.msg import AckermannDriveStamped
from rosidl_runtime_py.utilities import get_message

# === CONFIG ===
bag_path = "/path/to/your/bagfile"
topic_name = "/ackermann_mux/output"
output_csv = "ackermann_output.csv"

def get_topic_id_and_type(conn, topic_name):
    cursor = conn.cursor()
    cursor.execute("SELECT id, type FROM topics WHERE name=?", (topic_name,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"Topic {topic_name} not found in database.")
    return result[0], result[1]

def main():
    db_path = os.path.join(bag_path, "data.db3")
    if not os.path.exists(db_path):
        print(f"Could not find database at: {db_path}")
        return

    # Start rclpy so we can deserialize properly
    rclpy.init()

    conn = sqlite3.connect(db_path)
    topic_id, topic_type = get_topic_id_and_type(conn, topic_name)

    msg_type = get_message(topic_type)  # e.g., ackermann_msgs/msg/AckermannDriveStamped

    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, data FROM messages WHERE topic_id=?", (topic_id,))

    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'steering_angle', 'speed'])

        for timestamp, data in cursor.fetchall():
            msg = deserialize_message(data, msg_type)
            try:
                steer = msg.drive.steering_angle
                speed = msg.drive.speed
                writer.writerow([timestamp, steer, speed])
            except AttributeError:
                print("Malformed message — skipping.")

    print(f"✅ Extracted data written to: {output_csv}")
    rclpy.shutdown()

if __name__ == "__main__":
    main()
