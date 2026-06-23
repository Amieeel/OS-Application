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


def create_scrollable_text(parent, width=28, height=6, bg="#193c54", fg="white", font=("Arial", 10)):
    """Create a Text widget with scrollbar for scrollable logs"""
    frame = tk.Frame(parent, bg=bg)
    
    text_widget = tk.Text(
        frame,
        width=width,
        height=height,
        bg=bg,
        fg=fg,
        font=font,
        bd=0,
        highlightthickness=0,
        wrap=tk.WORD
    )
    
    scrollbar = tk.Scrollbar(frame, command=text_widget.yview, bg="#1a3a4a", troughcolor="#0a1a2a")
    text_widget.config(yscrollcommand=scrollbar.set)
    
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Bind mouse wheel for scrolling
    def _on_mousewheel(event):
        text_widget.yview_scroll(int(-1*(event.delta/120)), "units")
    
    text_widget.bind("<MouseWheel>", _on_mousewheel)
    
    return frame, text_widget


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

        # track embedded widgets so they can be destroyed when changing screens
        self.ui_windows = []
        self._orig_canvas_create_window = self.canvas.create_window
        def _create_window(x, y, window=None, **kwargs):
            if window is not None:
                self.ui_windows.append(window)
            return self._orig_canvas_create_window(x, y, window=window, **kwargs)
        self.canvas.create_window = _create_window

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
        # memory table manager (like CPU)
        self.memory_table_manager = None

        # FOR DISK SCHEDULING
        self.disk_size_var = tk.StringVar(value="200")
        self.disk_head_var = tk.StringVar(value="50")
        self.disk_requests_var = tk.StringVar(value="40 10 100 80")
        self.selected_disk_algo = tk.StringVar(value="FCFS")
        self.disk_total_var = tk.StringVar(value="Total Movement:\n")
        self.disk_sequence_var = tk.StringVar(value="Sequence:\n")
        self.disk_graph_canvas = None
        self.disk_sequence_text = None  # For scrollable text widget

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
        self.memory_sim_running = False
        self.memory_step_btn = None
        self.memory_log_text = None  # For scrollable text widget
        self.virtual_pages_var = tk.StringVar(value="7,0,1,2,0,3")
        self.virtual_capacity_var = tk.StringVar(value="3")
        self.virtual_algo_var = tk.StringVar(value="fifo")
        self.virtual_frames_canvas = None
        self.virtual_faults_var = tk.StringVar(value="Faults: 0")
        self.virtual_sequence_var = tk.StringVar(value="Frames:\n")
        self.virtual_log_var = tk.StringVar(value="Logs:\n")
        self.virtual_log_text = None  # For scrollable text widget
        self.virtual_sequence_text = None  # For scrollable text widget
        self.virtual_module = load_virtual_memory_module()
        # saved table data (persist across screen switches)
        self._memory_table_saved_data = None

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
        # save memory table data if present so it can be restored
        try:
            if self.memory_table_manager is not None:
                self._memory_table_saved_data = self.memory_table_manager.get_data()
        except Exception:
            self._memory_table_saved_data = None

        self.clear_ui_windows()
        self.canvas.delete("ui")

        self.set_background(bg)
        builder()

        self.updating_ui = False
        self.render_buttons()
        self.after(1, self.render_buttons)

    def clear_ui_windows(self):
        for widget in self.ui_windows:
            try:
                widget.destroy()
            except tk.TclError:
                pass
        self.ui_windows.clear()

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
        w, h = 1420, 770

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

        self.create_button("back", "back_button", 0.015, 0.035, self.on_back, scale=0.4)

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
        self.canvas.create_window(container_x - 455, container_y - 220, window=disk_size_entry, tags="ui")

        head_entry = tk.Entry(self, textvariable=self.disk_head_var, width=9, font=entry_font)
        self.canvas.create_window(container_x - 150, container_y - 220, window=head_entry, tags="ui")

        requests_entry = tk.Entry(self, textvariable=self.disk_requests_var, width=24, font=entry_font)
        self.canvas.create_window(container_x + 167, container_y - 220, window=requests_entry, tags="ui")

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
        self.canvas.create_window(container_x + 465, container_y - 230, window=algo_menu, tags="ui")
        algo_menu.config(font=("Arial", 14), width=7)

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
        self.canvas.create_window(container_x - 455, container_y - 60, window=total_frame, tags="ui")

        # Create scrollable text widget for disk sequence
        sequence_frame, self.disk_sequence_text = create_scrollable_text(
            self,
            width=24,
            height=4,
            bg="#193c54",
            fg="white",
            font=("Arial", 11)
        )
        self.disk_sequence_text.insert("1.0", "Sequence:\n")
        self.disk_sequence_text.config(state="disabled")
        self.canvas.create_window(container_x - 455, container_y + 185, window=sequence_frame, tags="ui")

        self.disk_graph_canvas = tk.Canvas(
            self,
            width=850,
            height=400,
            bg="#193c54",
            bd=0,
            highlightthickness=0
        )
        self.canvas.create_window(container_x + 155, container_y + 65, window=self.disk_graph_canvas, tags="ui")

        self.create_button("back", "back_button", 0.015, 0.035, self.on_back, scale=0.4)

        # run button
        self.create_button("disk_run", "start_button", 0.134, 0.57, self.run_disk_scheduler, scale=0.3)

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

        self.create_button("back", "back_button", 0.015, 0.035, self.on_back, scale=0.4)

        entry_font = ("Arial", 12)

        # System inputs
        total_entry = tk.Entry(self, textvariable=self.memory_total_mem_var, width=6, font=entry_font)
        self.canvas.create_window(container_x - 165, container_y - 145, window=total_entry, tags="ui")

        os_entry = tk.Entry(self, textvariable=self.memory_os_size_var, width=6, font=entry_font)
        self.canvas.create_window(container_x + 50, container_y - 145, window=os_entry, tags="ui")

        quantum_entry = tk.Entry(self, textvariable=self.memory_quantum_var, width=6, font=entry_font)
        self.canvas.create_window(container_x + 270, container_y - 145, window=quantum_entry, tags="ui")

        policy_menu = tk.OptionMenu(
            self,
            self.memory_policy_var,
            "First Fit",
            "Best Fit",
            "Worst Fit",
            "Next Fit"
        )
        self.canvas.create_window(container_x + 490, container_y - 145, window=policy_menu, tags="ui")
        policy_menu.config(font=("Arial", 11), width=8)

        # Process table (re-uses ProcessTableManager from CPU view)
        need_create = False
        if self.memory_table_manager is None:
            need_create = True
        else:
            try:
                if not getattr(self.memory_table_manager, 'container', None) or not self.memory_table_manager.container.winfo_exists():
                    need_create = True
            except Exception:
                need_create = True

        if need_create:
            self.memory_table_manager = ProcessTableManager(
                self.canvas,
                self,
                base_x=130,
                base_y=container_y - 155,
                col_x=[40, 110, 200],
                headers=["PID", "Arrival", "Burst", "Mem"],
                win_height=250,
            )

            # restore saved data into the table if available
            try:
                saved = self._memory_table_saved_data or []
                for i, row in enumerate(saved):
                    # make sure enough rows exist
                    while len(self.memory_table_manager.entries) <= i:
                        self.memory_table_manager.add_row()

                    arrival_entry, burst_entry, mem_entry = self.memory_table_manager.entries[i]
                    # saved row format: [name, burst, arrival, extra]
                    burst_val = str(row[1]) if len(row) > 1 and row[1] is not None else ""
                    arrival_val = str(row[2]) if len(row) > 2 and row[2] is not None else ""
                    mem_val = str(row[3]) if len(row) > 3 and row[3] is not None else ""

                    arrival_entry.delete(0, tk.END)
                    arrival_entry.insert(0, arrival_val)
                    burst_entry.delete(0, tk.END)
                    burst_entry.insert(0, burst_val)
                    mem_entry.delete(0, tk.END)
                    mem_entry.insert(0, mem_val)
            except Exception:
                pass

        # Metrics and logs
        metrics_label = tk.Label(
            self,
            textvariable=self.memory_metrics_var,
            bg="#193c54",
            fg="white",
            font=("Arial", 10),
            justify="left",
            width=24,
            height=2,
            bd=0
        )
        # position metrics under the Start button (shifted right/down)
        self.canvas.create_window(container_x - 440, container_y + 200, window=metrics_label, tags="ui")

        # Create scrollable log text widget for memory
        log_frame, self.memory_log_text = create_scrollable_text(
            self,
            width=28,
            height=21,
            bg="#193c54",
            fg="white",
            font=("Arial", 10)
        )
        self.memory_log_text.insert("1.0", "Logs:\n")
        self.memory_log_text.config(state="disabled")
        self.canvas.create_window(container_x - 140, container_y + 75, window=log_frame, tags="ui")

        self.memory_map_canvas = tk.Canvas(
            self,
            width=600,
            height=350,
            bg="#193c54",
            bd=0,
            highlightthickness=0
        )
        self.canvas.create_window(container_x + 275, container_y + 75, window=self.memory_map_canvas, tags="ui")

        # Initialize and Step buttons
        init_btn = tk.Button(
            self,
            text="Initialize",
            command=self.init_memory_simulation,
            font=("Arial", 11),
            bg="#2a5a8a",
            fg="white",
            padx=15,
            pady=5
        )
        self.canvas.create_window(container_x - 180, container_y + 320, window=init_btn, tags="ui")

        self.memory_step_btn = tk.Button(
            self,
            text="Next Step (1ms)",
            command=self.memory_step_simulation,
            font=("Arial", 11),
            bg="#2a5a8a",
            fg="white",
            padx=15,
            pady=5,
            state="disabled"
        )
        self.canvas.create_window(container_x, container_y + 320, window=self.memory_step_btn, tags="ui")

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

        self.create_button("back", "back_button", 0.015, 0.035, self.on_back, scale=0.4)

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
        # If a table manager exists, prefer its data
        if self.memory_table_manager is not None:
            table_data = self.memory_table_manager.get_data()
            for row in table_data:
                # row format from ProcessTableManager: [name, burst, arrival, extra]
                name = row[0]
                burst = row[1]
                arrival = row[2]
                mem = row[3] if len(row) > 3 and row[3] is not None else ""
                lines.append(f"{name}: A{arrival}, B{burst}, M{mem}")
        else:
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

    def append_memory_log(self, message):
        """Append a message to the memory log text widget"""
        if self.memory_log_text:
            self.memory_log_text.config(state="normal")
            self.memory_log_text.insert("end", message + "\n")
            self.memory_log_text.see("end")
            self.memory_log_text.config(state="disabled")

    def append_disk_log(self, message):
        """Append a message to the disk sequence text widget"""
        if self.disk_sequence_text:
            self.disk_sequence_text.config(state="normal")
            self.disk_sequence_text.insert("end", message + "\n")
            self.disk_sequence_text.see("end")
            self.disk_sequence_text.config(state="disabled")

    def set_disk_log(self, message):
        """Clear and set the disk sequence log"""
        if self.disk_sequence_text:
            self.disk_sequence_text.config(state="normal")
            self.disk_sequence_text.delete("1.0", "end")
            self.disk_sequence_text.insert("1.0", message + "\n")
            self.disk_sequence_text.config(state="disabled")

    def init_memory_simulation(self):
        # Collect processes from the memory table if present
        if self.memory_table_manager is not None:
            table_data = self.memory_table_manager.get_data()
            collected = []
            for row in table_data:
                # row: [name, burst, arrival, mem]
                if len(row) >= 3:
                    pid = row[0]
                    burst = int(row[1])
                    arrival = int(row[2])
                    mem_req = int(row[3]) if len(row) > 3 and row[3] is not None else 0
                    collected.append(MemProcess(pid, arrival, burst, mem_req))
            self.memory_processes = collected

        if not self.memory_processes:
            self.append_memory_log("Add at least one process")
            return

        try:
            total_mem = int(self.memory_total_mem_var.get())
            os_size = int(self.memory_os_size_var.get())
            self.memory_quantum = int(self.memory_quantum_var.get())
        except ValueError:
            self.append_memory_log("Invalid memory settings")
            return

        self.memory_manager = MemMemoryManager(total_mem, os_size)
        self.memory_strategy = self.memory_policy_var.get()
        self.memory_time = 0
        self.memory_completed_count = 0
        self.memory_quantum_tick = 0
        self.memory_input_queue = []
        self.memory_ready_queue = []
        self.append_memory_log("Simulation initialized")
        self.memory_sim_running = True

        for p in self.memory_processes:
            p.remaining_burst = p.burst_time
            p.in_memory = False
            p.start_time = -1
            p.end_time = 0

        if self.memory_step_btn:
            self.memory_step_btn.config(state="normal")

        self.update_memory_metrics()
        self.draw_memory_map()

    def memory_step_simulation(self):
        if not self.memory_sim_running or self.memory_completed_count >= len(self.memory_processes):
            self.append_memory_log("--- SIMULATION COMPLETE ---")
            self.memory_sim_running = False
            if self.memory_step_btn:
                self.memory_step_btn.config(state="disabled")
            return

        # 1. Check for new arrivals
        for p in self.memory_processes:
            if p.arrival_time == self.memory_time and p not in self.memory_input_queue and not p.in_memory and p.remaining_burst > 0:
                self.memory_input_queue.append(p)
                self.append_memory_log(f"[T={self.memory_time}] {p.pid} arrived. Added to Wait Queue.")

        # 2. Memory Allocation
        loaded = True
        while loaded and self.memory_input_queue:
            loaded = False
            for p in list(self.memory_input_queue):
                if self.memory_manager.allocate(p, self.memory_strategy):
                    self.memory_input_queue.remove(p)
                    self.memory_ready_queue.append(p)
                    self.append_memory_log(f"[T={self.memory_time}] {p.pid} loaded into memory at {p.memory_start}K")
                    loaded = True
                    break

        # 3. CPU Execution
        if self.memory_ready_queue:
            curr = self.memory_ready_queue[0]
            if curr.start_time == -1:
                curr.start_time = self.memory_time

            # Execute for 1ms
            curr.remaining_burst -= 1
            self.memory_quantum_tick += 1

            if curr.remaining_burst == 0:
                curr.end_time = self.memory_time + 1
                curr.turnaround_time = curr.end_time - curr.arrival_time
                curr.waiting_time = curr.turnaround_time - curr.burst_time
                self.memory_completed_count += 1
                self.memory_manager.deallocate(curr)
                self.memory_ready_queue.pop(0)
                self.memory_quantum_tick = 0
                self.append_memory_log(f"[T={self.memory_time+1}] {curr.pid} finished! Memory Released.")

            elif self.memory_quantum_tick == self.memory_quantum:
                # Time quantum expired, rotate queue
                rotated = self.memory_ready_queue.pop(0)
                self.memory_ready_queue.append(rotated)
                self.memory_quantum_tick = 0
                self.append_memory_log(f"[T={self.memory_time+1}] Quantum expired for {rotated.pid}. Context Switch.")

        self.memory_time += 1
        self.update_memory_metrics()
        self.draw_memory_map()

    def update_memory_metrics(self):
        util, ext_frag, int_frag = self.memory_manager.get_metrics(self.memory_input_queue)
        time_str = f"[T={self.memory_time}ms]"
        self.memory_metrics_var.set(f"{time_str} | Utilization: {util:.1f}% | Ext: {ext_frag}K | Int: {int_frag}K")

    def draw_memory_map(self):
        if self.memory_map_canvas is None or self.memory_manager is None:
            return

        self.memory_map_canvas.delete("all")
        
        # Canvas dimensions
        width = int(self.memory_map_canvas["width"])
        height = int(self.memory_map_canvas["height"])
        padding = 15
        tot = self.memory_manager.total_memory
        
        # Calculate scale
        y_scale = (height - padding * 2) / tot if tot > 0 else 1
        y_offset = padding
        
        # Draw OS section
        os_h = max(10, self.memory_manager.os_size * y_scale)
        self.memory_map_canvas.create_rectangle(
            padding, y_offset, 
            width - padding, y_offset + os_h, 
            fill="#555555", 
            outline="white",
            width=2
        )
        self.memory_map_canvas.create_text(
            width // 2, y_offset + os_h / 2, 
            text=f"OS ({self.memory_manager.os_size}K)", 
            fill="white",
            font=("Arial", 9, "bold")
        )
        y_offset += os_h
        
        # Draw memory blocks
        for block in self.memory_manager.blocks:
            block_h = max(10, block[1] * y_scale)
            color = "#f0f0f0" if block[2] else "#88ccff"  # Light gray for free, light blue for allocated
            outline_color = "#999999" if block[2] else "#0066cc"
            
            self.memory_map_canvas.create_rectangle(
                padding, y_offset,
                width - padding, y_offset + block_h,
                fill=color,
                outline=outline_color,
                width=2
            )
            
            # Label
            label = f"Free ({block[1]}K)" if block[2] else f"{block[3]} ({block[1]}K)"
            self.memory_map_canvas.create_text(
                width // 2, y_offset + block_h / 2,
                text=label,
                fill="black" if block[2] else "white",
                font=("Arial", 8)
            )
            y_offset += block_h

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
            self.set_disk_log("Sequence:")
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
            self.set_disk_log("Sequence:")
            return

        if disk_size <= 0 or head < 0 or head >= disk_size or any(r < 0 or r >= disk_size for r in requests):
            self.disk_total_var.set("Invalid input. Use numbers only.")
            self.set_disk_log("Sequence:")
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
        self.set_disk_log("Sequence:\n" + " -> ".join(map(str, sequence)))
        
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
