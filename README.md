# Container Security Lab

A hands-on lab I built to practice building, running, securing and troubleshooting containers on Linux and Kubernetes (Amazon Linux 2023, Docker, k3s, Trivy).

## Image hardening results

| | `Dockerfile.v1` (before) | `Dockerfile` (after) |
|---|---|---|
| Base image | `python:3.9` (full) | `python:3.12-slim`, multi-stage |
| Size | 1.1 GB | 122 MB |
| User | root | non-root (`appuser`, UID 10001) |
| HIGH + CRITICAL CVEs (Trivy) | 2,905 (236 critical) | 0 fixable |
| Rebuild after code change | 4.1 s | 0.6 s (dependency layer cached) |

## Vulnerability fixes

- `requests 2.25.0` pinned an old transitive dependency, `urllib3 1.26.20`, with 6 HIGH CVEs. Fixed by upgrading `requests`, which allows `urllib3 >= 2.8.0`.
- `zlib1g` HIGH CVE in the base image: Debian had a fix (`deb13u1`) that the base image did not include yet. Patched with a targeted `apt-get install --only-upgrade` in the final stage.
- Trivy gate: `trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed` went from exit 1 (blocked) to exit 0 (pass).

## Kubernetes hardening

`k8s/deploy.yaml` runs with `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, all capabilities dropped and the `RuntimeDefault` seccomp profile. `trivy config` HIGH findings went from 3 to 0.

## Troubleshooting scenarios practiced

| Area | Scenario | Key evidence |
|---|---|---|
| Docker | Container exits | Exit codes (2 = app error, 127 = command not found, 137 = OOM) |
| Docker | OOM kill | `OOMKilled=true`, `dmesg`: `CONSTRAINT_MEMCG` |
| Docker | Cannot reach app | App bound to `127.0.0.1` inside the container |
| Docker | Missing logs | Python output buffering, fixed with `PYTHONUNBUFFERED=1` |
| Docker | Disk usage | `docker system df`, log rotation in `daemon.json` |
| Kubernetes | ImagePullBackOff | Events: "pull access denied" for a missing tag |
| Kubernetes | CrashLoopBackOff | `kubectl logs` / `--previous`, exit code |
| Kubernetes | OOMKilled | Reason OOMKilled, exit code 137 |
| Kubernetes | Pending | FailedScheduling: insufficient CPU (requests) |
| Kubernetes | Service not working | Empty endpoints: selector/label mismatch |
| Kubernetes | 0/1 Ready | Readiness probe 404 on the wrong path |
| Kubernetes | Rollout and rollback | Two ReplicaSets, zero-downtime update and `rollout undo` |
| Registry | Tags vs digests | A moved tag served different code; a digest always returned the original |
| Registry | Promotion | Same digest promoted dev to prod, no rebuild |


## CI/CD pipeline

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request:

1. Build the image (tag = commit SHA)
2. Smoke test: `/health` responds and the container is not root
3. Trivy image scan gate: fails on fixable HIGH/CRITICAL
4. Trivy config scan gate on `k8s/`
5. SBOM (CycloneDX) uploaded as an artifact
6. On `main` only: push to Amazon ECR with OIDC (no stored AWS keys), immutable tags, scan on push

The IAM trust policy is limited to this repository and the `main` branch, using GitHub's immutable subject claim (owner and repository IDs).
