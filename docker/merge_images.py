#!/usr/bin/env python3
"""
Extract /workspace from each PatchEval Docker image into a single directory.

Usage:
    python merge_images.py

This creates:
    ./workspaces/
        cve-2021-23376/
        cve-2024-25620/
        ...
"""

import os
import subprocess
import re

IMAGES_FILE = "../data/images_python.txt"
OUTPUT_DIR = "workspaces"


def extract_cve_workspaces():
    """Extract /workspace from each image into OUTPUT_DIR/cve-xxx/"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(IMAGES_FILE) as f:
        images = [line.strip() for line in f if line.strip()]

    total = len(images)
    success = 0
    failed = []

    for i, image in enumerate(images, 1):
        # Extract CVE ID from image name (e.g., cve-2021-23376)
        match = re.search(r"(cve-[\d-]+)", image, re.IGNORECASE)
        if not match:
            print(f"[{i}/{total}] Skipping {image} - no CVE ID found")
            continue

        cve_id = match.group(1).lower()
        dest_dir = os.path.join(OUTPUT_DIR, cve_id)

        if os.path.exists(dest_dir):
            print(f"[{i}/{total}] Skipping {cve_id} - already extracted")
            # Delete the image to free disk space
            subprocess.run(
                ["docker", "rmi", image],
                capture_output=True,
            )
            print(f"         Deleted image {image}")
            success += 1
            continue

        print(f"[{i}/{total}] Extracting {cve_id}...")

        container_name = f"temp_{cve_id}"
        try:
            # Create container (don't start it)
            subprocess.run(
                ["docker", "create", "--name", container_name, image],
                check=True,
                capture_output=True,
            )

            # Copy /workspace to local directory
            subprocess.run(
                ["docker", "cp", f"{container_name}:/workspace", dest_dir],
                check=True,
            )

            success += 1
            print(f"         -> {dest_dir}")

        except subprocess.CalledProcessError as e:
            print(f"         ERROR: {e}")
            failed.append(cve_id)

        finally:
            # Clean up temporary container
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
            )

            # Delete the image to free disk space
            subprocess.run(
                ["docker", "rmi", image],
                capture_output=True,
            )
            print(f"         Deleted image {image}")

    print(f"\nDone! Extracted {success}/{total} workspaces to ./{OUTPUT_DIR}/")
    if failed:
        print(f"Failed: {failed}")


if __name__ == "__main__":
    extract_cve_workspaces()
