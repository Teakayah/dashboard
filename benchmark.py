import time
import subprocess

start = time.time()
subprocess.run(["python3", "deployment/update_flood_data.py"], capture_output=True)
end = time.time()
print(f"Time taken: {end - start:.4f}s")
