# 🚀 Auto-Start & Safe Deployment on Raspberry Pi

This project is designed to run automatically on boot via a systemd service on a Raspberry Pi (tested on Pi 5 with Raspberry Pi OS Bullseye). It also supports versioned, rollback-safe deployments using a simple script.

## 🛠️ One-Time Setup

### 1. Create the release directory

```bash
sudo mkdir -p /opt/gialappas/releases
sudo chown -R pi:pi /opt/gialappas
```

### 2. Create the systemd service

Create the service file:

```bash
sudo nano /etc/systemd/system/gialappas.service
```

Paste the following:

```ini
[Unit]
Description=Gialappas Service
After=network.target

[Service]
ExecStart=/usr/local/bin/gialappas
Restart=always
User=pi
WorkingDirectory=/home/pi/
Environment=GO_ENV=production

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable gialappas.service
sudo systemctl start gialappas.service
```

### 3. Set up symlink (only once)

Ensure that `/usr/local/bin/gialappas` points to the "latest" version:

```bash
sudo rm /usr/local/bin/gialappas  # Remove existing binary if needed
sudo ln -s /opt/gialappas/releases/latest /usr/local/bin/gialappas
```

## 🔄 Deploying Updates

Use the `deploy.sh` script to:

- Build a new binary with a timestamp
- Store it under `/opt/gialappas/releases/`
- Update the latest symlink
- Restart the systemd service

### 1. Save this script as `deploy.sh` in your project root

```bash
#!/bin/bash

set -e

APP_NAME=gialappas
RELEASE_DIR=/opt/$APP_NAME/releases
BUILD_DIR=$(pwd)
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
TARGET_BIN=$RELEASE_DIR/$APP_NAME-$TIMESTAMP

echo "🔨 Building $APP_NAME..."
go build -o $TARGET_BIN

echo "🔗 Updating symlink..."
ln -sfn $TARGET_BIN $RELEASE_DIR/latest
sudo ln -sfn $RELEASE_DIR/latest /usr/local/bin/$APP_NAME

echo "♻️ Restarting systemd service..."
sudo systemctl restart $APP_NAME.service

echo "✅ Deployed $APP_NAME -> $TARGET_BIN"
```

### 2. Make it executable

```bash
chmod +x deploy.sh
```

### 3. Deploy

```bash
./deploy.sh
```

## 📋 Monitoring & Logs

Check if the service is running:

```bash
systemctl status gialappas.service
```

Follow logs in real time:

```bash
journalctl -u gialappas.service -f
```

## 🧹 Optional: Clean Up Old Builds

To remove older versions and keep only the 5 most recent:

```bash
find /opt/gialappas/releases -name 'gialappas-*' | sort | head -n -5 | xargs rm
```

## ✅ Summary: One-Time vs Per-Update Tasks

| Task                                               | When to Do It |
| -------------------------------------------------- | ------------- |
| Create `/opt/gialappas/releases/`                  | Once          |
| Create and enable the systemd service              | Once          |
| Set up symlink `/usr/local/bin/gialappas` → latest | Once          |
| Run `./deploy.sh`                                  | Every update  |
| Clean up old builds                                | Occasionally  |
