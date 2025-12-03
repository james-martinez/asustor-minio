import os
import urllib.request
import zipfile
import tarfile
import shutil
import time

# Configuration
MINIO_VERSION = "RELEASE.2025-09-07T16-13-09Z"
ARCH = "linux-arm64"
DOWNLOAD_URL = f"https://dl.min.io/server/minio/release/{ARCH}/archive/minio.{MINIO_VERSION}"
APK_NAME = f"minio_{MINIO_VERSION}_arm64.apk"
ICON_URL = "https://min.io/resources/img/logo/MINIO_Bird.png" # Placeholder, ideally use a proper icon

def download_file(url, filename):
    print(f"Downloading {filename} from {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        raise

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                st = os.stat(full_path)
                ti = tarfile.TarInfo(name=rel_path)
                ti.size = st.st_size
                ti.mtime = time.time()
                
                # Permissions: 755 for scripts/binaries, 644 for others
                if file.endswith('.sh') or file.endswith('.py') or os.access(full_path, os.X_OK):
                    ti.mode = 0o755
                else:
                    ti.mode = 0o644
                
                ti.uid = 0
                ti.gid = 0
                ti.uname = "root"
                ti.gname = "root"

                with open(full_path, "rb") as f:
                    tar.addfile(ti, f)

def build_apkg():
    print(f"--- Building Asustor Package: {APK_NAME} ---")
    
    build_root = "build_env"
    control_dir = os.path.join(build_root, "CONTROL")
    bin_dir = os.path.join(build_root, "bin")

    # 1. Clean Build Env
    if os.path.exists(build_root): shutil.rmtree(build_root)
    os.makedirs(control_dir)
    os.makedirs(bin_dir)

    # 2. Download MinIO
    minio_bin_path = "minio_bin"
    if not os.path.exists(minio_bin_path):
        download_file(DOWNLOAD_URL, minio_bin_path)
    
    shutil.copy(minio_bin_path, os.path.join(bin_dir, "minio"))
    os.chmod(os.path.join(bin_dir, "minio"), 0o755)

    # 3. Process CONTROL Files
    required_files = ["config.json", "start-stop.sh"]
    for f in required_files:
        if not os.path.exists(f):
            print(f"ERROR: {f} missing! Ensure it is in this folder.")
            return
        shutil.copy(f, os.path.join(control_dir, f))

    # Fix Line Endings for Script
    script_path = os.path.join(control_dir, "start-stop.sh")
    with open(script_path, "rb") as infile:
        content = infile.read().replace(b"\r\n", b"\n")
    with open(script_path, "wb") as outfile:
        outfile.write(content)
    os.chmod(script_path, 0o755)

    # 4. Smart File Handling (Changelog/Description)
    if os.path.exists("description.txt"):
        shutil.copy("description.txt", os.path.join(control_dir, "description.txt"))
    else:
        with open(os.path.join(control_dir, "description.txt"), "w") as f: f.write("MinIO Object Storage for Asustor")

    if os.path.exists("changelog.txt"):
        shutil.copy("changelog.txt", os.path.join(control_dir, "changelog.txt"))
    else:
        with open(os.path.join(control_dir, "changelog.txt"), "w") as f: f.write("Initial Version")

    # 5. Smart Icon Handling
    if os.path.exists("icon.png"):
        print("Using local icon.png")
        shutil.copy("icon.png", os.path.join(control_dir, "icon.png"))
    else:
        print("No icon found, downloading default...")
        # Note: MinIO logo might need resizing or format conversion for Asustor, but we'll download a placeholder
        # Ideally, user should provide a 256x256 png
        try:
             download_file(ICON_URL, "icon.png")
             shutil.copy("icon.png", os.path.join(control_dir, "icon.png"))
        except:
             print("Failed to download icon. Creating dummy.")
             with open(os.path.join(control_dir, "icon.png"), "wb") as f: pass # Empty file

    # 6. Create Package
    print("Creating internal tarballs...")
    make_tarfile("control.tar.gz", control_dir)
    
    # Exclude CONTROL from data.tar.gz
    shutil.move(control_dir, "CONTROL_TEMP")
    make_tarfile("data.tar.gz", build_root)
    shutil.move("CONTROL_TEMP", control_dir)

    with open("apkg-version", "w") as f:
        f.write("2.0\n")

    print(f"Zipping final package {APK_NAME}...")
    with zipfile.ZipFile(APK_NAME, 'w', zipfile.ZIP_DEFLATED) as apk:
        apk.write("apkg-version")
        apk.write("control.tar.gz")
        apk.write("data.tar.gz")

    # Cleanup
    os.remove("apkg-version")
    os.remove("control.tar.gz")
    os.remove("data.tar.gz")
    # Keep minio_bin for future builds to save bandwidth
    # if os.path.exists("minio_bin"): os.remove("minio_bin")
    shutil.rmtree(build_root)
    if os.path.exists("CONTROL_TEMP"): shutil.rmtree("CONTROL_TEMP")

    print("Success! Package created.")

if __name__ == "__main__":
    build_apkg()