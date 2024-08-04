import requests, os

devices_server = "https://download.lineageos.org/api/v2/devices/%s"
builds_server = "https://download.lineageos.org/api/v2/devices/%s/builds"
file_server = "https://mirrorbits.lineageos.org/%s"

magisk_url = "https://api.github.com/repos/topjohnwu/Magisk/releases/latest"

def remove_temp():
    if os.path.exists("temp"):
        os.system("rm -r temp")

def ask_for_device():
    return check_device(input("Please enter the device codename (e.g. 'bramble'): "))

def check_device(device):
    response = requests.get(devices_server % device)

    if response.status_code == 400:
        raise Exception("Device not found.")
    elif response.status_code != 200:
        raise Exception("Failed to fetch device.")
    
    json = response.json()

    confirmed = input("Is this the device? \"%s\" (yes/no): " % json["name"]).lower()
    if confirmed != "yes":
        ask_for_device()
    
    return device

def get_latest_build(device):
    response = requests.get(builds_server % device)

    if response.status_code != 200:
        raise Exception("Failed to fetch builds.")

    return response.json()[0]

def download_file(url, name):
    file = requests.get(url)

    if not os.path.exists("temp"):
        os.mkdir("temp")

    with open(f"temp/{name}", "wb") as f:
        f.write(file.content)

def download_boot_img(device):
    latest_build = get_latest_build(device)
    boot_url = file_server % [file["filepath"] for file in latest_build["files"] if file["filename"] == "boot.img"][0]

    download_file(boot_url, "boot.img")

def download_magisk():
    json = requests.get(magisk_url).json()
    magisk_download_url = json["assets"][0]["browser_download_url"]

    download_file(magisk_download_url, "magisk.zip")

def check_command(command):
    if os.system(f"which {command}") != 0:
        raise ProcessLookupError(f"{command} command is not installed. Please install it.")

def unzip_magisk():
    check_command("unzip")

    os.system("unzip temp/magisk.zip -d temp/magisk")
    os.system("rm temp/magisk.zip")

def move_magisk_files():
    os.system("mv temp/magisk/assets/stub.apk temp/stub.apk")

    os.system("mv temp/magisk/assets/boot_patch.sh temp/boot_patch.sh")
    os.system("mv temp/magisk/assets/util_functions.sh temp/util_functions.sh")

    os.system("mv temp/magisk/lib/armeabi-v7a/libmagisk32.so temp/magisk32")
    os.system("mv temp/magisk/lib/arm64-v8a/libmagisk64.so temp/magisk64")

    os.system("mv temp/magisk/lib/x86_64/libmagiskboot.so temp/magiskboot")
    os.system("mv temp/magisk/lib/arm64-v8a/libmagiskinit.so temp/magiskinit")

def replace_keywords_in_script():
    boot_patch = open("temp/boot_patch.sh", "r")
    boot_patch_content = boot_patch.read()
    boot_patch.close()

    boot_patch_content = boot_patch_content.replace("getprop", "adb shell getprop")

    boot_patch = open("temp/boot_patch.sh", "w")
    boot_patch.write(boot_patch_content)
    boot_patch.close()

    os.system("chmod +x temp/boot_patch.sh")

    print("Done! Now you can run the script in the temp folder.")

remove_temp()

device = ask_for_device()
download_boot_img(device)
download_magisk()

unzip_magisk()
move_magisk_files()

replace_keywords_in_script()