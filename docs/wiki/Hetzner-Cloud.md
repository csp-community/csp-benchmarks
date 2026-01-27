# Hetzner Cloud Integration

csp-benchmarks supports running benchmarks on dedicated Hetzner Cloud servers for consistent, reproducible results.

## Why Hetzner Cloud?

- **Consistent environment**: Dedicated VMs provide stable performance
- **Cost-effective**: Pay only for benchmark time
- **Automated**: Full automation via CLI and GitHub Actions
- **Reproducible**: Same hardware configuration each run

## Setup

### 1. Create Hetzner Cloud Account

1. Go to [Hetzner Cloud Console](https://console.hetzner.cloud/)
1. Create a new project
1. Generate an API token with read/write permissions

### 2. Configure Authentication

Set the `HCLOUD_TOKEN` environment variable:

```bash
export HCLOUD_TOKEN="your-api-token-here"
```

For GitHub Actions, add it as a repository secret.

### 3. (Optional) SSH Key Setup

For passwordless access:

1. Add your SSH public key to Hetzner Cloud
1. Set the key name in the CLI: `--ssh-key-name my-key`
1. Provide the private key path: `--ssh-key ~/.ssh/id_rsa`

## CLI Usage

### Run Benchmarks

```bash
# Basic run
python -m csp_benchmarks.hetzner.cli run

# With options
python -m csp_benchmarks.hetzner.cli run \
    --server-type cx32 \
    --commits "HEAD~5..HEAD" \
    --push
```

### Options

| Option           | Description             | Default                |
| ---------------- | ----------------------- | ---------------------- |
| `--token`        | Hetzner API token       | `$HCLOUD_TOKEN`        |
| `--server-name`  | Server name             | `csp-benchmark-runner` |
| `--server-type`  | Server size             | `cx32`                 |
| `--ssh-key`      | Path to SSH private key | None                   |
| `--ssh-key-name` | Hetzner SSH key name    | None                   |
| `--branches`     | Branches to benchmark   | `main`                 |
| `--commits`      | Commit range            | None                   |
| `--reuse`        | Reuse existing server   | False                  |
| `--keep-server`  | Keep server after run   | False                  |
| `--push`         | Push results to repo    | False                  |

### Cleanup

Remove leftover servers:

```bash
python -m csp_benchmarks.hetzner.cli cleanup
```

## Server Types

| Type | vCPU | RAM  | Use Case                      |
| ---- | ---- | ---- | ----------------------------- |
| cx22 | 2    | 4GB  | Quick tests                   |
| cx32 | 4    | 8GB  | Standard benchmarks (default) |
| cx42 | 8    | 16GB | Large benchmarks              |
| cx52 | 16   | 32GB | Full suite                    |

## GitHub Actions

The benchmarks workflow automatically uses Hetzner Cloud:

```yaml
# .github/workflows/benchmarks.yaml
- name: Run benchmarks on Hetzner
  env:
    HCLOUD_TOKEN: ${{ secrets.HCLOUD_TOKEN }}
  run: |
    python -m csp_benchmarks.hetzner.cli run --push
```

### Required Secrets

| Secret                    | Description                |
| ------------------------- | -------------------------- |
| `HCLOUD_TOKEN`            | Hetzner Cloud API token    |
| `HETZNER_SSH_PRIVATE_KEY` | SSH private key (optional) |

## Architecture

```
┌─────────────────┐
│  GitHub Action  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  CLI Runner     │────▶│  Hetzner Cloud  │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┘
         ▼
┌─────────────────┐
│  Ubuntu Server  │
│  - Clone repo   │
│  - Run ASV      │
│  - Push results │
└─────────────────┘
```

## Troubleshooting

### Server Creation Fails

- Check API token permissions
- Verify server type is available in the selected location
- Check Hetzner Cloud quotas

### SSH Connection Fails

- Ensure the server has finished provisioning (cloud-init)
- Verify SSH key is correctly configured
- Check firewall rules in Hetzner Cloud

### Benchmarks Fail

- Check CSP build dependencies are installed
- Verify Python version compatibility
- Review cloud-init logs: `ssh root@<ip> cat /var/log/cloud-init-output.log`

## Cost Estimation

Approximate costs (as of 2024):

| Server | Hourly | Monthly |
| ------ | ------ | ------- |
| cx22   | €0.006 | €4.35   |
| cx32   | €0.011 | €7.68   |
| cx42   | €0.021 | €15.03  |
| cx52   | €0.040 | €28.73  |

Servers are automatically deleted after benchmarks complete.
