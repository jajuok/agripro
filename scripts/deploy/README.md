# Automated Coolify Deployment for AgriScheme Pro

This directory contains fully automated deployment scripts for deploying AgriScheme Pro to a Coolify instance on OVHcloud VPS.

## Quick Start

### Prerequisites

1. A fresh Ubuntu 22.04 LTS VPS from OVHcloud
2. Root SSH access to the server
3. A domain name with DNS access
4. Your server IP address

### One-Command Deployment

From your local machine:

```bash
./scripts/deploy/deploy.sh <SERVER_IP> <DOMAIN> <SSH_KEY_PATH>
```

Example:
```bash
./scripts/deploy/deploy.sh 51.178.42.123 agrischeme.com ~/.ssh/id_rsa
```

## What Gets Deployed

The automated deployment will:

1. ✓ Configure server (firewall, updates, security)
2. ✓ Install and configure Coolify
3. ✓ Set up DNS (with instructions)
4. ✓ Deploy 10 PostgreSQL databases
5. ✓ Deploy Redis
6. ✓ Deploy Kafka cluster
7. ✓ Create Coolify project structure
8. ✓ Configure monitoring (Prometheus + Grafana)
9. ✓ Set up automated backups
10. ✓ Deploy all 15 microservices
11. ✓ Run database migrations
12. ✓ Configure API gateway routing

## Manual Steps Required

Only 2 manual steps:

1. **DNS Configuration** - Add A records (script will show you what to add)
2. **GitHub Integration** - Connect your repository in Coolify UI (one-time setup)

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `deploy.sh` | Main orchestration script |
| `01-server-setup.sh` | Server initialization and security |
| `02-install-coolify.sh` | Coolify installation |
| `03-configure-dns.sh` | DNS configuration helper |
| `04-deploy-databases.sh` | PostgreSQL database deployment |
| `05-deploy-infrastructure.sh` | Redis, Kafka deployment |
| `06-deploy-services.sh` | Microservice deployment |
| `07-configure-monitoring.sh` | Prometheus + Grafana setup |
| `08-run-migrations.sh` | Database migrations |
| `utils/` | Helper functions and utilities |

## Configuration

Edit `config/deployment.env` to customize:

```bash
# Server Configuration
SERVER_USER=root
SSH_PORT=22

# Database Configuration
POSTGRES_VERSION=16
POSTGRES_USER=agrischeme_admin
POSTGRES_PASSWORD=<your-password>

# Service Configuration
SERVICES_TO_DEPLOY=(auth farmer farm financial gis market ai iot livestock task inventory notification traceability compliance integration)

# Monitoring
ENABLE_MONITORING=true
GRAFANA_PASSWORD=<your-password>
```

## Deployment Phases

### Phase 1: Server Setup (5 minutes)
- System updates
- Firewall configuration
- Docker installation
- Security hardening

### Phase 2: Coolify Installation (5 minutes)
- Coolify installation
- Initial configuration
- SSL setup

### Phase 3: Infrastructure (10 minutes)
- 10 PostgreSQL containers
- Redis cluster
- Kafka + Zookeeper

### Phase 4: Services (20 minutes)
- 15 FastAPI microservices
- Environment variables
- Health checks

### Phase 5: Finalization (5 minutes)
- Database migrations
- Monitoring setup
- Backup configuration

**Total Time: ~45 minutes** (mostly automated)

## Rollback

If something goes wrong:

```bash
./scripts/deploy/rollback.sh <SERVER_IP> <SSH_KEY_PATH>
```

This will:
- Stop all services
- Create backup
- Restore to clean state

## Troubleshooting

### Check deployment status
```bash
./scripts/deploy/status.sh <SERVER_IP> <SSH_KEY_PATH>
```

### View logs
```bash
./scripts/deploy/logs.sh <SERVER_IP> <SERVICE_NAME>
```

### Retry failed step
```bash
./scripts/deploy/retry.sh <SERVER_IP> <PHASE_NUMBER>
```

## Security Notes

- All passwords are generated automatically and stored in `.secrets/` (gitignored)
- SSH key authentication is required
- Firewall is configured to allow only necessary ports
- SSL certificates are automatically provisioned via Let's Encrypt

## Support

For issues or questions:
- Check logs: `./scripts/deploy/logs.sh`
- View status: `./scripts/deploy/status.sh`
- GitHub Issues: https://github.com/jajuok/agripro/issues

---

**Time to Production: ~1 hour** (including manual DNS setup)
