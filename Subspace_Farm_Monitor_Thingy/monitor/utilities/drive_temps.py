import platform
import psutil
import subprocess
import re

def get_drive_temps_linux():
    """Fetch temperatures for NVMe and SSD drives on Linux."""
    drives = []
    nvme_pattern = re.compile(r"nvme\d+n\d+")
    ssd_pattern = re.compile(r"sd[a-z]+")
    
    for partition in psutil.disk_partitions():
        device = partition.device.split('/')[-1]
        mount_point = partition.mountpoint
        temp = "----"
        drive_type = "Unknown"

        try:
            if nvme_pattern.match(device):  # NVMe drives
                drive_type = "NVMe"
                temp_output = subprocess.check_output(
                    f"sudo nvme smart-log /dev/{device} | grep 'temperature' | awk '{{print $3}}'",
                    shell=True, text=True
                ).strip()
                temp = f"{temp_output}°C" if temp_output else " N/A"
            elif ssd_pattern.match(device):  # SATA SSD drives
                drive_type = "SSD"
                temp_output = subprocess.check_output(
                    f"sudo smartctl -A /dev/{device} | grep -i 'Temperature_Celsius' | awk '{{print $10}}'",
                    shell=True, text=True
                ).strip()
                temp = f"{temp_output}°C" if temp_output else " N/A"
        except subprocess.CalledProcessError:
            temp = " N/A"

        drives.append({"Device": f"/dev/{device}", "Mount Point": mount_point, "Temperature": temp, "Type": drive_type})
    
    return drives

def get_drive_temps_windows():
    """Fetch temperatures for NVMe and SSD drives on Windows."""
    drives = []
    try:
        import wmi
        c = wmi.WMI(namespace=r"root\Microsoft\Windows\Storage")
        
        # Query all physical disks
        for disk in c.MSFT_PhysicalDisk():
            media_type = getattr(disk, "MediaType", "Unknown")
            if media_type in ["SSD", "NVMe"]:  # Check if the drive is SSD or NVMe
                mount_points = []
                for partition in psutil.disk_partitions():
                    if partition.device in str(disk.DeviceID):
                        mount_points.append(partition.mountpoint)
                
                # Get temperature (if available)
                temperature = getattr(disk, "Temperature", " N/A")
                drives.append({
                    "Device": disk.DeviceID,
                    "Mount Point": ", ".join(mount_points) if mount_points else "Unmounted",
                    "Temperature": f"{temperature}°C" if temperature != " N/A" else " N/A",
                    "Type": media_type
                })
    except ImportError:
        print("Please install the 'wmi' module for Windows support.")
    except Exception as e:
        print(f"Error fetching drive temperatures on Windows: {e}")
    
    return drives

def main():
    system = platform.system()
    # print(f"Running on {system}...")

    if system == "Linux":
        drives = get_drive_temps_linux()
    elif system == "Windows":
        drives = get_drive_temps_windows()
    else:
        print("Unsupported operating system.")
        return
    
    
    if drives:
        driveStats = {}
        for drive in drives:
            if 'loop' not in drive['Device']:
                driveStats[drive['Mount Point']] = {
                    'device': drive['Device'],
                    'temperature': drive['Temperature'],
                    'type': drive['Type']
                }
    else:
        print("No drives found or unable to fetch data.")

    # print(driveStats) 
    return driveStats

if __name__ == "__main__":
    main()
