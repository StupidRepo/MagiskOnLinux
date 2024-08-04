import requests, os, re, datetime, subprocess

devices_server = "https://download.lineageos.org/api/v2/devices/%s"
builds_server = "https://download.lineageos.org/api/v2/devices/%s/builds"
file_server = "https://mirrorbits.lineageos.org/%s"

magisk_url = "https://api.github.com/repos/topjohnwu/Magisk/releases/latest"

def clear():
    os.system("clear")

def check_command(command):
    if subprocess.call(['which', command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        raise ProcessLookupError(f"{command} command is not installed. Please install it.")

def confirm(message):
    return input(f"{message} (yes/no): ").lower() == "yes"

def remove_temp():
    if os.path.exists("temp"):
        os.system("rm -r temp")

def download_file(url, name):
    file = requests.get(url)

    if not os.path.exists("temp"):
        os.mkdir("temp")

    with open(f"temp/{name}", "wb") as f:
        f.write(file.content)

def ask_for_device():
    return check_device(input("Please enter the device codename (e.g. 'bramble'): "))

def check_device(device):
    response = requests.get(devices_server % device)

    if response.status_code == 400:
        print("Device not found. Please try again.")
        ask_for_device()
    elif response.status_code != 200:
        raise Exception("Failed to fetch device.")
    
    json = response.json()

    if not confirm(f"Is your device the {json['name']}?"):
        ask_for_device()
    
    return device

def get_latest_build(device):
    print("Fetching latest build for your device...")

    response = requests.get(builds_server % device)

    if response.status_code != 200:
        raise Exception("Failed to fetch builds.")

    return response.json()[0]

def download_boot_img(device):
    latest_build = get_latest_build(device)
    boot_url = file_server % [file["filepath"] for file in latest_build["files"] if file["filename"] == "boot.img"][0]

    date = datetime.datetime.fromtimestamp(latest_build["datetime"]).strftime("%d %B, %Y")

    if not confirm(f"I am about to download the boot.img from the latest LineageOS build available for your device (released {date}). If your device is NOT running the LineageOS build from that date, this boot.img may put you in a bootloop when flashed or cause other issues! Continue?"):
        print("Okay, I'll skip this step and start downloading Magisk. If you want to download the boot.img later, you can run the script again. Just make sure you've updated your device to the latest LineageOS build available for it!")
        return

    print("Downloading boot.img...")

    download_file(boot_url, "boot.img")

def download_magisk():
    json = requests.get(magisk_url).json()
    magisk_download_url = json["assets"][0]["browser_download_url"]

    print("Downloading Magisk...")

    download_file(magisk_download_url, "magisk.zip")

def unzip_magisk():
    check_command("unzip")

    print("Unzipping Magisk...")

    os.system("unzip -qq -o temp/magisk.zip -d temp/magisk")
    os.system("rm temp/magisk.zip")

def move_magisk_files():
    print("Moving Magisk files...")

    os.system("mv temp/magisk/assets/stub.apk temp/stub.apk")

    os.system("mv temp/magisk/assets/boot_patch.sh temp/boot_patch.sh")
    os.system("mv temp/magisk/assets/util_functions.sh temp/util_functions.sh")

    os.system("mv temp/magisk/lib/x86_64/libmagiskboot.so temp/magiskboot")

    os.system("mv temp/magisk/lib/armeabi-v7a/libmagisk32.so temp/magisk32")

    os.system("mv temp/magisk/lib/arm64-v8a/libmagisk64.so temp/magisk64")
    os.system("mv temp/magisk/lib/arm64-v8a/libmagiskinit.so temp/magiskinit")

def fix_scripts():
    print("Fixing scripts...")

    with open("temp/util_functions.sh") as f:
        new = f.read()
        f.close()
    
    new = new.replace("getprop", "adb shell getprop")
    new = re.sub(r'ui_print\(\)\s*{[^}]*}', 'ui_print() {\n  echo $1\n}', new)

    with open("temp/util_functions.sh", "w") as f:
        f.write(new)

    os.system("chmod +x temp/boot_patch.sh")

remove_temp()
clear()

isLineage = confirm("If your device is running LineageOS, I can automatically download a boot.img for you. Are you using LineageOS?")
if isLineage:
    device = ask_for_device()

    clear()

    download_boot_img(device)

clear()

download_magisk()

unzip_magisk()
move_magisk_files()

fix_scripts()

print("\nDone! Now you can run the script in the temp folder with the following command:")
print(f"cd temp && sudo sh boot_patch.sh {'path/to/' if not isLineage else ''}boot.img")