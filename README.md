# MinIO for Asustor NAS

This project builds an Asustor App (`.apk`) for MinIO Object Storage. It allows you to run a standalone MinIO server on your NAS without using Docker.

## Features

- **Standalone Binary**: Runs the native MinIO binary for ARM64 (configurable).
- **Configurable**: Uses a `minio.env` file in the configuration share for easy setup.
- **Persistent Data**: Stores data in a dedicated share folder.
- **Service Management**: Starts/Stops via App Central.

## Build Instructions

1.  **Prerequisites**: Python 3 installed on your machine.
2.  **Run the Build Script**:
    ```bash
    cd asustor-minio
    python build_minio_apk.py
    ```
    This will:
    - Download the MinIO binary.
    - Create the package structure.
    - Generate `minio_RELEASE.xxxx_arm64.apk`.

## Installation

1.  Log in to ADM.
2.  Open **App Central**.
3.  Click **Manual Install**.
4.  Upload the generated `.apk` file.
5.  Follow the installation wizard.

## Configuration

After installation, a share folder named `MinIOConfig` will be created.

1.  Open **File Explorer** and navigate to `MinIOConfig`.
2.  Edit `minio.env` to change:
    - `MINIO_ROOT_USER` (Default: `admin`)
    - `MINIO_ROOT_PASSWORD` (Default: `password123`)
    - `MINIO_CONSOLE_ADDRESS` (Default: `:9001`)
    - `MINIO_ADDRESS` (Default: `:9000`)
3.  Restart the MinIO app in App Central for changes to take effect.

## Data

Data is stored in the `MinIOData` share folder by default. You can change this path in `minio.env` if needed.

## Disclaimer

This is an unofficial package. Use at your own risk.