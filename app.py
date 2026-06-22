import tkinter as tk
from PIL import Image, ImageTk
from img_loader import get_images
from cpuschedulingv2 import scheduling_algorithm
import disk_scheduling
import importlib.util
import os
from Memory_Management import Process as MemProcess, MemoryManager as MemMemoryManager
from process_manager import ProcessTableManager


def load_virtual_memory_module():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.join(script_dir, "Virtual Memory.py")
    spec = importlib.util.spec_from_file_location("virtual_memory", module_path)
    vm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm)
    return vm


class App(tk.Tk):

    def __init__(self):
        super().__init__()

        # FIXED WINDOW
        self.title("Go Rhythm")
        self.geometry("1420x780")
        self.resizable(False, False)

        # assets
        self.imgs = get_images()

        # canvas
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # background
        self.bg_id = None
        self.bg_tk = None
        self.bg_name = "home"

        # state
        self.updating_ui = False
        self.buttons = {}

        # scheduler + result cache
        self.scheduler = None
        self.result = None

        # FOR CPU SCHEDULING
        self.selected_algo = tk.StringVar(value="FCFS")
        self.cpu_table_manager = None

        # FOR DISK SCHEDULING
        self.disk_size_var = tk.StringVar(value="200")
        self.disk_head_var = tk.StringVar(value="50")
        self.disk_requests_var = tk.StringVar(value="40 10 100 80")
        self.selected_disk_algo = tk.StringVar(value="FCFS")
        self.disk_total_var = tk.StringVar(value="Total Movement:\n")
        self.disk_sequence_var = tk.StringVar(value="Sequence:\n")
        self.disk_graph_canvas = None

        # FOR MEMORY MANAGEMENT
        self.memory_total_mem_var = tk.StringVar(value="256")
        self.memory_os_size_var = tk.StringVar(value="40")
        self.memory_quantum_var = tk.StringVar(value="5")
        self.memory_policy_var = tk.StringVar(value="First Fit")
        self.memory_pid_var = tk.StringVar(value="J1")
        self.memory_arr_var = tk.StringVar(value="0")
        self.memory_burst_var = tk.StringVar(value="10")
        self.memory_mem_req_var = tk.StringVar(value="60")
        self.memory_processes = []
        self.memory_manager = None
        self.memory_time = 0
        self.memory_completed_count = 0
        self.memory_quantum_tick = 0
        self.memory_input_queue = []
        self.memory_ready_queue = []
        self.memory_metrics_var = tk.StringVar(value="Utilization: 0% | Ext: 0K | Int: 0K")
        self.memory_log_var = tk.StringVar(value="Logs:\n")
        self.memory_process_list_var = tk.StringVar(value="Processes:\n")
        self.memory_map_canvas = None
        self.virtual_pages_var = tk.StringVar(value="7,0,1,2,0,3")
        self.virtual_capacity_var = tk.StringVar(value="3")
        self.virtual_algo_var = tk.StringVar(value="fifo")
        self.virtual_frames_canvas = None
        self.virtual_faults_var = tk.StringVar(value="Faults: 0")
        self.virtual_sequence_var = tk.StringVar(value="Frames:\n")
        self.virtual_log_var = tk.StringVar(value="Logs:\n")
        self.virtual_module = load_virtual_memory_module()

        self.set_background("home")
        self.create_main_menu()
        self.render_buttons()

    # ---------------- BACKGROUND ----------------
    def set_background(self, name):
        self.bg_name = name
        self.render_background()

    def render_background(self):
        w, h = 1420, 780

        img = self.imgs[self.bg_name].resize((w, h), Image.Resampling.LANCZOS)
        self.bg_tk = ImageTk.PhotoImage(img)

        if self.bg_id is None:
            self.bg_id = self.canvas.create_image(
                0, 0, anchor="nw", image=self.bg_tk
            )
        else:
            self.canvas.itemconfig(self.bg_id, image=self.bg_tk)

    # ---------------- SCREEN SWITCH ----------------
    def switch_screen(self, bg, builder):
        self.updating_ui = True
        self.clear_buttons()
        self.canvas.delete("ui")

        self.set_background(bg)
        builder()

        self.updating_ui = False
        self.render_buttons()
        self.after(1, self.render_buttons)

    # ---------------- BUTTON SYSTEM ----------------
    def create_button(self, name, img_name, x, y, command, scale=1.0):
        btn_id = self.canvas.create_image(0, 0, anchor="nw", tags="ui")

        self.canvas.tag_bind(btn_id, "<Button-1>", lambda e: command())

        self.buttons[name] = {
            "img": self.imgs[img_name],
            "id": btn_id,
            "pos": (x, y),
            "tk": None,
            "scale": scale
        }

        self.canvas.tag_raise(btn_id)

    def clear_buttons(self):
        for b in self.buttons.values():
            self.canvas.delete(b["id"])
        self.buttons.clear()

    def render_buttons(self):
        if self.updating_ui:
            return

        w, h = 1420, 780

        for b in self.buttons.values():
            img = b["img"]
            scale = b.get("scale", 1.0)

            x = int(b["pos"][0] * w)
            y = int(b["pos"][1] * h)

            new_w = int(img.width * scale)
            new_h = int(img.height * scale)

            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(resized)

            b["tk"] = tk_img

            self.canvas.itemconfig(b["id"], image=tk_img)
            self.canvas.coords(b["id"], x, y)
            self.canvas.tag_raise(b["id"])

    # ---------------- NAV ----------------
    def on_start(self):
        self.switch_screen("select", self.create_select_menu)

    def on_back(self):
        self.switch_screen("home", self.create_main_menu)

    def on_CPU(self):
        self.switch_screen("cpu_bg", self.create_cpu_view)

    def on_disk(self):
        self.switch_screen("disk_bg", self.create_disk_view)

    def on_memory(self):
        self.switch_screen("mainmem", self.create_memory_view)

    def on_virtual(self):
        self.switch_screen("virtual_bg", self.create_virtual_view)

    # ---------------- MENUS ----------------
    def create_main_menu(self): 
        self.create_button("start", "start_button", 0.4, 0.45, self.on_start, scale=0.65) 
        self.create_button("learn", "learn_button", 0.41, 0.59, lambda: None, scale=0.6) 
        self.create_button("about", "about_button", 0.41, 0.69, lambda: None, scale=0.6) 
        
    def create_select_menu(self): 
        self.create_button("back", "back_button", 0.03, 0.11, self.on_back, scale=0.6) 
        self.create_button("CPU", "CPU_sched_button", 0.05, 0.25, self.on_CPU, scale=0.8)
        self.create_button("DISK", "Disk_sched_button", 0.27, 0.25, self.on_disk, scale=0.8)
        self.create_button("MEM", "Main_mem_button", 0.49, 0.25, self.on_memory, scale=0.8)
        self.create_button("VIRT", "Virt_mem_button", 0.71, 0.25, self.on_virtual, scale=0.8)

    # ---------------- CPU VIEW ----------------
    def create_cpu_view(self):
        w, h = 1420, 780

        self.canvas.delete("ui")

        # CPU container
        cont_img = self.imgs["cpu_cont"]
        cont_w = int(w * 0.9)
        cont_h = int(h * 0.75)

        resized = cont_img.resize((cont_w, cont_h), Image.Resampling.LANCZOS)
        self.cpu_cont_tk = ImageTk.PhotoImage(resized)

        container_x = w // 2
        container_y = h // 2 + 30

        self.canvas.create_image(
            container_x,
            container_y,
            image=self.cpu_cont_tk,
            tags="ui"
        )

        self.create_button("back", "back_button", 0.03, 0.11, self.on_back, scale=0.6)

        # dropdown 
        algo_menu = tk.OptionMenu(
            self,
            self.selected_algo,
            "FCFS",
            "SJF",
            "Priority"
        )

        self.canvas.create_window(
            container_x - 440,
            container_y + 220,
            window=algo_menu
        )
        algo_menu.config( font=("Arial", 26))

        # table manager
        if self.cpu_table_manager is None:
            self.cpu_table_manager = ProcessTableManager(
                self.canvas,
                self,
                base_x=130,
                base_y=190,
                col_x=[40, 110, 200]
            )

        if len(self.cpu_table_manager.rows) == 0:
            self.cpu_table_manager.add_row()

        # start button
        self.create_button("run_algo", "start_button", 0.15, 0.6, self.run_scheduler, scale=0.3)

    # ---------------- DISK VIEW ----------------
    def create_disk_view(self):
        w, h = 1420, 780

        self.canvas.delete("ui")

        cont_img = self.imgs["disk_cont"]
        cont_w = int(w * 0.9)
        cont_h = int(h * 0.75)

        resized = cont_img.resize((cont_w, cont_h), Image.Resampling.LANCZOS)
        self.disk_cont_tk = ImageTk.PhotoImage(resized)

        container_x = w // 2
        container_y = h // 2 + 30

        self.canvas.create_image(
            container_x,
            container_y,
            image=self.disk_cont_tk,
            tags="ui"
        )

        entry_font = ("Arial", 12)

        disk_size_entry = tk.Entry(self, textvariable=self.disk_size_var, width=9, font=entry_font)
        self.canvas.create_window(container_x - 480, container_y - 220, window=disk_size_entry, tags="ui")

        head_entry = tk.Entry(self, textvariable=self.disk_head_var, width=9, font=entry_font)
        self.canvas.create_window(container_x - 160, container_y - 220, window=head_entry, tags="ui")

        requests_entry = tk.Entry(self, textvariable=self.disk_requests_var, width=24, font=entry_font)
        self.canvas.create_window(container_x + 170, container_y - 220, window=requests_entry, tags="ui")

        algo_menu = tk.OptionMenu(
            self,
            self.selected_disk_algo,
            "FCFS",
            "SSTF",
            "SCAN",
            "C-SCAN",
            "LOOK",
            "C-LOOK"
        )
        self.canvas.create_window(container_x + 480, container_y - 220, window=algo_menu, tags="ui")
        algo_menu.config(font=("Arial", 14), width=10)

        total_frame = tk.Label(
            self,
            textvariable=self.disk_total_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 14),
            justify="left",
            width=20,
            height=6,
            bd=0
        )
        self.canvas.create_window(container_x - 300, container_y + 10, window=total_frame, tags="ui")

        sequence_frame = tk.Label(
            self,
            textvariable=self.disk_sequence_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 11),
            justify="left",
            width=24,
            height=4,
            bd=0
        )
        self.canvas.create_window(container_x - 300, container_y + 150, window=sequence_frame, tags="ui")

        self.disk_graph_canvas = tk.Canvas(
            self,
            width=560,
            height=340,
            bg="#193c54",
            bd=0,
            highlightthickness=0
        )
        self.canvas.create_window(container_x + 240, container_y + 30, window=self.disk_graph_canvas, tags="ui")

        self.create_button("back", "back_button", 0.03, 0.11, self.on_back, scale=0.6)

        # run button
        self.create_button("disk_run", "start_button", 0.15, 0.6, self.run_disk_scheduler, scale=0.3)

    # ---------------- MEMORY VIEW ----------------
    def create_memory_view(self):
        w, h = 1420, 780

        self.canvas.delete("ui")

        cont_img = self.imgs["memory_cont"]
        cont_w = int(w * 0.9)
        cont_h = int(h * 0.75)

        resized = cont_img.resize((cont_w, cont_h), Image.Resampling.LANCZOS)
        self.memory_cont_tk = ImageTk.PhotoImage(resized)

        container_x = w // 2
        container_y = h // 2 + 30

        self.canvas.create_image(
            container_x,
            container_y,
            image=self.memory_cont_tk,
            tags="ui"
        )

        self.create_button("back", "back_button", 0.03, 0.11, self.on_back, scale=0.6)

        entry_font = ("Arial", 12)

        # System inputs
        total_label = tk.Label(self, text="Total Mem", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x - 500, container_y - 240, window=total_label, tags="ui")
        total_entry = tk.Entry(self, textvariable=self.memory_total_mem_var, width=6, font=entry_font)
        self.canvas.create_window(container_x - 500, container_y - 210, window=total_entry, tags="ui")

        os_label = tk.Label(self, text="OS Size", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x - 360, container_y - 240, window=os_label, tags="ui")
        os_entry = tk.Entry(self, textvariable=self.memory_os_size_var, width=6, font=entry_font)
        self.canvas.create_window(container_x - 360, container_y - 210, window=os_entry, tags="ui")

        quantum_label = tk.Label(self, text="Quantum", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x - 220, container_y - 240, window=quantum_label, tags="ui")
        quantum_entry = tk.Entry(self, textvariable=self.memory_quantum_var, width=6, font=entry_font)
        self.canvas.create_window(container_x - 220, container_y - 210, window=quantum_entry, tags="ui")

        policy_label = tk.Label(self, text="Policy", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x - 80, container_y - 240, window=policy_label, tags="ui")
        policy_menu = tk.OptionMenu(
            self,
            self.memory_policy_var,
            "First Fit",
            "Best Fit",
            "Worst Fit",
            "Next Fit"
        )
        self.canvas.create_window(container_x - 80, container_y - 210, window=policy_menu, tags="ui")
        policy_menu.config(font=("Arial", 12), width=10)

        # Process inputs
        pid_label = tk.Label(self, text="PID", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x + 170, container_y - 240, window=pid_label, tags="ui")
        pid_entry = tk.Entry(self, textvariable=self.memory_pid_var, width=6, font=entry_font)
        self.canvas.create_window(container_x + 170, container_y - 210, window=pid_entry, tags="ui")

        arr_label = tk.Label(self, text="Arr", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x + 260, container_y - 240, window=arr_label, tags="ui")
        arr_entry = tk.Entry(self, textvariable=self.memory_arr_var, width=6, font=entry_font)
        self.canvas.create_window(container_x + 260, container_y - 210, window=arr_entry, tags="ui")

        burst_label = tk.Label(self, text="Burst", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x + 350, container_y - 240, window=burst_label, tags="ui")
        burst_entry = tk.Entry(self, textvariable=self.memory_burst_var, width=6, font=entry_font)
        self.canvas.create_window(container_x + 350, container_y - 210, window=burst_entry, tags="ui")

        mem_label = tk.Label(self, text="Mem", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x + 440, container_y - 240, window=mem_label, tags="ui")
        mem_entry = tk.Entry(self, textvariable=self.memory_mem_req_var, width=6, font=entry_font)
        self.canvas.create_window(container_x + 440, container_y - 210, window=mem_entry, tags="ui")

        add_button = tk.Button(self, text="Add", command=self.memory_add_process, font=("Arial", 10), bg="#4caf50", fg="white")
        self.canvas.create_window(container_x + 540, container_y - 210, window=add_button, tags="ui")

        # Process list and metrics
        process_frame = tk.Label(
            self,
            textvariable=self.memory_process_list_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 10),
            justify="left",
            width=28,
            height=7,
            bd=0
        )
        self.canvas.create_window(container_x - 300, container_y + 10, window=process_frame, tags="ui")

        metrics_label = tk.Label(
            self,
            textvariable=self.memory_metrics_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 12),
            justify="left",
            width=28,
            height=3,
            bd=0
        )
        self.canvas.create_window(container_x - 300, container_y + 130, window=metrics_label, tags="ui")

        log_label = tk.Label(
            self,
            textvariable=self.memory_log_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 10),
            justify="left",
            width=28,
            height=6,
            bd=0
        )
        self.canvas.create_window(container_x - 300, container_y + 240, window=log_label, tags="ui")

        self.memory_map_canvas = tk.Canvas(
            self,
            width=560,
            height=340,
            bg="#193c54",
            bd=0,
            highlightthickness=0
        )
        self.canvas.create_window(container_x + 240, container_y + 30, window=self.memory_map_canvas, tags="ui")

        # run button
        self.create_button("mem_run", "start_button", 0.15, 0.6, self.run_memory_scheduler, scale=0.3)

    def create_virtual_view(self):
        w, h = 1420, 780

        self.canvas.delete("ui")

        cont_img = self.imgs["virt_cont"]
        cont_w = int(w * 0.9)
        cont_h = int(h * 0.75)

        resized = cont_img.resize((cont_w, cont_h), Image.Resampling.LANCZOS)
        self.virtual_cont_tk = ImageTk.PhotoImage(resized)

        container_x = w // 2
        container_y = h // 2 + 30

        self.canvas.create_image(
            container_x,
            container_y,
            image=self.virtual_cont_tk,
            tags="ui"
        )

        self.create_button("back", "back_button", 0.03, 0.11, self.on_back, scale=0.6)

        entry_font = ("Arial", 12)

        pages_label = tk.Label(self, text="Pages", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x - 500, container_y - 240, window=pages_label, tags="ui")
        pages_entry = tk.Entry(self, textvariable=self.virtual_pages_var, width=24, font=entry_font)
        self.canvas.create_window(container_x - 500, container_y - 210, window=pages_entry, tags="ui")

        capacity_label = tk.Label(self, text="Frames", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x - 240, container_y - 240, window=capacity_label, tags="ui")
        capacity_entry = tk.Entry(self, textvariable=self.virtual_capacity_var, width=6, font=entry_font)
        self.canvas.create_window(container_x - 240, container_y - 210, window=capacity_entry, tags="ui")

        algo_label = tk.Label(self, text="Algorithm", font=("Arial", 10), bg="#193c54", fg="white")
        self.canvas.create_window(container_x + 40, container_y - 240, window=algo_label, tags="ui")
        algo_menu = tk.OptionMenu(
            self,
            self.virtual_algo_var,
            "fifo",
            "lru",
            "optimal",
            "lfu"
        )
        self.canvas.create_window(container_x + 40, container_y - 210, window=algo_menu, tags="ui")
        algo_menu.config(font=("Arial", 12), width=10)

        self.virtual_frames_canvas = tk.Canvas(
            self,
            width=560,
            height=340,
            bg="#193c54",
            bd=0,
            highlightthickness=0
        )
        self.canvas.create_window(container_x + 240, container_y + 30, window=self.virtual_frames_canvas, tags="ui")

        frames_label = tk.Label(
            self,
            textvariable=self.virtual_sequence_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 11),
            justify="left",
            width=28,
            height=8,
            bd=0
        )
        self.canvas.create_window(container_x - 300, container_y + 20, window=frames_label, tags="ui")

        faults_label = tk.Label(
            self,
            textvariable=self.virtual_faults_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 14),
            justify="left",
            width=18,
            height=2,
            bd=0
        )
        self.canvas.create_window(container_x - 300, container_y + 170, window=faults_label, tags="ui")

        log_label = tk.Label(
            self,
            textvariable=self.virtual_log_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 10),
            justify="left",
            width=28,
            height=6,
            bd=0
        )
        self.canvas.create_window(container_x - 300, container_y + 260, window=log_label, tags="ui")

        self.create_button("virt_run", "start_button", 0.15, 0.6, self.run_virtual_scheduler, scale=0.3)

    def memory_add_process(self):
        try:
            pid = self.memory_pid_var.get().strip()
            arr = int(self.memory_arr_var.get())
            burst = int(self.memory_burst_var.get())
            mem_req = int(self.memory_mem_req_var.get())
        except ValueError:
            self.memory_log_var.set("Logs:\nInvalid process values")
            return

        process = MemProcess(pid, arr, burst, mem_req)
        self.memory_processes.append(process)
        self.memory_pid_var.set(f"J{len(self.memory_processes)+1}")
        self.update_memory_process_list()
        self.memory_log_var.set("Logs:\nProcess added")

    def update_memory_process_list(self):
        lines = ["Processes:"]
        for p in self.memory_processes:
            lines.append(f"{p.pid}: A{p.arrival_time}, B{p.burst_time}, M{p.mem_req}")
        self.memory_process_list_var.set("\n".join(lines))

    def run_virtual_scheduler(self):
        try:
            pages = [int(x.strip()) for x in self.virtual_pages_var.get().split(",") if x.strip() != ""]
            capacity = int(self.virtual_capacity_var.get())
            algo = self.virtual_algo_var.get().lower()
        except ValueError:
            self.virtual_log_var.set("Logs:\nInvalid page or capacity values")
            return

        if capacity <= 0 or not pages:
            self.virtual_log_var.set("Logs:\nEnter valid frames and page list")
            return

        manager = self.virtual_module.PageReplacementManager(capacity, algo)
        faults = 0
        sequence_lines = []
        current_frames = []

        for i, page in enumerate(pages):
            if algo == "optimal":
                future_refs = pages[i+1:]
                frames, is_fault = manager.step(page, future_refs)
            else:
                frames, is_fault = manager.step(page)

            current_frames = frames
            if is_fault:
                faults += 1

            sequence_lines.append(f"P{page}: {frames} | Fault: {'Y' if is_fault else 'N'}")

        self.virtual_sequence_var.set("Frames:\n" + "\n".join(sequence_lines[-8:]))
        self.virtual_faults_var.set(f"Faults: {faults}")
        self.virtual_log_var.set("Logs:\nSimulation complete")
        self.draw_virtual_frames(current_frames)

    def draw_virtual_frames(self, frames):
        if self.virtual_frames_canvas is None:
            return

        self.virtual_frames_canvas.delete("all")
        width = int(self.virtual_frames_canvas["width"])
        height = int(self.virtual_frames_canvas["height"])
        padding = 20
        frame_count = max(1, len(frames))
        box_width = (width - padding * 2) / frame_count
        box_height = height - padding * 2

        for idx, page in enumerate(frames):
            x1 = padding + idx * box_width
            y1 = padding
            x2 = x1 + box_width - 10
            y2 = y1 + box_height
            self.virtual_frames_canvas.create_rectangle(x1, y1, x2, y2, fill="#4caf50", outline="white", width=2)
            self.virtual_frames_canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=str(page),
                fill="white",
                font=("Arial", 16, "bold")
            )

    def run_memory_scheduler(self):
        if not self.memory_processes:
            self.memory_log_var.set("Logs:\nAdd at least one process")
            return

        try:
            total_mem = int(self.memory_total_mem_var.get())
            os_size = int(self.memory_os_size_var.get())
            quantum = int(self.memory_quantum_var.get())
        except ValueError:
            self.memory_log_var.set("Logs:\nInvalid memory settings")
            return

        self.memory_manager = MemMemoryManager(total_mem, os_size)
        self.memory_time = 0
        self.memory_completed_count = 0
        self.memory_quantum_tick = 0
        self.memory_input_queue = []
        self.memory_ready_queue = []
        self.memory_log_var.set("Logs:\nSimulation started")

        for p in self.memory_processes:
            p.remaining_burst = p.burst_time
            p.in_memory = False
            p.start_time = -1
            p.end_time = 0

        strategy = self.memory_policy_var.get()

        while self.memory_completed_count < len(self.memory_processes):
            for p in self.memory_processes:
                if p.arrival_time == self.memory_time and not p.in_memory and p.remaining_burst > 0:
                    self.memory_input_queue.append(p)
                    self.memory_log_var.set(self.memory_log_var.get() + f"\n[T={self.memory_time}] {p.pid} arrived")

            loaded = True
            while loaded and self.memory_input_queue:
                loaded = False
                for p in list(self.memory_input_queue):
                    if self.memory_manager.allocate(p, strategy):
                        self.memory_input_queue.remove(p)
                        self.memory_ready_queue.append(p)
                        self.memory_log_var.set(self.memory_log_var.get() + f"\n[T={self.memory_time}] {p.pid} loaded")
                        loaded = True
                        break

            if self.memory_ready_queue:
                curr = self.memory_ready_queue[0]
                if curr.start_time == -1:
                    curr.start_time = self.memory_time
                curr.remaining_burst -= 1
                self.memory_quantum_tick += 1

                if curr.remaining_burst == 0:
                    curr.end_time = self.memory_time + 1
                    curr.waiting_time = curr.end_time - curr.arrival_time - curr.burst_time
                    curr.turnaround_time = curr.end_time - curr.arrival_time
                    self.memory_completed_count += 1
                    self.memory_manager.deallocate(curr)
                    self.memory_ready_queue.pop(0)
                    self.memory_quantum_tick = 0
                    self.memory_log_var.set(self.memory_log_var.get() + f"\n[T={self.memory_time+1}] {curr.pid} finished")
                elif self.memory_quantum_tick == quantum:
                    rotated = self.memory_ready_queue.pop(0)
                    self.memory_ready_queue.append(rotated)
                    self.memory_quantum_tick = 0
                    self.memory_log_var.set(self.memory_log_var.get() + f"\n[T={self.memory_time+1}] Quantum expired for {rotated.pid}")

            self.memory_time += 1

        self.update_memory_metrics()
        self.draw_memory_map()
        self.memory_log_var.set(self.memory_log_var.get() + "\nSimulation complete")

    def update_memory_metrics(self):
        util, ext_frag, int_frag = self.memory_manager.get_metrics(self.memory_input_queue)
        self.memory_metrics_var.set(f"Utilization: {util:.1f}% | Ext: {ext_frag}K | Int: {int_frag}K")

    def draw_memory_map(self):
        if self.memory_map_canvas is None or self.memory_manager is None:
            return

        self.memory_map_canvas.delete("all")
        tot = self.memory_manager.total_memory
        width = int(self.memory_map_canvas["width"])
        height = int(self.memory_map_canvas["height"])
        padding = 20

        y_scale = (height - padding * 2) / tot
        y_offset = padding

        for block in self.memory_manager.blocks:
            block_height = max(10, block[1] * y_scale)
            color = "#f0f0f0" if block[2] else "#88ccff"
            self.memory_map_canvas.create_rectangle(padding, y_offset, width - padding, y_offset + block_height, fill=color, outline="white")
            label = f"Free {block[1]}K" if block[2] else f"{block[3]} {block[1]}K"
            self.memory_map_canvas.create_text(width // 2, y_offset + block_height / 2, text=label, fill="black", font=("Arial", 9))
            y_offset += block_height
        self.disk_graph_canvas.delete("all")

        try:
            disk_size = int(self.disk_size_var.get())
            head = int(self.disk_head_var.get())
            requests = [int(x) for x in self.disk_requests_var.get().split() if x.strip() != ""]

            if disk_size <= 0:
                raise ValueError
            if head < 0 or head >= disk_size:
                raise ValueError
            if any(r < 0 or r >= disk_size for r in requests):
                raise ValueError

        except ValueError:
            self.disk_total_var.set("Invalid input.\nUse numbers only.")
            self.disk_sequence_var.set("Sequence:\n")
            return

        algo = self.selected_disk_algo.get()
        if algo == "FCFS":
            sequence, total = disk_scheduling.fcfs(requests, head)
        elif algo == "SSTF":
            sequence, total = disk_scheduling.sstf(requests, head)
        elif algo == "SCAN":
            sequence, total = disk_scheduling.scan(requests, head, disk_size)
        elif algo == "C-SCAN":
            sequence, total = disk_scheduling.cscan(requests, head, disk_size)
        elif algo == "LOOK":
            sequence, total = disk_scheduling.look(requests, head)
        elif algo == "C-LOOK":
            sequence, total = disk_scheduling.clook(requests, head)
        else:
            return

        self.disk_total_var.set(f"Total Movement:\n{total}")
        self.disk_sequence_var.set("Sequence:\n" + " -> ".join(map(str, sequence)))
        self.draw_disk_graph(sequence, disk_size)

    def run_disk_scheduler(self):
        self.canvas.delete("gantt")

        try:
            disk_size = int(self.disk_size_var.get())
            head = int(self.disk_head_var.get())
            requests = [int(x) for x in self.disk_requests_var.get().split() if x.strip() != ""]
        except ValueError:
            self.disk_total_var.set("Invalid input. Use numbers only.")
            self.disk_sequence_var.set("Sequence:\n")
            return

        if disk_size <= 0 or head < 0 or head >= disk_size or any(r < 0 or r >= disk_size for r in requests):
            self.disk_total_var.set("Invalid input. Use numbers only.")
            self.disk_sequence_var.set("Sequence:\n")
            return

        algo = self.selected_disk_algo.get()
        if algo == "FCFS":
            sequence, total = disk_scheduling.fcfs(requests, head)
        elif algo == "SSTF":
            sequence, total = disk_scheduling.sstf(requests, head)
        elif algo == "SCAN":
            sequence, total = disk_scheduling.scan(requests, head, disk_size)
        elif algo == "C-SCAN":
            sequence, total = disk_scheduling.cscan(requests, head, disk_size)
        elif algo == "LOOK":
            sequence, total = disk_scheduling.look(requests, head)
        elif algo == "C-LOOK":
            sequence, total = disk_scheduling.clook(requests, head)
        else:
            return

        self.disk_total_var.set(f"Total Movement:\n{total}")
        self.disk_sequence_var.set("Sequence:\n" + " -> ".join(map(str, sequence)))
        self.draw_disk_graph(sequence, disk_size)

    def draw_disk_graph(self, sequence, disk_size):
        if self.disk_graph_canvas is None:
            return

        self.disk_graph_canvas.delete("all")
        width = int(self.disk_graph_canvas["width"])
        height = int(self.disk_graph_canvas["height"])
        padding = 30

        if len(sequence) < 2:
            return

        min_track = min(sequence)
        max_track = max(sequence)
        if max_track == min_track:
            max_track += 1

        x_step = (width - padding * 2) / (len(sequence) - 1)
        y_scale = (height - padding * 2) / (max_track - min_track)

        points = []
        for i, track in enumerate(sequence):
            x = padding + i * x_step
            y = height - padding - ((track - min_track) * y_scale)
            points.append((x, y))

        for i in range(len(points) - 1):
            self.disk_graph_canvas.create_line(
                points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill="white", width=2
            )

        for i, (x, y) in enumerate(points):
            self.disk_graph_canvas.create_oval(x-5, y-5, x+5, y+5, fill="white", outline="white")
            self.disk_graph_canvas.create_text(x, y - 12, text=str(sequence[i]), fill="white", font=("Arial", 9))

        self.disk_graph_canvas.create_text(
            width // 2,
            height - 15,
            text="Head movement graph",
            fill="white",
            font=("Arial", 11, "bold")
        )

    # ---------------- ALGORITHM RUN ----------------
    def run_scheduler(self):
        self.canvas.delete("gantt")

        if self.cpu_table_manager is None:
            return

        data = self.cpu_table_manager.get_data()
        if not data:
            return

        algo = self.selected_algo.get()

        try:
            self.scheduler = scheduling_algorithm(data)

            if algo == "FCFS":
                self.result = self.scheduler.FCFS()
            elif algo == "SJF":
                self.result = self.scheduler.SJF()
            elif algo == "Priority":
                self.result = self.scheduler.NonPreemptivePriority()
            else:
                return

        except Exception as e:
            print("Scheduler error:", e)
            return

        processes = self.result.get("process", [])
        avg_tat = self.result.get("avg_tat", 0)
        avg_wt = self.result.get("avg_wt", 0)

        w, h = 1420, 780
        cx = w // 2
        cy = h // 2 + 30

        self.canvas.create_text(
            cx + 200,
            cy - 260,
            text=f"AVG TAT: {avg_tat:.2f} | AVG WT: {avg_wt:.2f}",
            font=("Arial", 14),
            fill="yellow",
            tags="gantt"
        )

        # GANTT
        x = cx - 200
        y = cy - 220

        for p in processes:
            self.canvas.create_rectangle(
                x, y, x + 80, y + 40,
                fill="white",
                tags="gantt"
            )

            self.canvas.create_text(
                x + 40, y + 20,
                text=p,
                fill="black",
                tags="gantt"
            )

            x += 80


if __name__ == "__main__":
    App().mainloop()
