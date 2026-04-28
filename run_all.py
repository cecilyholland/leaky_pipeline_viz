"""
Regenerate all visualization HTML files.

Run from repo root:
    python run_all.py
"""

import subprocess
import sys

SCRIPTS = [
    "visualizations/chart1_bls_age_cliff.py",
    "visualizations/chart2_nscg_intersectional.py",
    "visualizations/chart3_bigtech_timeline.py",
    "visualizations/chart4_ipeds_pipeline.py",
]


def main():
    print("Regenerating all visualizations...\n")

    for script in SCRIPTS:
        print(f"Running {script}...")
        result = subprocess.run([sys.executable, script], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ERROR: {result.stderr}")
        else:
            print(f"  Done")

    print("\nAll charts regenerated. Refresh your browser to see changes.")


if __name__ == "__main__":
    main()
