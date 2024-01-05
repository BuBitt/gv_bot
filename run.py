import subprocess

subprocess.call(["podman", "build", "-t", "gv_bot", "."])
subprocess.call(["podman", "run", "localhost/gv_bot:latest"])
