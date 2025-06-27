import os
import re
import sys
import ssl
import platform
import subprocess
import ctypes
import psutil
import webbrowser
import win32com.client
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# Konstanta Aplikasi
version = "1.0.0.0"
developer = "PT Ananda Technology Solution"
release_date = "27 Juni 2025"
tool_name = "Pynek (Python Koneksi)"
base_dir = r"C:\Folder Download Sementara\Pynek(Python Koneksi)"

# Fungsi Hak Akses Administrator
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

# Utilitas Sistem
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def run_background(command):
    subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_service(service_exe, display_name):
    subprocess.run(f"taskkill /f /im {service_exe}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"{Fore.YELLOW}{display_name} stopped.{Style.RESET_ALL}")

# Fungsi Service Apache dan MySQL
def start_apache():
    apache_path = os.path.join(base_dir, r"bin\httpd\bin\httpd.exe")
    apache_dir = os.path.join(base_dir, r"bin\httpd")
    cmd = f'"{apache_path}" -d "{apache_dir}"'
    run_background(cmd)
    print(f"{Fore.GREEN}Apache started in background.{Style.RESET_ALL}")

def start_mysql():
    mysql_cmd = (
        f'"{os.path.join(base_dir, "bin", "mysql", "bin", "mysqld.exe")}" '
        f'--datadir="{os.path.join(base_dir, "etc", "config", "mysql")}" '
        f'--log-error="{os.path.join(base_dir, "logs", "mysql", "mysql_error.log")}" '
        f'--log-bin="{os.path.join(base_dir, "logs", "mysql", "binlog")}"'
    )
    run_background(mysql_cmd)
    print(f"{Fore.GREEN}MySQL started in background.{Style.RESET_ALL}")

def stop_apache():
    stop_service("httpd.exe", "Apache")

def stop_mysql():
    stop_service("mysqld.exe", "MySQL")

def check_status():
    apache = os.system("tasklist | findstr httpd.exe > nul") == 0
    mysql = os.system("tasklist | findstr mysqld.exe > nul") == 0
    return apache, mysql

def initialize_mysql():
    print(f"{Fore.YELLOW}Initializing MySQL database...{Style.RESET_ALL}")
    data_dir = os.path.join(base_dir, r"etc\config\mysql")
    if os.listdir(data_dir):
        print(f"{Fore.RED}Warning: MySQL data directory is not empty.{Style.RESET_ALL}")
        if input("Delete and reinitialize? (y/n): ").lower() != 'y':
            print("Cancelled.")
            return
        for item in os.listdir(data_dir):
            path = os.path.join(data_dir, item)
            if os.path.isfile(path):
                os.remove(path)
            else:
                subprocess.run(f'rmdir /s /q "{path}"', shell=True)

    mysql_install = os.path.join(base_dir, r"bin\mysql\bin\mysql_install_db.exe")
    result = subprocess.run(
        f'"{mysql_install}" --datadir="{data_dir}"',
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"{Fore.GREEN}MySQL initialized successfully.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Error initializing MySQL database:{Style.RESET_ALL}\n{result.stderr}")

# Fungsi Versi
def extract_version(text):
    match = re.search(r"\d+(?:\.\d+)+", text)
    return match.group() if match else "Not found"

def get_php_version():
    php_exe = os.path.join(base_dir, r"bin\php\php.exe")
    res = subprocess.run(f'"{php_exe}" -v', shell=True, capture_output=True, text=True)
    return extract_version(res.stdout) if res.returncode == 0 else "PHP not found"

def get_mysql_version():
    mysql_exe = os.path.join(base_dir, r"bin\mysql\bin\mysql.exe")
    res = subprocess.run(f'"{mysql_exe}" -V', shell=True, capture_output=True, text=True)
    return extract_version(res.stdout) if res.returncode == 0 else "MySQL not found"

def get_apache_version():
    apache_exe = os.path.join(base_dir, r"bin\httpd\bin\httpd.exe")
    res = subprocess.run(f'"{apache_exe}" -v', shell=True, capture_output=True, text=True)
    return extract_version(res.stdout) if res.returncode == 0 else "Apache not found"

def get_windows_edition():
    wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    os_info = wmi.ConnectServer(".", "root\\cimv2").ExecQuery("Select * from Win32_OperatingSystem")[0]
    return re.sub(r"Microsoft\s+", "", os_info.Caption).strip()

def get_system_info():
    os_name = f"{get_windows_edition()} ({platform.release()})"
    arch = platform.architecture()[0]
    ram = psutil.virtual_memory()
    ram_text = f"{ram.used / (1024 ** 3):.2f} GB / {ram.total / (1024 ** 3):.2f} GB"
    return os_name, arch, ram_text
def enable_ssl_apache():
    httpd_conf = os.path.join(base_dir, r"bin\httpd\conf\httpd.conf")
    ssl_conf = os.path.join(base_dir, r"bin\httpd\conf\extra\httpd-ssl.conf")

    if not os.path.exists(httpd_conf) or not os.path.exists(ssl_conf):
        print(Fore.RED + "File konfigurasi Apache tidak ditemukan." + Style.RESET_ALL)
        return

    # Aktifkan modul SSL dan include httpd-ssl.conf
    with open(httpd_conf, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    ssl_module_found = False
    ssl_include_found = False

    for line in lines:
        if "LoadModule ssl_module modules/mod_ssl.so" in line:
            ssl_module_found = True
            updated_lines.append("LoadModule ssl_module modules/mod_ssl.so\n")
        elif "Include conf/extra/httpd-ssl.conf" in line:
            ssl_include_found = True
            updated_lines.append("Include conf/extra/httpd-ssl.conf\n")
        else:
            updated_lines.append(line)

    if not ssl_module_found:
        updated_lines.append("LoadModule ssl_module modules/mod_ssl.so\n")
    if not ssl_include_found:
        updated_lines.append("Include conf/extra/httpd-ssl.conf\n")

    with open(httpd_conf, 'w') as file:
        file.writelines(updated_lines)

    # Pastikan httpd-ssl.conf aktif di port 443
    with open(ssl_conf, 'r') as file:
        ssl_lines = file.readlines()

    ssl_lines_updated = []
    for line in ssl_lines:
        if line.strip().startswith("Listen"):
            ssl_lines_updated.append("Listen 443\n")
        else:
            ssl_lines_updated.append(line)

    with open(ssl_conf, 'w') as file:
        file.writelines(ssl_lines_updated)

    print(Fore.GREEN + "SSL Apache telah diaktifkan (port 443)." + Style.RESET_ALL)

def banner():
    clear_screen()
    print("=" * 60)
    print(f"Nama Tools     : {tool_name}")
    print(f"Version        : {version}")
    print(f"Developer      : {developer}")
    print(f"Tanggal Rilis  : {release_date}")
    print(f"Python         : {sys.version.split()[0]}")
    print("-" * 60)
    print(f"MySQL Version  : {get_mysql_version()}")
    print(f"Apache Version : {get_apache_version()}")
    print(f"PHP Version    : {get_php_version()}")
    os_name, arch, ram = get_system_info()
    print(f"OS             : {os_name}")
    print(f"Architecture   : {arch}")
    print(f"RAM Used/Total : {ram}")
    print("=" * 60)

def main_menu():
    if os.name == "nt" and not is_admin():
        print(Fore.YELLOW + "⚠ Jalankan ulang sebagai Administrator..." + Style.RESET_ALL)
        run_as_admin()
        sys.exit()

    while True:
        banner()
        print("MENU:")
        print("1. Start MySQL")
        print("2. Start Apache")
        print("3. Stop MySQL")
        print("4. Stop Apache")
        print("5. Initialize MySQL (hapus data)")
        print("6. Buka phpMyAdmin")
        print("7. Jalankan Flask Web (path project)")
        print("8. Aktifkan SSL Apache")
        print("0. Keluar")

        choice = input("\nPilih aksi: ").strip()

        if choice == "1":
            start_mysql()
        elif choice == "2":
            start_apache()
        elif choice == "3":
            stop_mysql()
        elif choice == "4":
            stop_apache()
        elif choice == "5":
            initialize_mysql()
        elif choice == "6":
            webbrowser.open("http://localhost/phpmyadmin")
        elif choice == "7":
            folder = input("Path folder Flask: ").strip('"')
            if not os.path.isdir(folder):
                print(Fore.RED + "Folder tidak ditemukan." + Style.RESET_ALL)
            else:
                os.chdir(folder)
                os.environ["FLASK_APP"] = "app.py"
                subprocess.run(["flask", "run"], shell=True)
        elif choice == "8":
            enable_ssl_apache()
        elif choice == "0":
            print(f"Terima kasih telah menggunakan {tool_name}.")
            break
        else:
            print(Fore.RED + "Pilihan tidak valid." + Style.RESET_ALL)

        input("\nTekan Enter untuk kembali ke menu...")

if __name__ == "__main__":
    main_menu()