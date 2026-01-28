import os
import numpy as np
import matplotlib.pyplot as plt
import json
import scipy.stats 

# ================= CONFIGURATION =================
# Path to the data file
DATA_FILE = "data_minecraft.txt"

# Path to your designs folder (used for filtering)
# Only designs found in this folder will be analyzed and plotted.
DESIGNS_PATH = r"designs"

# Max time in seconds to consider a run a "failure" (timeout)
# Default is 5 minutes (300 seconds)
TIMEOUT_SECONDS = 300 
# =================================================

def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Please run the log parser first.")
        return {}
    
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("Error decoding JSON.")
            return {}

def get_active_designs():
    """Returns a list of design names (without .nbt) found in the designs folder."""
    if not os.path.exists(DESIGNS_PATH):
        print(f"Warning: Designs path not found: {DESIGNS_PATH}")
        print("Plotting all data found in text file instead.")
        return None # Return None to indicate no filtering

    files = [f for f in os.listdir(DESIGNS_PATH) if f.endswith(".nbt")]
    # Strip extension
    return [f[:-4] for f in files]

def analyze_data(data, active_designs):
    print(f"{'Design Name':<50} | {'Avg (s)':<10} | {'Std Dev':<10} | {'Std Err':<10} | {'Samples':<8} | {'Fail Rate'}")
    print("-" * 100)

    # If active_designs is None (folder not found), use all keys from data
    keys_to_process = active_designs if active_designs is not None else data.keys()

    for name in keys_to_process:
        if name not in data:
            continue
            
        times = np.array(data[name])
        
        if len(times) == 0:
            print(f"{name:<50} | No Data")
            continue

        avg = np.mean(times)
        std_dev = np.std(times)
        # Standard Error = StdDev / sqrt(N)
        std_err = std_dev / np.sqrt(len(times))
        
        # Calculate failure rate (ratio of runs that hit the timeout)
        failure_rate = (times >= TIMEOUT_SECONDS).mean()

        print(f"{name:<50} | {avg:<10.2f} | {std_dev:<10.2f} | {std_err:<10.2f} | {len(times):<8} | {failure_rate:.2%}")
    print("-" * 100)

def plot_fixed(data, active_designs):
    # PDF plot with Boundary Correction
    x = np.linspace(0, 120, 500)
    
    keys_to_process = active_designs if active_designs is not None else data.keys()

    plt.figure(figsize=(10, 6))

    for name in keys_to_process:
        if name not in data: continue
        if "validation" in name: continue # Optional skip
            
        dataset = np.array(data[name])
        if len(dataset) < 2: continue

        # 1. Normal KDE
        try:
            kde = scipy.stats.gaussian_kde(dataset)
            y_raw = kde(x)
            
            # 2. Bandwidth & Correction
            bw = np.sqrt(kde.covariance[0, 0])
            correction_factor = scipy.stats.norm.cdf(x, loc=0, scale=bw)
            y = y_raw / correction_factor
            
            plt.plot(x, y, label=name)
        except Exception as e:
            print(f"Skipping plot for {name}: {e}")
        
    plt.legend()
    plt.xlabel("Time (seconds)")
    plt.ylabel("Probability Density")
    plt.xlim(0, 120)
    plt.title("Portal Light Time PDF (Corrected KDE)")
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_histogram(data, active_designs):
    keys_to_process = active_designs if active_designs is not None else data.keys()

    plt.figure(figsize=(10, 6))
    
    for name in keys_to_process:
        if name not in data: continue
        if "validation" in name: continue
        
        if len(data[name]) > 0:
            plt.hist(data[name], bins=120, alpha=0.5, density=True, 
                    label=name, range=(0, 120))
    
    plt.legend()
    plt.xlabel("Time (seconds)")
    plt.ylabel("Probability")
    plt.title("Portal Light Time Histogram")
    plt.show()

if __name__ == "__main__":
    # 1. Load Data
    full_data = load_data()
    
    if full_data:
        # 2. Get Filtering List
        valid_designs = get_active_designs()
        
        # 3. Print Statistics
        analyze_data(full_data, valid_designs)

        # 4. Plot
        # You can comment out one of these if you prefer
        plot_histogram(full_data, valid_designs)
        plot_fixed(full_data, valid_designs)
