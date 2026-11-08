import subprocess
import sys
import multiprocessing

def run_test(i):
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/test_usability.py", "-k", "test_viz_elements_have_height", "-v", "--tb=short"],
        capture_output=True, text=True
    )
    if "FAILED" in result.stdout or result.returncode != 0:
        return (False, i, result.stdout)
    return (True, i, "")

def main():
    pool = multiprocessing.Pool(processes=2) # Only 2 concurrent to avoid overloading the local port for pytest's builtin server
    results = pool.map(run_test, range(50))
    pool.close()
    pool.join()

    failed = False
    for success, i, out in results:
        if not success:
            print(f"Failed on run {i}")
            print(out)
            failed = True
            break

    if not failed:
        print("Passed all 50 concurrent runs!")

if __name__ == "__main__":
    main()
