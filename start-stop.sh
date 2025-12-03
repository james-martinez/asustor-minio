#!/bin/sh

# Define paths
PKG_NAME="minio"
INSTALL_DIR="/usr/local/AppCentral/$PKG_NAME"
BIN_PATH="$INSTALL_DIR/bin/minio"
PID_FILE="/var/run/$PKG_NAME.pid"
CONF_DIR="/volume1/MinIOConfig"
DATA_DIR="/volume1/MinIOData"
ENV_FILE="$CONF_DIR/minio.env"
LOG_FILE="$CONF_DIR/minio.log"

# Default Settings
DEFAULT_ROOT_USER="admin"
DEFAULT_ROOT_PASSWORD="password123"
DEFAULT_CONSOLE_PORT=":9001"
DEFAULT_API_PORT=":9000"

# --- 1. Load or Create Configuration ---
if [ ! -d "$CONF_DIR" ]; then
  mkdir -p "$CONF_DIR"
fi

if [ ! -d "$DATA_DIR" ]; then
  mkdir -p "$DATA_DIR"
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "# MinIO Configuration" > "$ENV_FILE"
  echo "MINIO_ROOT_USER=$DEFAULT_ROOT_USER" >> "$ENV_FILE"
  echo "MINIO_ROOT_PASSWORD=$DEFAULT_ROOT_PASSWORD" >> "$ENV_FILE"
  echo "MINIO_VOLUMES=$DATA_DIR" >> "$ENV_FILE"
  echo "MINIO_ADDRESS=$DEFAULT_API_PORT" >> "$ENV_FILE"
  echo "MINIO_CONSOLE_ADDRESS=$DEFAULT_CONSOLE_PORT" >> "$ENV_FILE"
  echo "MINIO_REGION=us-east-1" >> "$ENV_FILE"
fi

# Load variables from config
# We export them so MinIO picks them up
set -a
. "$ENV_FILE"
set +a

# Ensure data directory exists (in case it was changed in env file)
if [ ! -d "$MINIO_VOLUMES" ]; then
    mkdir -p "$MINIO_VOLUMES"
fi

case "$1" in
  start)
    echo "Starting $PKG_NAME..."

    # Check if already running
    if [ -f "$PID_FILE" ]; then
        if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "$PKG_NAME is already running."
            exit 0
        else
            rm "$PID_FILE"
        fi
    fi

    # Start MinIO
    # We use nohup to keep it running in the background
    # The 'server' command is used, and the volume path is passed as an argument
    nohup $BIN_PATH server "$MINIO_VOLUMES" --address "$MINIO_ADDRESS" --console-address "$MINIO_CONSOLE_ADDRESS" > "$LOG_FILE" 2>&1 &
    
    echo $! > "$PID_FILE"
    echo "$PKG_NAME started with PID $(cat $PID_FILE)."
    ;;

  stop)
    echo "Stopping $PKG_NAME..."
    
    if [ -f "$PID_FILE" ]; then
      kill $(cat "$PID_FILE")
      rm "$PID_FILE"
      echo "$PKG_NAME stopped."
    else
      # Fallback: kill by name
      killall minio 2>/dev/null
      echo "$PKG_NAME stopped (via killall)."
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac

exit 0