# Podman in Toolbox — Using the Host Socket (Bazzite)

This guide explains how to configure Podman inside a **Toolbox container** to use the **host's Podman socket** on Bazzite. Once set up, `podman` and `podman-compose` commands inside Toolbox operate on host containers directly.

---

## Prerequisites

- **Host OS**: Bazzite (or any Linux using rootless Podman)
- **Toolbox**: Fedora-based container (`toolbox enter`)

---

## Setup

### 1. On the host — verify the Podman socket

```bash
ls -l /run/user/$UID/podman/podman.sock
```

Expected output:

```
srw-rw----. 1 user group 0 [date] /run/user/1000/podman/podman.sock
```

If the socket does not exist, enable the Podman user service:

```bash
systemctl --user enable --now podman.socket
```

### 2. Inside Toolbox — install Podman tools

```bash
sudo dnf install -y podman-remote podman-compose
```

> **Note:** `podman-compose` pulls in the full `podman` package as a dependency. This is expected — step 5 handles the resulting conflict.

### 3. Inside Toolbox — configure the remote connection

Create `~/.config/containers/containers.conf`:

```bash
mkdir -p ~/.config/containers
cat > ~/.config/containers/containers.conf << 'EOF'
[engine]
active_service = "host"

[engine.service_destinations]
  [engine.service_destinations.host]
  uri = "unix:///run/user/1000/podman/podman.sock"
  identity = ""
EOF
```

> Replace `1000` with your actual UID if different (`echo $UID`).

### 4. Configure `.zshrc`

`DOCKER_HOST` is needed so that `podman-compose` can locate the socket automatically:

```bash
echo 'export DOCKER_HOST=unix:///run/user/$(id -u)/podman/podman.sock' >> ~/.zshrc
source ~/.zshrc
```

### 5. Create a `podman` wrapper in `~/.local/bin`

Installing `podman-compose` pulls in the full `podman` package, which places a local Podman daemon at `/usr/bin/podman`. That daemon cannot run inside Toolbox (no user namespace), so `podman` commands fail.

A shell alias in `.zshrc` would fix this for interactive sessions, but **aliases are not loaded by non-interactive shells** — meaning task runners like `go-task` or scripts would still call `/usr/bin/podman` and fail.

The reliable fix is a wrapper script in `~/.local/bin`, which takes priority over `/usr/bin` in the PATH and works in all contexts. Since `~/.local/bin` is shared between the host and Toolbox, the wrapper uses `/run/.toolboxenv` (a file present in every Toolbox container) to detect the environment:

```bash
cat > ~/.local/bin/podman << 'EOF'
#!/bin/sh
if [ -f /run/.toolboxenv ]; then
    exec podman-remote --connection=host "$@"
else
    exec /usr/bin/podman "$@"
fi
EOF
chmod +x ~/.local/bin/podman
```

This wrapper is transparent on both host and Toolbox — no conflict, no manual switching.

### 6. Verify

```bash
podman ps            # should list host containers
podman-compose version
```

Both should return without errors.

---

## Troubleshooting

**Socket missing on host**

```bash
systemctl --user restart podman.socket
```

**Permission denied on the socket**

```bash
# Run on the host
chmod 660 /run/user/$UID/podman/podman.sock
```

**`podman` fails with "cannot re-exec process to join user namespace"**

The local `/usr/bin/podman` is being called instead of the wrapper. Check that:

```bash
which podman                     # should be ~/.local/bin/podman
ls -l ~/.local/bin/podman        # wrapper exists and is executable
```

If the wrapper is missing, follow step 5. If it exists but is not picked up, check that `~/.local/bin` is before `/usr/bin` in your PATH.

**Connection error from `podman-remote`**

```bash
ls -l /run/user/$UID/podman/podman.sock   # socket exists?
echo $DOCKER_HOST                          # env var set?
systemctl --user restart podman.socket    # restart if needed
```

---

## Quick Reference

| Step                        | Command                                                                         |
| --------------------------- | ------------------------------------------------------------------------------- |
| Check socket (host)         | `ls -l /run/user/$UID/podman/podman.sock`                                       |
| Enable Podman socket (host) | `systemctl --user enable --now podman.socket`                                   |
| Install tools (Toolbox)     | `sudo dnf install -y podman-remote podman-compose`                              |
| Configure connection        | Edit `~/.config/containers/containers.conf`                                     |
| Set DOCKER_HOST             | `export DOCKER_HOST=unix:///run/user/$(id -u)/podman/podman.sock` in `~/.zshrc` |
| Create wrapper              | `~/.local/bin/podman` — see step 5                                              |
| Test                        | `podman ps`                                                                     |

---

## Why this approach

Connecting via the Unix socket is simpler and safer than SSH-based remoting: no network exposure, no extra authentication, and no conflict with the host Podman daemon.

The `~/.local/bin/podman` wrapper is the key piece: it ensures `podman` resolves to `podman-remote --connection=host` in **all shell contexts** (interactive, non-interactive, task runners), without requiring aliases or environment variables to be loaded first. The `/run/.toolboxenv` detection keeps the wrapper safe to use on the host as well.
