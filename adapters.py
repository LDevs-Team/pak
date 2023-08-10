import os, platform

def adapter_ps1(filePath: str, needsReboot:bool):
    proc = os.system(f"powershell -ExecutionPolicy Bypass -C {filePath}")
    if needsReboot:
        match platform.system():
            case 'Linux':
                os.system('sleep 10; systemctl reboot -i')
            case 'Darwin':
                print("Reboot is required. Expect a password prompt")
                os.system('sudo shutdown -r -h now')
            case 'Windows':
                os.system('shutdown -r -t 10')
            case _:
                print("Package needs reboot, but auto-reboot is not supported on your OS. Please reboot manually.")
    
    return True if proc == 0 else False
def adapter_batch(filePath: str, needsReboot:bool):
    proc = os.system(f"cmd /c {filePath}")
    if needsReboot:
        match platform.system():
            case 'Linux':
                os.system('sleep 10; systemctl reboot -i')
            case 'Darwin':
                print("Reboot is required. Expect a password prompt")
                os.system('sudo shutdown -r -h now')
            case 'Windows':
                os.system('shutdown -r -t 10')
            case _:
                print("Package needs reboot, but auto-reboot is not supported on your OS. Please reboot manually.")
    return True if proc == 0 else False
