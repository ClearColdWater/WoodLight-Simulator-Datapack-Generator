import json
import re
import os
import numpy as np

# --- Configuration ---
LOG_PATH = r"latest.log" # Change to your log path
OUTPUT_FILE = "data_minecraft.txt" # Output filename
# ---------------------

def parse_log():
    # 1. Load existing data if available (Incremental Update)
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    data = json.loads(content)
                else:
                    data = {}
            print(f"Loaded existing data from {OUTPUT_FILE}")
        except Exception as e:
            print(f"Error loading existing data: {e}. Starting with empty data.")
            data = {}
    else:
        data = {}
    
    # Regex to match LOG_DATA::{...}
    # Minecraft logs contain timestamps/thread info, so we need to filter them out
    pattern = re.compile(r'LOG_DATA::(\{.*\})')
    
    print(f"Reading: {LOG_PATH}")
    
    new_records_count = 0

    try:
        with open(LOG_PATH, "r", encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    try:
                        json_str = match.group(1)
                        record = json.loads(json_str)
                        
                        design = record.get('design')
                        tick = record.get('tick')
                        
                        if design and tick is not None:
                            if design not in data:
                                data[design] = []
                            
                            # The simulator records ticks. Convert to seconds (tick / 20)
                            # You might want to add a check here to avoid duplicates if processing the same log twice,
                            # but simple list appending is the standard behavior for this script.
                            data[design].append(tick / 20.0)
                            new_records_count += 1
                        
                    except json.JSONDecodeError:
                        print(f"Parse error: {line}")
                    except Exception as e:
                        print(f"Unknown error: {e}")
    except FileNotFoundError:
        print(f"Log file not found: {LOG_PATH}")
        return

    print(f"Processed {new_records_count} new records.")

    # Output statistics
    print("-" * 30)
    for design, times in data.items():
        if len(times) > 0:
            print(f"Design: {design}")
            print(f"  Samples: {len(times)}")
            print(f"  Avg Time: {np.mean(times):.2f}s")
    print("-" * 30)

    # Save compatible format
    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    parse_log()
