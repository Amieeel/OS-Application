from PIL import Image
import os

def get_images():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "assets")
    
    return {
        "home": Image.open(os.path.join(assets_dir, "home.png")),
        "start_button": Image.open(os.path.join(assets_dir, "start_button.png")),
        "learn_button": Image.open(os.path.join(assets_dir, "learn_button.png")),
        "about_button": Image.open(os.path.join(assets_dir, "about_button.png")),
        "select": Image.open(os.path.join(assets_dir, "select.png")),
        "back_button": Image.open(os.path.join(assets_dir, "back_button.png")),

        "round_bb": Image.open(os.path.join(assets_dir, "round_back_button.png")),
        # --- CPU SCHEDULING VISUALIZATION ASSETS ---
        "CPU_sched_button": Image.open(os.path.join(assets_dir, "CPU_sched_button.png")),
        "cpu_bg": Image.open(os.path.join(assets_dir, "cpu.png")),
        "cpu_cont": Image.open(os.path.join(assets_dir, "CPU_container.png")),

        # -- MAIN MEMORY VISUALIZATION ASSETS ---
        "Main_mem_button": Image.open(os.path.join(assets_dir, "Main_mem_button.png")),
        "mainmem": Image.open(os.path.join(assets_dir, "mainmem.png")),
        "memory_cont": Image.open(os.path.join(assets_dir, "MemoryManage_Container.png")),

        # -- VIRT MEMORY VISUALIZATION ASSETS ---
        "Virt_mem_button": Image.open(os.path.join(assets_dir, "Virt_mem_button.png")),
        "virtual_bg": Image.open(os.path.join(assets_dir, "virtualmem.png")),
        "virt_cont": Image.open(os.path.join(assets_dir, "VirtualMem_Container.png")),
        
        # -- DISK SCHEDULING VISUALIZATION ASSETS ---
        "Disk_sched_button": Image.open(os.path.join(assets_dir, "Disk_sched_button.png")),
        "disk_bg": Image.open(os.path.join(assets_dir, "disk.png")),
        "disk_cont": Image.open(os.path.join(assets_dir, "DISK_container.png")),
    }
