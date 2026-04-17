import time
import sys
import subprocess

start_time = time.time()
subprocess.run([sys.executable, "deployment/generate_index.py"], stdout=subprocess.DEVNULL)
end_time = time.time()
print(f"Execution time: {end_time - start_time:.4f} seconds")
