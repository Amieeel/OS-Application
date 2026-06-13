from PIL import Image

def get_images():
    return {
        "home": Image.open("assets/home.png"),
        "start_button": Image.open("assets/start_button.png"),
        "learn_button": Image.open("assets/learn_button.png"),
        "about_button": Image.open("assets/about_button.png"),
        "select": Image.open("assets/select.png"),
        "back_button": Image.open("assets/back_button.png"),
        "CPU_sched_button": Image.open("assets/CPU_sched_button.png"),
        "cpu_bg": Image.open("assets/cpu.png"),
        "Main_mem_button": Image.open("assets/Main_mem_button.png"),
        "Virt_mem_button": Image.open("assets/Virt_mem_button.png"),
        "Disk_sched_button": Image.open("assets/Disk_sched_button.png"),
    }