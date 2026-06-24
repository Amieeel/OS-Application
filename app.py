import tkinter as tk
from PIL import Image, ImageTk
from img_loader import get_images
from cpuschedulingv2 import scheduling_algorithm
import disk_scheduling
import importlib.util
import os
import re
from Memory_Management import Process as MemProcess, MemoryManager as MemMemoryManager
from process_manager import ProcessTableManager
from content_data import LEARN_CONTENT, ABOUT_CONTENT


FONT_FAMILY = "Segoe UI"
FONT_SEMIBOLD = "Segoe UI Semibold"
PANEL_BG = "#315d75"
PANEL_BG_DARK = "#193c54"
TEXT_PRIMARY = "#f6fbff"
TEXT_MUTED = "#c9dde8"
INK = "#0a2a3c"
ACCENT = "#f4d35e"
BUTTON_BG = "#23607f"
BUTTON_ACTIVE_BG = "#347d9e"


def load_virtual_memory_module():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.join(script_dir, "Virtual Memory.py")
    spec = importlib.util.spec_from_file_location("virtual_memory", module_path)
    vm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm)
    return vm


def create_scrollable_text(parent, width=28, height=6, bg=PANEL_BG_DARK, fg=TEXT_PRIMARY, font=(FONT_FAMILY, 10)):
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
        wrap=tk.WORD,
        insertbackground=fg,
        selectbackground=BUTTON_ACTIVE_BG,
        padx=8,
        pady=6
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
        self.configure_base_style()

        # assets
        self.imgs = get_images()

        # canvas
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # track embedded widgets so they can be destroyed when changing screens
        self.ui_windows = []
        self.ui_window_ids = []
        self._orig_canvas_create_window = self.canvas.create_window
        def _create_window(x, y, window=None, **kwargs):
            item_id = self._orig_canvas_create_window(x, y, window=window, **kwargs)
            if window is not None:
                self.ui_windows.append(window)
                self.ui_window_ids.append(item_id)
            return item_id
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
        self.cpu_quantum_var = tk.StringVar(value="2")
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

        # FOR VIRTUAL MEMORY
        self.virtual_pages_var = tk.StringVar(value="7,0,1,2,0,3")
        self.virtual_capacity_var = tk.StringVar(value="3")
        self.virtual_algo_var = tk.StringVar(value="FIFO")
        self.virtual_faults_var = tk.StringVar(value="0")
        self.virtual_hits_var = tk.StringVar(value="0")

        self.virtual_frames_canvas = None
        self.virtual_log_text = None
        self.virtual_sequence_text = None
        self.virtual_step_btn = None
        self.virtual_run_btn = None
        self.virtual_faults_text_id = None
        self.virtual_hits_text_id = None

        self.virtual_manager = None
        self.virtual_pages_list = []
        self.virtual_history = []
        self.virtual_current_step = 0
        self.virtual_faults = 0
        self.virtual_hits = 0

        self.virtual_module = load_virtual_memory_module()

        # saved table data (persist across screen switches)
        self._cpu_table_saved_data = None
        self._memory_table_saved_data = None

        self.set_background("home")
        self.create_main_menu()
        self.render_buttons()

    def configure_base_style(self):
        self.option_add("*Font", f"{{{FONT_FAMILY}}} 10")
        self.option_add("*Menu.font", f"{{{FONT_FAMILY}}} 10")
        self.option_add("*Entry.relief", "flat")
        self.option_add("*Entry.borderWidth", 0)
        self.option_add("*Button.relief", "flat")
        self.option_add("*Button.borderWidth", 0)

    def style_entry(self, entry):
        entry.config(
            bg="#edf7fb",
            fg=INK,
            insertbackground=INK,
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground="#5f93aa",
            highlightcolor=ACCENT,
        )

    def style_panel_button(self, button):
        button.config(
            font=(FONT_SEMIBOLD, 10),
            bg=BUTTON_BG,
            fg=TEXT_PRIMARY,
            activebackground=BUTTON_ACTIVE_BG,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )

    def create_panel_button(self, parent, text, command, state="normal", padx=10, pady=3):
        button = tk.Button(parent, text=text, command=command, padx=padx, pady=pady, state=state)
        self.style_panel_button(button)
        return button

    def style_option_menu(self, menu, width):
        menu.config(
            font=(FONT_SEMIBOLD, 11),
            width=width,
            bg="#edf7fb",
            fg=INK,
            activebackground="#d6eef6",
            activeforeground=INK,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        try:
            menu["menu"].config(
                font=(FONT_FAMILY, 10),
                bg="#edf7fb",
                fg=INK,
                activebackground="#d6eef6",
                activeforeground=INK,
                bd=0,
            )
        except tk.TclError:
            pass

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
        try:
            if self.cpu_table_manager is not None:
                self._cpu_table_saved_data = self.cpu_table_manager.get_data()
        except Exception:
            self._cpu_table_saved_data = None

        # save memory table data if present so it can be restored
        try:
            if self.memory_table_manager is not None:
                self._memory_table_saved_data = self.memory_table_manager.get_data()
        except Exception:
            self._memory_table_saved_data = None

        self.clear_ui_windows()
        self.cpu_table_manager = None
        self.canvas.delete("ui")
        self.canvas.delete("gantt")

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

        for item_id in self.ui_window_ids:
            try:
                self.canvas.delete(item_id)
            except tk.TclError:
                pass
        self.ui_window_ids.clear()

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

    def on_learn(self):
        self.switch_screen("learn", self.create_learn_view)
        
    def on_about(self):
        self.switch_screen("about", self.create_about_view) 

    # ---------------- MENUS ----------------
    def create_main_menu(self):
        self.create_button("start", "start_button", 0.4, 0.45, self.on_start, scale=0.65)
        self.create_button("learn", "learn_button", 0.41, 0.59, self.on_learn, scale=0.6)
        self.create_button("about", "about_button", 0.41, 0.69, self.on_about, scale=0.6)

    def create_select_menu(self):
        self.create_button("back", "back_button", 0.03, 0.11, self.on_back, scale=0.6)
        self.create_button("CPU", "CPU_sched_button", 0.065, 0.27, self.on_CPU, scale=0.72)
        self.create_button("DISK", "Disk_sched_button", 0.285, 0.27, self.on_disk, scale=0.72)
        self.create_button("MEM", "Main_mem_button", 0.505, 0.27, self.on_memory, scale=0.72)
        self.create_button("VIRT", "Virt_mem_button", 0.725, 0.27, self.on_virtual, scale=0.72)


     # ---------------- LEARN----------------
    def create_learn_view(self):
        w, h = 1420, 780
        self.canvas.delete("ui")

        cont_img = self.imgs["learn-cont"]
        resized = cont_img.resize((int(w * 0.9), int(h * 0.75)), Image.Resampling.LANCZOS)
        self.learn_cont_tk = ImageTk.PhotoImage(resized)
        self.canvas.create_image(w // 2, h // 2 + 30, image=self.learn_cont_tk, tags="ui")
        
        self.create_button("back", "back_button", 0.015, 0.035, self.on_back, scale=0.4)
        
        # Mini-buttons for topics
        self.create_button("cpu_info", "CpuSched_MiniButton", 0.059, 0.265, lambda: self.show_learn_content("CPU"), scale=0.68)
        self.create_button("mem_info", "MainMem_Minibutton", 0.284, 0.265, lambda: self.show_learn_content("MEM"), scale=0.68)
        self.create_button("virt_info", "Virtual_MiniButton", 0.502, 0.265, lambda: self.show_learn_content("VIRT"), scale=0.68)
        self.create_button("disk_info", "Disk_MiniButton", 0.719, 0.265, lambda: self.show_learn_content("DISK"), scale=0.68)

        self.learn_title_id = self.canvas.create_text(
            w // 2, h // 2 + 90, 
            text="",
            font=("Century Gothic", 12, "bold"),
            fill="white",
            width=1000,      
            justify="center",
            anchor="n",      
            tags="ui"
        )

        self.learn_body_id = self.canvas.create_text(
            w // 2, h // 2 + 115, 
            text="Click a topic above to learn more.",
            font=("Century Gothic", 11),
            fill="white",
            width=1000,      
            justify="center",
            anchor="n",      
            tags="ui"
        )
        
    def show_learn_content(self, topic):
        content_data = {
            "CPU": {
                "title": "CPU Scheduling Algorithms",
                "body": "Inputs: You provide a list of processes along with Arrival Times, Burst Times, Priorities, and a Time Quantum.\n\nVisualization: The app generates a live Gantt Chart, displaying exactly which process occupies the CPU at any given millisecond.\n\nSimulation: Step through time to watch processes arrive, preempt, and finish."
            },
            "MEM": {
                "title": "Memory Management",
                "body": "Inputs: Define the Total Memory size, OS size, and a queue of incoming jobs.\n\nVisualization: A dynamic Memory Map draws the memory blocks, showing where the OS lives, where user processes are loaded, and where free \"holes\" exist.\n\nSimulation: Watch algorithms like First Fit, Best Fit, Worst Fit, and Next Fit hunt for appropriate holes and track fragmentation levels."
            },
            "VIRT": {
                "title": "Virtual Memory Management",
                "body": "Inputs: Input a Reference String (page sequence) and number of available physical Frames.\n\nVisualization: The app displays a Frame Grid, visually filling slots as pages are loaded and highlighting when a page is swapped out.\n\nSimulation: The app flags Page Faults vs. Page Hits and simulates algorithms like FIFO, Optimal, and LRU to calculate the total Page Fault Rate."
            },
            "DISK": {
                "title": "Disk Scheduling Algorithms",
                "body": "Inputs: Provide the starting head position, total cylinders, and request queue.\n\nVisualization: The app plots a path diagram showing the physical movement of the disk head.\n\nSimulation: Simulates FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK to compute total Head Movement (Seek Time) for efficiency comparison."
            }
        }

        data = content_data.get(topic, {"title": "", "body": "Content not found."})

        self.canvas.itemconfig(self.learn_title_id, text=data["title"])
        self.canvas.itemconfig(self.learn_body_id, text=data["body"])

     # ---------------- ABOUT ----------------
    def create_about_view(self):
        w, h = 1420, 780
        self.canvas.delete("ui")
        
        cont_img = self.imgs["about_cont"]
        resized = cont_img.resize((int(w * 0.9), int(h * 0.75)), Image.Resampling.LANCZOS)
        self.about_cont_tk = ImageTk.PhotoImage(resized)
        self.canvas.create_image(w // 2, h // 2 + 30, image=self.about_cont_tk, tags="ui")
        
        self.create_button("back", "back_button", 0.015, 0.035, self.on_back, scale=0.4)
        
        self.about_title1_id = self.canvas.create_text(
            w // 2, h // 2 - 22, 
            text="",
            font=("Century Gothic", 11, "bold"),
            fill="white",
            width=1000, 
            justify="center",
            anchor="n",
            tags="ui"
        )

        self.about_body1_id = self.canvas.create_text(
            w // 2, h // 2 - 2, 
            text="",
            font=("Century Gothic", 11),
            fill="white",
            width=1000, 
            justify="center",
            anchor="n",
            tags="ui"
        )
        
        self.about_title2_id = self.canvas.create_text(
            w // 2, h // 2 + 102, 
            text="",
            font=("Century Gothic", 11, "bold"),
            fill="white",
            width=1000, 
            justify="center",
            anchor="n",
            tags="ui"
        )

        self.about_body2_id = self.canvas.create_text(
            w // 2, h // 2 + 120, 
            text="",
            font=("Century Gothic", 11),
            fill="white",
            width=1000, 
            justify="center",
            anchor="n",
            tags="ui"
        )
        
        self.show_about_content()

    def show_about_content(self):
        title1 = "GO Rhythm (Ready, Set, GO!)"
        
        body1 = """Visualizes and simulates different algorithms according to CPU scheduling, \nmemory allocation, virtual memory, and disk scheduling in modern operating systems. \nThis educational tool allows users to input custom parameters, step through the execution of \nvarious OS algorithms, and observe real-time visual feedback and computed metrics. \nIt is designed to bridge the gap between theoretical OS concepts and practical, mechanical understanding."""

        title2 = "Algorithm Categories:"
        
        body2 = """CPU Scheduling: In a multiprogramming system, the OS decides which process uses the CPU.\nMemory Allocation: Main memory must accommodate both the OS and user processes efficiently.\nVirtual Memory: Virtual memory allows a computer to run processes larger than physical RAM.\nDisk Scheduling: Manages the movement of the disk head to minimize seek time."""

        # Update all four items
        self.canvas.itemconfig(self.about_title1_id, text=title1)
        self.canvas.itemconfig(self.about_body1_id, text=body1)
        self.canvas.itemconfig(self.about_title2_id, text=title2)
        self.canvas.itemconfig(self.about_body2_id, text=body2)

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

        self.create_button("back", "back_button", 0.015, 0.035, self.on_start, scale=0.4)

        # dropdown
        algo_menu = tk.OptionMenu(
            self,
            self.selected_algo,
            "FCFS",
            "SJF",
            "SRTF (Preemptive)",
            "Priority (Non-Preemptive)",
            "Priority (Preemptive)",
            "Round Robin"
        )

        self.canvas.create_window(
            container_x - 440,
            container_y + 195,
            window=algo_menu,
            tags="ui"
        )
        self.style_option_menu(algo_menu, width=22)

        self.canvas.create_text(
            container_x - 510,
            container_y + 245,
            text="Quantum",
            font=(FONT_SEMIBOLD, 12),
            fill=TEXT_PRIMARY,
            tags="ui"
        )
        quantum_entry = tk.Entry(self, textvariable=self.cpu_quantum_var, width=6, font=("Segoe UI", 12))
        self.style_entry(quantum_entry)
        self.canvas.create_window(
            container_x - 425,
            container_y + 245,
            window=quantum_entry,
            tags="ui"
        )

        # table manager
        if self.cpu_table_manager is None:
            self.cpu_table_manager = ProcessTableManager(
                self.canvas,
                self,
                base_x=130,
                base_y=190,
                col_x=[40, 110, 200]
            )
            saved = self._cpu_table_saved_data or []
            for i, row in enumerate(saved):
                while len(self.cpu_table_manager.entries) <= i:
                    self.cpu_table_manager.add_row()

                arrival_entry, burst_entry, priority_entry = self.cpu_table_manager.entries[i]
                burst_val = str(row[1]) if len(row) > 1 and row[1] is not None else ""
                arrival_val = str(row[2]) if len(row) > 2 and row[2] is not None else ""
                priority_val = str(row[3]) if len(row) > 3 and row[3] is not None else ""

                arrival_entry.delete(0, tk.END)
                arrival_entry.insert(0, arrival_val)
                burst_entry.delete(0, tk.END)
                burst_entry.insert(0, burst_val)
                priority_entry.delete(0, tk.END)
                priority_entry.insert(0, priority_val)

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

        entry_font = ("Segoe UI", 12)

        disk_size_entry = tk.Entry(self, textvariable=self.disk_size_var, width=9, font=entry_font)
        self.style_entry(disk_size_entry)
        self.canvas.create_window(container_x - 455, container_y - 230, window=disk_size_entry, tags="ui")

        head_entry = tk.Entry(self, textvariable=self.disk_head_var, width=9, font=entry_font)
        self.style_entry(head_entry)
        self.canvas.create_window(container_x - 150, container_y - 230, window=head_entry, tags="ui")

        requests_entry = tk.Entry(self, textvariable=self.disk_requests_var, width=24, font=entry_font)
        self.style_entry(requests_entry)
        self.canvas.create_window(container_x + 167, container_y - 230, window=requests_entry, tags="ui")

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
        self.style_option_menu(algo_menu, width=8)

        total_frame = tk.Label(
            self,
            textvariable=self.disk_total_var,
            bg=PANEL_BG_DARK,
            fg=TEXT_PRIMARY,
            font=(FONT_SEMIBOLD, 13),
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
            bg=PANEL_BG_DARK,
            fg=TEXT_PRIMARY,
            font=(FONT_FAMILY, 10)
        )
        self.disk_sequence_text.insert("1.0", "Sequence:\n")
        self.disk_sequence_text.config(state="disabled")
        self.canvas.create_window(container_x - 455, container_y + 185, window=sequence_frame, tags="ui")

        self.disk_graph_canvas = tk.Canvas(
            self,
            width=850,
            height=400,
            bg=PANEL_BG_DARK,
            bd=0,
            highlightthickness=0
        )
        self.canvas.create_window(container_x + 155, container_y + 65, window=self.disk_graph_canvas, tags="ui")

        self.create_button("back", "back_button", 0.015, 0.035, self.on_start, scale=0.4)

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

        self.create_button("back", "back_button", 0.015, 0.035, self.on_start, scale=0.4)

        entry_font = ("Segoe UI", 12)

        # System inputs
        total_entry = tk.Entry(self, textvariable=self.memory_total_mem_var, width=6, font=entry_font)
        self.style_entry(total_entry)
        self.canvas.create_window(container_x - 165, container_y - 145, window=total_entry, tags="ui")

        os_entry = tk.Entry(self, textvariable=self.memory_os_size_var, width=6, font=entry_font)
        self.style_entry(os_entry)
        self.canvas.create_window(container_x + 50, container_y - 145, window=os_entry, tags="ui")

        quantum_entry = tk.Entry(self, textvariable=self.memory_quantum_var, width=6, font=entry_font)
        self.style_entry(quantum_entry)
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
        self.style_option_menu(policy_menu, width=9)

        # Process table 
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
                win_height=255,
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
            bg=PANEL_BG_DARK,
            fg=TEXT_PRIMARY,
            font=(FONT_FAMILY, 10),
            justify="left",
            width=28,
            height=2,
            bd=0
        )
        # position metrics under the Start button (shifted right/down)
        self.canvas.create_window(container_x - 440, container_y + 200, window=metrics_label, tags="ui")

        # Create scrollable log text widget for memory
        log_frame, self.memory_log_text = create_scrollable_text(
            self,
            width=28,
            height=20,
            bg=PANEL_BG_DARK,
            fg=TEXT_PRIMARY,
            font=(FONT_FAMILY, 10)
        )
        self.memory_log_text.insert("1.0", "Logs:\n")
        self.memory_log_text.config(state="disabled")
        self.canvas.create_window(container_x - 140, container_y + 75, window=log_frame, tags="ui")

        self.memory_map_canvas = tk.Canvas(
            self,
            width=600,
            height=350,
            bg=PANEL_BG_DARK,
            bd=0,
            highlightthickness=0
        )
        self.canvas.create_window(container_x + 275, container_y + 75, window=self.memory_map_canvas, tags="ui")

        # Initialize and Step buttons
        init_btn = self.create_panel_button(self, "Initialize", self.init_memory_simulation, padx=15, pady=5)
        self.canvas.create_window(container_x - 180, container_y + 320, window=init_btn, tags="ui")

        self.memory_step_btn = self.create_panel_button(
            self,
            "Next Step (1ms)",
            self.memory_step_simulation,
            padx=15,
            pady=5,
            state="disabled"
        )
        self.canvas.create_window(container_x, container_y + 320, window=self.memory_step_btn, tags="ui")

    # ---------------- VIRTUAL VIEW ----------------
    def create_virtual_view(self):
        w, h = 1420, 780
        self.canvas.delete("ui")

        cont_img = self.imgs["virt_cont"]
        cont_w = int(w * 0.92)
        cont_h = int(cont_w * cont_img.height / cont_img.width)
        resized = cont_img.resize((cont_w, cont_h), Image.Resampling.LANCZOS)
        self.virtual_cont_tk = ImageTk.PhotoImage(resized)

        container_x = w // 2
        container_y = h // 2 + 30
        self.canvas.create_image(container_x, container_y, image=self.virtual_cont_tk, tags="ui")
        self.create_button("back", "back_button", 0.015, 0.035, self.on_start, scale=0.4)

        input_frame = tk.Frame(self, bg=PANEL_BG)
        pages_entry = tk.Entry(
            input_frame,
            textvariable=self.virtual_pages_var,
            width=24,
            font=("Segoe UI", 13),
            justify="center"
        )
        self.style_entry(pages_entry)
        pages_entry.grid(row=0, column=0, columnspan=3, padx=8, pady=(0, 12), sticky="ew")
        tk.Label(input_frame, text="Frames", font=(FONT_SEMIBOLD, 12), bg=PANEL_BG, fg=TEXT_PRIMARY).grid(row=1, column=0, padx=(8, 4))
        capacity_entry = tk.Entry(input_frame, textvariable=self.virtual_capacity_var, width=5, font=(FONT_FAMILY, 12), justify="center")
        self.style_entry(capacity_entry)
        capacity_entry.grid(row=1, column=1, padx=4)

        self.virtual_step_btn = self.create_panel_button(
            input_frame,
            "Step",
            self.virtual_step_simulation,
            state="disabled"
        )
        self.create_panel_button(
            input_frame,
            "Init",
            self.init_virtual_simulation,
        ).grid(row=2, column=0, padx=4, pady=(14, 0))
        self.virtual_step_btn.grid(row=2, column=1, padx=4, pady=(14, 0))
        self.virtual_run_btn = self.create_panel_button(
            input_frame,
            "Run All",
            self.run_virtual_simulation,
            state="disabled"
        )
        self.virtual_run_btn.grid(row=2, column=2, padx=4, pady=(14, 0))
        self.canvas.create_window(container_x - 465, container_y - 65, window=input_frame, tags="ui")

        self.virtual_faults_text_id = self.canvas.create_text(
            container_x - 150,
            container_y - 190,
            text=self.virtual_faults_var.get(),
            font=(FONT_SEMIBOLD, 22),
            fill=TEXT_PRIMARY,
            tags="ui"
        )

        self.virtual_hits_text_id = self.canvas.create_text(
            container_x + 160,
            container_y - 190,
            text=self.virtual_hits_var.get(),
            font=(FONT_SEMIBOLD, 22),
            fill=TEXT_PRIMARY,
            tags="ui"
        )

        self.virtual_algo_var.set(self.virtual_algo_var.get().upper())
        algo_menu = tk.OptionMenu(self, self.virtual_algo_var, "FIFO", "LRU", "OPTIMAL", "LFU")
        self.style_option_menu(algo_menu, width=10)
        self.canvas.create_window(container_x + 465, container_y - 190, window=algo_menu, tags="ui")

        logs_frame, self.virtual_log_text = create_scrollable_text(self, width=29, height=8, bg=PANEL_BG, fg=TEXT_PRIMARY, font=(FONT_FAMILY, 9))
        self.virtual_log_text.insert("1.0", "Activity:\n")
        self.virtual_log_text.config(state="disabled")
        self.virtual_sequence_text = None
        self.canvas.create_window(container_x - 465, container_y + 220, window=logs_frame, tags="ui")

        self.virtual_frames_canvas = tk.Canvas(self, width=885, height=410, bg=PANEL_BG, bd=0, highlightthickness=0)
        self.canvas.create_window(container_x + 160, container_y + 105, window=self.virtual_frames_canvas, tags="ui")
        self.draw_virtual_frames()

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

    # --- Virtual Memory Log Helpers ---
    def append_virtual_log(self, message):
        if self.virtual_log_text:
            self.virtual_log_text.config(state="normal")
            self.virtual_log_text.insert("end", message + "\n")
            self.virtual_log_text.see("end")
            self.virtual_log_text.config(state="disabled")

    def append_virtual_sequence(self, message):
        if self.virtual_sequence_text:
            self.virtual_sequence_text.config(state="normal")
            self.virtual_sequence_text.insert("end", message + "\n")
            self.virtual_sequence_text.see("end")
            self.virtual_sequence_text.config(state="disabled")

    def clear_virtual_logs(self):
        if self.virtual_log_text:
            self.virtual_log_text.config(state="normal")
            self.virtual_log_text.delete("1.0", "end")
            self.virtual_log_text.insert("1.0", "Activity:\n")
            self.virtual_log_text.config(state="disabled")
        if self.virtual_sequence_text:
            self.virtual_sequence_text.config(state="normal")
            self.virtual_sequence_text.delete("1.0", "end")
            self.virtual_sequence_text.insert("1.0", "Frames:\n")
            self.virtual_sequence_text.config(state="disabled")

    # --- Virtual Memory Step-by-Step Logic ---
    def update_virtual_counters(self):
        if self.virtual_faults_text_id:
            self.canvas.itemconfig(self.virtual_faults_text_id, text=self.virtual_faults_var.get())
        if self.virtual_hits_text_id:
            self.canvas.itemconfig(self.virtual_hits_text_id, text=self.virtual_hits_var.get())

    def parse_virtual_reference_string(self):
        raw_pages = self.virtual_pages_var.get().strip()
        tokens = [token for token in re.split(r"[,\s]+", raw_pages) if token]
        return [int(token) for token in tokens]

    def init_virtual_simulation(self):
        try:
            self.virtual_pages_list = self.parse_virtual_reference_string()
            capacity = int(self.virtual_capacity_var.get())
            algo = self.virtual_algo_var.get().lower()
        except ValueError:
            self.append_virtual_log("Error: Invalid reference string or capacity.")
            return

        if capacity <= 0:
            self.append_virtual_log("Error: Frames must be greater than 0.")
            return

        if capacity > 10:
            self.append_virtual_log("Error: Use 10 frames or fewer for a readable graph.")
            return

        if not self.virtual_pages_list:
            self.append_virtual_log("Error: Reference string is required.")
            return

        self.virtual_manager = self.virtual_module.PageReplacementManager(capacity, algo)
        self.virtual_current_step = 0
        self.virtual_faults = 0
        self.virtual_hits = 0
        self.virtual_history = []

        self.virtual_faults_var.set("0")
        self.virtual_hits_var.set("0")
        self.update_virtual_counters()

        self.clear_virtual_logs()
        self.draw_virtual_frames()
        self.append_virtual_log(f"{algo.upper()} initialized.")

        if hasattr(self, 'virtual_step_btn') and self.virtual_step_btn:
            self.virtual_step_btn.config(state="normal")
        if hasattr(self, 'virtual_run_btn') and self.virtual_run_btn:
            self.virtual_run_btn.config(state="normal")

    def run_virtual_simulation(self):
        if not self.virtual_manager:
            self.init_virtual_simulation()
            if not self.virtual_manager:
                return

        while self.virtual_current_step < len(self.virtual_pages_list):
            self.virtual_step_simulation(log_step=False)

        self.append_virtual_log("--- SIMULATION COMPLETE ---")

    def virtual_step_simulation(self, log_step=True):
        if not self.virtual_manager or self.virtual_current_step >= len(self.virtual_pages_list):
            self.append_virtual_log("--- SIMULATION COMPLETE ---")
            if hasattr(self, 'virtual_step_btn') and self.virtual_step_btn:
                self.virtual_step_btn.config(state="disabled")
            if hasattr(self, 'virtual_run_btn') and self.virtual_run_btn:
                self.virtual_run_btn.config(state="disabled")
            return

        page = self.virtual_pages_list[self.virtual_current_step]
        algo = self.virtual_algo_var.get().lower()

        if algo == "optimal":
            future_refs = self.virtual_pages_list[self.virtual_current_step + 1:]
            frames, is_fault = self.virtual_manager.step(page, future_refs)
        else:
            frames, is_fault = self.virtual_manager.step(page)

        if is_fault:
            self.virtual_faults += 1
            status = "FAULT"
        else:
            self.virtual_hits += 1
            status = "HIT"

        self.virtual_faults_var.set(str(self.virtual_faults))
        self.virtual_hits_var.set(str(self.virtual_hits))
        self.update_virtual_counters()

        self.virtual_history.append({
            "page": page,
            "frames": list(frames),
            "status": status,
            "is_fault": is_fault
        })
        self.virtual_current_step += 1
        self.draw_virtual_frames()

        if log_step:
            frame_text = ", ".join(str(frame) for frame in frames)
            self.append_virtual_log(f"{self.virtual_current_step}. Page {page}: {status} | [{frame_text}]")

        if self.virtual_current_step >= len(self.virtual_pages_list):
            if log_step:
                self.append_virtual_log("--- SIMULATION COMPLETE ---")
            if hasattr(self, 'virtual_step_btn') and self.virtual_step_btn:
                self.virtual_step_btn.config(state="disabled")
            if hasattr(self, 'virtual_run_btn') and self.virtual_run_btn:
                self.virtual_run_btn.config(state="disabled")

    def draw_virtual_frames(self, frames=None):
        if self.virtual_frames_canvas is None:
            return

        self.virtual_frames_canvas.delete("all")
        width = int(self.virtual_frames_canvas["width"])
        height = int(self.virtual_frames_canvas["height"])
        try:
            pages = (self.virtual_pages_list or self.parse_virtual_reference_string()) if self.virtual_pages_var.get().strip() else []
        except ValueError:
            pages = []
        capacity = int(self.virtual_capacity_var.get()) if self.virtual_capacity_var.get().isdigit() else 3
        capacity = max(1, min(10, capacity))

        if not pages:
            self.virtual_frames_canvas.create_text(
                width // 2,
                height // 2,
                text="Enter references and initialize.",
                fill=TEXT_MUTED,
                font=(FONT_SEMIBOLD, 16)
            )
            return

        padding = 18
        label_w = 64
        header_h = 42
        status_h = 42
        table_w = width - (padding * 2) - label_w
        col_w = table_w / len(pages)
        row_h = (height - (padding * 2) - header_h - status_h) / max(1, capacity)
        font_size = max(8, min(13, int(col_w * 0.36), int(row_h * 0.42)))
        small_font_size = max(7, min(10, font_size - 1))

        self.virtual_frames_canvas.create_text(
            padding + 5,
            padding + header_h / 2,
            text="Page",
            fill=TEXT_MUTED,
            anchor="w",
            font=(FONT_SEMIBOLD, 10)
        )

        for i, page in enumerate(pages):
            x1 = padding + label_w + (i * col_w)
            x2 = x1 + col_w
            completed = i < len(self.virtual_history)
            current = i == len(self.virtual_history) - 1
            fill = "#f3f8fb" if completed else "#254d62"
            outline = ACCENT if current else "#16384a"

            self.virtual_frames_canvas.create_rectangle(
                x1, padding, x2, padding + header_h,
                fill=fill,
                outline=outline,
                width=2 if current else 1
            )
            self.virtual_frames_canvas.create_text(
                (x1 + x2) / 2,
                padding + header_h / 2,
                text=str(page),
                fill=INK if completed else TEXT_MUTED,
                font=(FONT_SEMIBOLD, font_size)
            )

        for frame_index in range(capacity):
            y1 = padding + header_h + (frame_index * row_h)
            y2 = y1 + row_h
            self.virtual_frames_canvas.create_text(
                padding + 5,
                (y1 + y2) / 2,
                text=f"F{frame_index + 1}",
                fill=TEXT_MUTED,
                anchor="w",
                font=(FONT_SEMIBOLD, 10)
            )
            self.virtual_frames_canvas.create_line(
                padding,
                y2,
                width - padding,
                y2,
                fill="#5f93aa"
            )

            for step_index in range(len(pages)):
                x1 = padding + label_w + (step_index * col_w)
                x2 = x1 + col_w
                value = ""

                if step_index < len(self.virtual_history):
                    step_frames = self.virtual_history[step_index]["frames"]
                    if frame_index < len(step_frames):
                        value = str(step_frames[frame_index])

                self.virtual_frames_canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=PANEL_BG,
                    outline="#5f93aa"
                )
                if value:
                    self.virtual_frames_canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=value,
                        fill=TEXT_PRIMARY,
                        font=(FONT_SEMIBOLD, font_size)
                    )

        status_y1 = height - padding - status_h
        self.virtual_frames_canvas.create_text(
            padding + 5,
            status_y1 + status_h / 2,
            text="Result",
            fill=TEXT_MUTED,
            anchor="w",
            font=(FONT_SEMIBOLD, 10)
        )

        for i in range(len(pages)):
            x1 = padding + label_w + (i * col_w)
            x2 = x1 + col_w
            if i >= len(self.virtual_history):
                self.virtual_frames_canvas.create_rectangle(x1, status_y1, x2, status_y1 + status_h, fill="#254d62", outline="#5f93aa")
                continue

            status = self.virtual_history[i]["status"]
            fill = "#d95f59" if status == "FAULT" else "#42a478"
            self.virtual_frames_canvas.create_rectangle(x1, status_y1, x2, status_y1 + status_h, fill=fill, outline=INK)
            self.virtual_frames_canvas.create_text(
                (x1 + x2) / 2,
                status_y1 + status_h / 2,
                text="F" if status == "FAULT" else "H",
                fill=TEXT_PRIMARY,
                font=(FONT_SEMIBOLD, small_font_size)
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
            font=("Segoe UI", 9, "bold")
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
                font=("Segoe UI", 8)
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
            self.disk_graph_canvas.create_text(x, y - 12, text=str(sequence[i]), fill="white", font=("Segoe UI", 9))

        self.disk_graph_canvas.create_text(
            width // 2,
            height - 15,
            text="Head movement graph",
            fill="white",
            font=("Segoe UI", 11, "bold")
        )

    # ---------------- ALGORITHM RUN ----------------
    def draw_cpu_message(self, message):
        self.canvas.delete("gantt")
        w, h = 1420, 780
        cx = w // 2
        cy = h // 2 + 30

        self.canvas.create_text(
            cx + 205,
            cy - 215,
            text=message,
            font=(FONT_SEMIBOLD, 16),
            fill=ACCENT,
            width=760,
            tags="gantt"
        )

    def draw_cpu_metric_panel(self, x, y, values, avg_value):
        row_height = 28
        max_rows = 8

        for i, (name, value) in enumerate(zip(self.scheduler.process_names, values)):
            col = i // max_rows
            row = i % max_rows
            self.canvas.create_text(
                x + (col * 160),
                y + (row * row_height),
                text=f"{name}: {value}",
                font=(FONT_SEMIBOLD, 14),
                fill=TEXT_PRIMARY,
                anchor="w",
                tags="gantt"
            )

        self.canvas.create_text(
            x,
            y + 250,
            text=f"Average: {avg_value:.2f}",
            font=(FONT_SEMIBOLD, 15),
            fill=ACCENT,
            anchor="w",
            tags="gantt"
        )

    def draw_cpu_gantt(self, segments):
        if not segments:
            return

        w, h = 1420, 780
        cx = w // 2
        cy = h // 2 + 30

        x0 = cx - 235
        x1 = cx + 550
        y0 = cy - 230
        y1 = y0 + 48
        total_time = max(1, segments[-1]["end"] - segments[0]["start"])
        scale = (x1 - x0) / total_time

        for segment in segments:
            start = segment["start"]
            end = segment["end"]
            label = segment["process"]
            left = x0 + ((start - segments[0]["start"]) * scale)
            right = x0 + ((end - segments[0]["start"]) * scale)
            fill = "#f2f7fb" if label != "Idle" else "#8aa3b3"

            self.canvas.create_rectangle(
                left, y0, right, y1,
                fill=fill,
                outline=INK,
                width=2,
                tags="gantt"
            )

            if right - left >= 26:
                self.canvas.create_text(
                    (left + right) / 2,
                    (y0 + y1) / 2,
                    text=label,
                    font=(FONT_SEMIBOLD, 11),
                    fill=INK,
                    tags="gantt"
                )

            self.canvas.create_text(
                left,
                y1 + 14,
                text=str(start),
                font=(FONT_FAMILY, 9),
                fill=TEXT_PRIMARY,
                tags="gantt"
            )

        self.canvas.create_text(
            x1,
            y1 + 14,
            text=str(segments[-1]["end"]),
            font=(FONT_FAMILY, 9),
            fill=TEXT_PRIMARY,
            tags="gantt"
        )

    def run_scheduler(self):
        self.canvas.delete("gantt")

        if self.cpu_table_manager is None:
            return

        data = self.cpu_table_manager.get_data()
        if not data:
            self.draw_cpu_message("Add at least one process with arrival and burst time.")
            return

        algo = self.selected_algo.get()

        try:
            self.scheduler = scheduling_algorithm(data)

            if algo == "FCFS":
                self.result = self.scheduler.FCFS()
            elif algo == "SJF":
                self.result = self.scheduler.SJF()
            elif algo == "SRTF (Preemptive)":
                self.result = self.scheduler.SRT()
            elif algo == "Priority (Non-Preemptive)":
                self.result = self.scheduler.NonPreemptivePriority()
            elif algo == "Priority (Preemptive)":
                self.result = self.scheduler.PreemptivePriority()
            elif algo == "Round Robin":
                self.result = self.scheduler.RoundRobin(self.cpu_quantum_var.get())
            else:
                return

        except Exception as e:
            print("Scheduler error:", e)
            self.draw_cpu_message(str(e))
            return

        segments = self.result.get("segments", [])
        tat = self.result.get("tat", [])
        wt = self.result.get("wt", [])
        avg_tat = self.result.get("avg_tat", 0)
        avg_wt = self.result.get("avg_wt", 0)

        w, h = 1420, 780
        cx = w // 2
        cy = h // 2 + 30

        self.draw_cpu_gantt(segments)
        self.draw_cpu_metric_panel(cx - 210, cy - 55, tat, avg_tat)
        self.draw_cpu_metric_panel(cx + 245, cy - 55, wt, avg_wt)


if __name__ == "__main__":
    App().mainloop()
