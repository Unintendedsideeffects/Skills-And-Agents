---
name: home-assistant-docker-update
description: Update a Docker-based Home Assistant deployment to the latest stable image and verify the service is healthy afterward. Use when a user asks to upgrade Home Assistant, check whether a Docker-based HA update is safe, or recover Home Assistant after an image refresh.
---

# Home Assistant Docker Update

Use this skill for Docker-based Home Assistant deployments.

## Runtime facts

On first successful run, discover and persist the local runtime facts in:

- `references/local-runtime-facts.md`

Store only the facts needed for repeatable upgrades, for example:

- host or container where HA actually runs
- container runtime (`docker`, `podman`, compose, etc.)
- container name
- image reference
- network mode
- restart policy
- bind mounts
- privilege requirements
- HA base URL
- token file location or verification method

On later runs:

1. Read `references/local-runtime-facts.md` first if it exists.
2. Re-verify the critical facts before making changes.
3. Update the file if the deployment drifted.

## Workflow

1. Confirm deployment model first.
   - Verify Home Assistant is actually containerized.
   - Identify the runtime and the live container/service to update.
   - Inspect the running container before touching it:
     - image
     - network mode
     - restart policy
     - mounts
     - privilege level
   - Do not assume helper scripts are authoritative unless they match the live deployment.

2. Pull the new image.
   - Preferred image is normally the current stable Home Assistant image for the detected runtime.
   - Keep note of the previous image tag in case rollback is needed.

3. Recreate the container with the same runtime settings.
   - Preserve the existing runtime settings exactly unless there is a clear reason to change them.
   - Stop and remove the old container only after the new image has been pulled.

4. Verify Home Assistant health.
   - Check the container or service is running again.
   - Query the HA API using the discovered base URL and token method.
   - Confirm:
     - API responds
     - `state` is `RUNNING`
     - version is the expected upgraded version

5. Check for immediate regressions.
   - Review recent HA logs for startup errors.
   - Separate pre-existing issues from upgrade-induced issues.
   - If an automation or integration needs a small post-upgrade fix, prefer the smallest targeted change and verify it.

## Commands

Inspect current container:

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
docker inspect <home-assistant-container> --format "{{.Config.Image}} {{.HostConfig.NetworkMode}} {{.HostConfig.RestartPolicy.Name}}"
```

Upgrade:

```bash
docker pull ghcr.io/home-assistant/home-assistant:stable
docker stop <home-assistant-container>
docker rm <home-assistant-container>
docker run -d --name <home-assistant-container> <preserved-runtime-args> ghcr.io/home-assistant/home-assistant:stable
```

Verify API:

```bash
python3 - <<'PY'
import requests
from pathlib import Path
base = "<ha-base-url>"
token = Path("<token-file>").read_text().strip()
headers = {"Authorization": f"Bearer {token}"}
print(requests.get(base + "/api/config", headers=headers, timeout=10).json())
PY
```

## Output

Report:

- previous image/version if known
- new image/version
- verification result
- any residual issues that were already present
- any post-upgrade fixes you applied
