import subprocess

subprocess.call(["podman", "build", "-t", "gv_bot", "."])
subprocess.call(
    [
        "podman",
        "run",
        "--network",
        "gv_bot",
        "localhost/gv_bot:latest",
    ]
)
