import os
import urllib.request
import zipfile
import tarfile
import shutil
import time
import subprocess

# Configuration
MINIO_VERSION = "RELEASE.2025-09-07T16-13-09Z"
ARCH = "linux-arm64"
DOWNLOAD_URL = f"https://dl.min.io/server/minio/release/{ARCH}/archive/minio.{MINIO_VERSION}"
APK_NAME = f"minio_{MINIO_VERSION}_arm64.apk"

# SVG Content provided by user
ICON_SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 106 18" fill="none" class="navbar_logo"><path d="M40.6149 0.304199H34.7266V17.6899H40.6149V0.304199Z" fill="currentColor"></path><path d="M27.4597 0.241986L15.5093 7.53878C15.3418 7.64426 15.1246 7.64426 14.9571 7.53878L3.00672 0.241986C2.75233 0.0868666 2.4545 0 2.15047 0H2.13806C1.23216 0 0.5 0.732161 0.5 1.63806V17.3671H6.38211V9.88418C6.38211 9.42503 6.88469 9.13961 7.27559 9.38159L13.9705 13.4767C14.6282 13.88 15.4597 13.8862 16.1236 13.4953L23.1908 9.35057C23.5817 9.12099 24.0781 9.40641 24.0781 9.85936V17.3671H29.9602V1.63806C29.9602 0.732161 29.228 0 28.3221 0H28.3097C28.0057 0 27.7141 0.0806618 27.4535 0.241986" fill="currentColor"></path><path d="M69.9642 0.304199H63.9953V8.21526C63.9953 8.66201 63.5237 8.94122 63.1328 8.73646L47.6581 0.496547C47.4224 0.372452 47.1556 0.304199 46.8887 0.304199H46.8763C45.9704 0.304199 45.2383 1.03636 45.2383 1.94226V17.6713H51.1576V9.76645C51.1576 9.32592 51.6292 9.0405 52.0201 9.24525L67.5506 17.4852C67.7864 17.6093 68.0532 17.6775 68.32 17.6775C69.2259 17.6775 69.958 16.9454 69.958 16.0395V0.304199H69.9642Z" fill="currentColor"></path><path d="M77.3013 0.304199H74.5898V17.6899H77.3013V0.304199Z" fill="currentColor"></path><path d="M93.242 18C85.9576 18 80.7891 14.544 80.7891 9.0031C80.7891 3.46225 85.9824 0 93.242 0C100.502 0 105.726 3.45605 105.726 8.9969C105.726 14.5377 100.619 17.9938 93.242 17.9938M93.242 2.30196C87.8253 2.30196 83.6495 4.66598 83.6495 8.9969C83.6495 13.3278 87.8253 15.6918 93.242 15.6918C98.6588 15.6918 102.866 13.3588 102.866 8.9969C102.866 4.63495 98.665 2.30196 93.242 2.30196Z" fill="currentColor"></path></svg>"""

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
        print("No icon found, using embedded SVG and converting...")
        try:
             # Write embedded SVG to file
             with open("icon.svg", "w") as f:
                 # Set color to red for visibility (currentColor -> #c72c48 is MinIO red)
                 f.write(ICON_SVG_CONTENT.replace("currentColor", "#c72c48"))
             
             # Convert SVG to PNG using rsvg-convert (requires librsvg2-bin)
             if shutil.which("rsvg-convert"):
                 # The SVG is wide (106x18), so we scale it to fit in 256x256 while maintaining aspect ratio
                 # We'll just set width to 256, height will adjust.
                 subprocess.run(["rsvg-convert", "-w", "256", "icon.svg", "-o", "icon.png"], check=True)
                 shutil.copy("icon.png", os.path.join(control_dir, "icon.png"))
                 os.remove("icon.svg")
                 os.remove("icon.png")
             else:
                 print("WARNING: rsvg-convert not found. Using empty icon.")
                 with open(os.path.join(control_dir, "icon.png"), "wb") as f: pass
        except Exception as e:
             print(f"Failed to process icon: {e}. Creating dummy.")
             with open(os.path.join(control_dir, "icon.png"), "wb") as f: pass

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