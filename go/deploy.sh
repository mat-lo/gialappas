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
