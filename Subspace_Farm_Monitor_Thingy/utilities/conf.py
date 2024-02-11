from collections import defaultdict
import time

# Initialize state
disk_farms = set()
reward_count = 0
farm_rewards = defaultdict(int)

event_times = defaultdict(str)
plot_space = {}
drive_directory = {}
farm_plot_size = defaultdict(lambda: "0")
replotting = defaultdict(lambda: False)
curr_line = str()
curr_sector_disk = defaultdict(lambda: 0)
sector_times = defaultdict(lambda: 0)
warnings = [str(), str(), str(), str(), str(), str(),str(),]
errors = [str(), str(), str(), str(), str(), str(),str(),]
node_warnings = [str(), str(), str(), str(), str(), str(),str(),]
node_errors = [str(), str(), str(), str(), str(), str(),str(),]
total_error_count = 0
curr_farm = None
no_more_drives = False
startTime = 0
wallet = str()
balance = "0.0"
peers = str()
best_block = str()
finalized = str()
imported = str()
ul = str()
dl = str()
node_log_file = str()
last_logs = [str(), str(), str(), str(), str(), str(),str(),]
last_node_logs = [str(), str(), str(), str(), str(), str(),]  # However many initialized is how many it'll show
total_completed = 0 
show_logging = True
hour_24 = False
deltas = defaultdict(lambda: '00:00')



