import os
import subprocess
import tempfile
import time

import pynvim
import pytest


@pytest.fixture(scope="session")
def nvim_path():
    """Locate a Neovim binary."""
    for candidate in ("nvim", "/usr/local/bin/nvim", "/opt/homebrew/bin/nvim"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True, check=True)
            return candidate
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    pytest.skip("Neovim binary not found")


@pytest.fixture
def nvim(nvim_path):
    """Start a headless Neovim instance and yield a connected pynvim session."""
    tmpdir = tempfile.mkdtemp()
    socket = os.path.join(tmpdir, "nvim.sock")

    proc = subprocess.Popen(
        [nvim_path, "--headless", "--listen", socket, "--cmd", "set nocp"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for socket to appear
    deadline = time.monotonic() + 10
    while not os.path.exists(socket):
        if time.monotonic() > deadline:
            proc.kill()
            proc.wait()
            pytest.fail("Neovim did not create socket in time")
        time.sleep(0.05)

    try:
        client = pynvim.attach("socket", path=socket)
        yield client
    finally:
        try:
            client.close()
        except Exception:
            pass
        proc.terminate()
        proc.wait(5)
