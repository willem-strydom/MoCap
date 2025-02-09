import csv
import time
from datetime import datetime
from pathlib import Path
import time
from NatNetClient import NatNetClient

class LiveMocapDataLogger:
    def __init__(self, output_directory='mocap_recordings'):
        # Create output directory if it doesn't exist
        self.output_dir = Path(output_directory)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create unique filename using timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.frame_file = self.output_dir / f'mocap_frames_{timestamp}.csv'
        self.rigid_body_file = self.output_dir / f'mocap_rigidbodies_{timestamp}.csv'
        
        # Initialize CSV files with headers
        with open(self.frame_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'frame_number', 'marker_count', 'rigid_body_count'])
            
        with open(self.rigid_body_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'body_id', 'pos_x', 'pos_y', 'pos_z', 
                           'rot_x', 'rot_y', 'rot_z'])
        
        self.start_time = time.time()

    def receive_new_frame(self, data_dict):
        """Called every time a new frame of mocap data arrives"""
        current_time = time.time() - self.start_time
        
        # Extract relevant data
        frame_data = [
            current_time,
            data_dict.get('frameNumber', ''),
            data_dict.get('markerSetCount', ''),
            data_dict.get('rigidBodyCount', '')
        ]
        
        # Append to CSV file
        with open(self.frame_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(frame_data)

    def receive_rigid_body_frame(self, body_id, position, rotation):
        """Called for each rigid body in every frame"""
        current_time = time.time() - self.start_time
        
        # Combine data into a single row
        body_data = [
            current_time,
            body_id,
            position[0], position[1], position[2],  # x, y, z position
            rotation[0], rotation[1], rotation[2]   # x, y, z rotation
        ]
        
        # Append to CSV file
        with open(self.rigid_body_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(body_data)

# Set up the data logger and streaming client
def main():
    # Create our data logger
    data_logger = LiveMocapDataLogger()
    
    # Create and configure the streaming client
    streaming_client = NatNetClient()
    streaming_client.set_client_address("192.168.1.103")  # Your computer's IP
    streaming_client.set_server_address("10.229.139.24")  # OptiTrack server IP
    streaming_client.set_use_multicast(True)
    
    # Connect our data logging callbacks
    streaming_client.new_frame_listener = data_logger.receive_new_frame
    streaming_client.rigid_body_listener = data_logger.receive_rigid_body_frame
    
    # Start the client
    is_running = streaming_client.run()
    if not is_running:
        print("ERROR: Could not start streaming client.")
        return
    
    print("Successfully connected to OptiTrack system!")
    print(f"Recording data to: {data_logger.output_dir}")
    print("Press Ctrl+C to stop recording...")
    
    try:
        while True:
            time.sleep(0.1)  # Small sleep to prevent CPU overuse
    except KeyboardInterrupt:
        print("\nStopping recording...")
        streaming_client.shutdown()
        print("Recording finished!")

if __name__ == "__main__":
    main()