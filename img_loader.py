from PIL import Image

def get_images():
    return {
        "home": Image.open("assets/home.png"),
        "start_button": Image.open("assets/start_button.png"),
        "learn_button": Image.open("assets/learn_button.png"),
        "about_button": Image.open("assets/about_button.png"),
        "select": Image.open("assets/select.png"),
        "back_button": Image.open("assets/back_button.png"),

        "round_bb": Image.open("assets/round_back_button.png"),
        # --- CPU SCHEDULING VISUALIZATION ASSETS ---
        "CPU_sched_button": Image.open("assets/CPU_sched_button.png"),
        "cpu_bg": Image.open("assets/cpu.png"),
        "cpu_cont": Image.open("assets/CPU_container.png"),

        # -- MAIN MEMORY VISUALIZATION ASSETS ---
        "Main_mem_button": Image.open("assets/Main_mem_button.png"),

        # -- VIRT MEMORY VISUALIZATION ASSETS ---
        "Virt_mem_button": Image.open("assets/Virt_mem_button.png"),
        
        # -- DISK SCHEDULING VISUALIZATION ASSETS ---
        "Disk_sched_button": Image.open("assets/Disk_sched_button.png"),
        "disk_bg": Image.open("assets/disk.png"),
        "disk_cont": Image.open("assets/DISK_container.png"),
    }
