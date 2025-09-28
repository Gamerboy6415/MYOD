import os
import signal
import subprocess
import time
from datetime import datetime


def start_recording():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"~/recordings/alert_{timestamp}.mp4"
    
    # Build the FFmpeg command
    # alsa_output.pci-0000_00_1f.3.analog-stereo.monitor
    # alsa_output.pci-0000_01_00.1.hdmi-stereo.monitor
    command = [
        "ffmpeg", "-f", "x11grab", "-video_size", "1280x720", "-framerate", "15", "-i", ":0", 
        "-f", "pulse", "-i", "alsa_output.pci-0000_01_00.1.hdmi-stereo.monitor", 
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", 
        "-c:a", "aac", "-b:a", "128k", output_file
    ]
    
    # Start FFmpeg completely detached using nohup
    command_str = " ".join(f'"{c}"' if ' ' in c else c for c in command)
    
    # The key part: run with nohup and redirect all output to /dev/null
    full_command = f"nohup {command_str} > /dev/null 2>&1 & echo $!"
    
    # Execute the shell command and get the process ID
    process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    pid_output, _ = process.communicate()
    
    # Extract the process ID
    pid = int(pid_output.strip())
    
    print(f"Recording started: {output_file} (PID: {pid})")
    return pid

def stop_recording(pid):
    try:
        # First try a graceful termination with SIGTERM
        os.kill(pid, signal.SIGTERM)
        
        # Give FFmpeg a moment to terminate cleanly
        timeout = 3
        for _ in range(timeout * 10):
            try:
                # Check if process still exists
                os.kill(pid, 0)
                time.sleep(0.1)
            except OSError:
                # Process is gone
                print(f"Recording stopped (PID: {pid}).")
                return True
                
        # If it's still running after timeout, force kill
        os.kill(pid, signal.SIGKILL)
        print(f"Recording force stopped (PID: {pid}).")
        return True
    except OSError as e:
        if e.errno == 3:  # No such process
            print(f"Process {pid} already stopped.")
            return True
        else:
            print(f"Error stopping recording: {e}")
            return False
