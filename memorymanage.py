import tkinter as tk
from tkinter import ttk, messagebox

class Process:
    def __init__(self, pid, arrival_time, burst_time, mem_req):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_burst = burst_time
        self.mem_req = mem_req
        self.start_time = -1
        self.end_time = 0
        self.waiting_time = 0
        self.turnaround_time = 0
        self.in_memory = False
        self.memory_start = -1

class MemoryManager:
    def __init__(self, total_memory, os_size):
        self.total_memory = total_memory
        self.os_size = os_size
        self.blocks = [[os_size, total_memory - os_size, True, None]]
        self.last_allocated_idx = 0

    def allocate(self, process, strategy):
        allocated = False
        
        if strategy == "First Fit":
            for i, block in enumerate(self.blocks):
                if block[2] and block[1] >= process.mem_req:
                    self._split_block(i, process)
                    allocated = True
                    break
                    
        elif strategy == "Best Fit":
            best_idx = -1
            min_diff = float('inf')
            for i, block in enumerate(self.blocks):
                if block[2] and block[1] >= process.mem_req:
                    diff = block[1] - process.mem_req
                    if diff < min_diff:
                        min_diff = diff
                        best_idx = i
            if best_idx != -1:
                self._split_block(best_idx, process)
                allocated = True
                
        elif strategy == "Worst Fit":
            worst_idx = -1
            max_diff = -1
            for i, block in enumerate(self.blocks):
                if block[2] and block[1] >= process.mem_req:
                    diff = block[1] - process.mem_req
                    if diff > max_diff:
                        max_diff = diff
                        worst_idx = i
            if worst_idx != -1:
                self._split_block(worst_idx, process)
                allocated = True
                
        elif strategy == "Next Fit":
            n = len(self.blocks)
            for i in range(n):
                idx = (self.last_allocated_idx + i) % n
                block = self.blocks[idx]
                if block[2] and block[1] >= process.mem_req:
                    self._split_block(idx, process)
                    allocated = True
                    break
                    
        return allocated

    def _split_block(self, idx, process):
        block = self.blocks[idx]
        remaining_size = block[1] - process.mem_req
        
        block[2] = False
        block[3] = process.pid
        process.in_memory = True
        process.memory_start = block[0]
        
        if remaining_size > 0:
            new_block = [block[0] + process.mem_req, remaining_size, True, None]
            block[1] = process.mem_req
            self.blocks.insert(idx + 1, new_block)
            
        self.last_allocated_idx = idx

    def deallocate(self, process):
        for i, block in enumerate(self.blocks):
            if block[3] == process.pid:
                block[2] = True
                block[3] = None
                process.in_memory = False
                process.memory_start = -1
                break
        self.merge_holes()

    def merge_holes(self):
        i = 0
        while i < len(self.blocks) - 1:
            if self.blocks[i][2] and self.blocks[i+1][2]:
                self.blocks[i][1] += self.blocks[i+1][1]
                del self.blocks[i+1]
            else:
                i += 1

    def get_metrics(self, waiting_queue):
        free_mem = sum(b[1] for b in self.blocks if b[2])
        total_user_mem = self.total_memory - self.os_size
        used_mem = total_user_mem - free_mem
        
        utilization = (used_mem / total_user_mem) * 100 if total_user_mem > 0 else 0
        
        external_frag = 0
        # If there are processes waiting, check if total free memory is enough, but contiguous holes are too small
        if waiting_queue:
            next_req = waiting_queue[0].mem_req
            largest_hole = max([b[1] for b in self.blocks if b[2]] + [0])
            if free_mem >= next_req and largest_hole < next_req:
                external_frag = free_mem

        # MVT (Dynamic Partitioning) allocates exactly what is needed, so internal fragmentation is always 0
        internal_frag = 0 
        
        return utilization, external_frag, internal_frag

class OSSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Step-by-Step OS Simulator: MVT & Round Robin")
        self.root.geometry("1100x800")
        
        self.processes = []
        
        self.sim_running = False
        self.time = 0
        self.completed_count = 0
        self.current_quantum_tick = 0
        self.mem_manager = None
        self.input_queue = []
        self.ready_queue = []

        self.setup_ui()

    def setup_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)


        # Inputs
        input_frame = ttk.LabelFrame(top_frame, text="System Parameters")
        input_frame.pack(side="left", fill="x", expand=True, padx=5)

        ttk.Label(input_frame, text="Total Mem:").grid(row=0, column=0, padx=2)
        self.total_mem_var = tk.IntVar(value=256)
        ttk.Entry(input_frame, textvariable=self.total_mem_var, width=5).grid(row=0, column=1)

        ttk.Label(input_frame, text="OS Size:").grid(row=0, column=2, padx=2)
        self.os_size_var = tk.IntVar(value=40)
        ttk.Entry(input_frame, textvariable=self.os_size_var, width=5).grid(row=0, column=3)

        ttk.Label(input_frame, text="Quantum:").grid(row=0, column=4, padx=2)
        self.quantum_var = tk.IntVar(value=5)
        ttk.Entry(input_frame, textvariable=self.quantum_var, width=5).grid(row=0, column=5)

        ttk.Label(input_frame, text="Policy:").grid(row=0, column=6, padx=2)
        self.strategy_var = tk.StringVar(value="First Fit")
        ttk.Combobox(input_frame, textvariable=self.strategy_var, values=["First Fit", "Best Fit", "Worst Fit", "Next Fit"], state="readonly", width=10).grid(row=0, column=7)


        # Process Add
        proc_frame = ttk.LabelFrame(top_frame, text="Add Process")
        proc_frame.pack(side="left", fill="x", expand=True, padx=5)

        ttk.Label(proc_frame, text="PID:").grid(row=0, column=0, padx=2)
        self.pid_var = tk.StringVar(value="J1")
        ttk.Entry(proc_frame, textvariable=self.pid_var, width=5).grid(row=0, column=1)

        ttk.Label(proc_frame, text="Arr:").grid(row=0, column=2, padx=2)
        self.arr_var = tk.IntVar(value=0)
        ttk.Entry(proc_frame, textvariable=self.arr_var, width=5).grid(row=0, column=3)

        ttk.Label(proc_frame, text="Burst:").grid(row=0, column=4, padx=2)
        self.burst_var = tk.IntVar(value=10)
        ttk.Entry(proc_frame, textvariable=self.burst_var, width=5).grid(row=0, column=5)

        ttk.Label(proc_frame, text="Mem:").grid(row=0, column=6, padx=2)
        self.mem_req_var = tk.IntVar(value=60)
        ttk.Entry(proc_frame, textvariable=self.mem_req_var, width=5).grid(row=0, column=7)

        ttk.Button(proc_frame, text="Add", command=self.add_process).grid(row=0, column=8, padx=5)


        # Middle Content (Table + Canvas)
        mid_frame = ttk.Frame(self.root)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Column: Tables & Controls
        left_col = ttk.Frame(mid_frame)
        left_col.pack(side="left", fill="both", expand=True)
        
        columns = ("PID", "Arrival", "Burst", "Memory", "Status")
        self.tree = ttk.Treeview(left_col, columns=columns, show="headings", height=6)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=60, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=5)
        
        control_frame = ttk.Frame(left_col)
        control_frame.pack(pady=5)
        
        ttk.Button(control_frame, text="Clear Data", command=self.clear_processes).grid(row=0, column=0, padx=5)
        self.init_btn = ttk.Button(control_frame, text="Initialize Simulation", command=self.init_simulation)
        self.init_btn.grid(row=0, column=1, padx=5)
        
        self.step_btn = ttk.Button(control_frame, text="Next Step (1ms)", command=self.step_simulation, state="disabled")
        self.step_btn.grid(row=0, column=2, padx=5)

        self.fast_btn = ttk.Button(control_frame, text="Run to End", command=self.run_to_end, state="disabled")
        self.fast_btn.grid(row=0, column=3, padx=5)


        # Memory Map
        map_frame = ttk.LabelFrame(mid_frame, text="Live Memory Map")
        map_frame.pack(side="right", fill="both", expand=True, padx=10)
        self.canvas = tk.Canvas(map_frame, width=200, bg="white")
        self.canvas.pack(fill="y", expand=True, pady=10)


        # Metrics & Logs
        bot_frame = ttk.Frame(self.root)
        bot_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.time_label = ttk.Label(bot_frame, text="Current Time: 0 ms", font=("Arial", 12, "bold"), foreground="blue")
        self.time_label.pack(anchor="w")

        self.metrics_label = ttk.Label(bot_frame, text="Memory Utilization: 0% | Ext. Fragmentation: 0K | Int. Fragmentation: 0K", font=("Arial", 10, "bold"))
        self.metrics_label.pack(anchor="w", pady=5)

        self.log_text = tk.Text(bot_frame, state="disabled", height=10)
        self.log_text.pack(fill="both", expand=True)


    def add_process(self):
        pid = self.pid_var.get()
        self.processes.append(Process(pid, self.arr_var.get(), self.burst_var.get(), self.mem_req_var.get()))
        self.update_table()
        self.pid_var.set(f"J{len(self.processes)+1}")

    def update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for p in self.processes:
            status = "Completed" if p.remaining_burst == 0 and self.sim_running else ("Running/Ready" if p.in_memory else "Waiting")
            if not self.sim_running and p.remaining_burst == p.burst_time:
                status = "Not Started"
            self.tree.insert("", "end", values=(p.pid, p.arrival_time, p.burst_time, p.mem_req, status))

    def clear_processes(self):
        self.processes.clear()
        self.update_table()
        self.canvas.delete("all")
        self.sim_running = False
        self.step_btn.config(state="disabled")
        self.fast_btn.config(state="disabled")
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        self.time_label.config(text="Current Time: 0 ms")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def draw_memory(self):
        if not self.mem_manager: return
        self.canvas.delete("all")
        tot = self.mem_manager.total_memory
        c_height = int(self.canvas.winfo_height())
        if c_height <= 10: c_height = 400 
            
        y_scale = c_height / tot
        
        os_h = self.mem_manager.os_size * y_scale
        self.canvas.create_rectangle(10, 10, 190, 10 + os_h, fill="#555555")
        self.canvas.create_text(100, 10 + os_h/2, text=f"OS ({self.mem_manager.os_size}K)", fill="white")
        
        y_offset = 10 + os_h
        for block in self.mem_manager.blocks:
            h = block[1] * y_scale
            color = "#f0f0f0" if block[2] else "#88ccff"
            text = f"Free ({block[1]}K)" if block[2] else f"{block[3]} ({block[1]}K)"
            self.canvas.create_rectangle(10, y_offset, 190, y_offset + h, fill=color)
            self.canvas.create_text(100, y_offset + h/2, text=text)
            y_offset += h
            
        self.root.update()

    def update_metrics(self):
        util, ext_frag, int_frag = self.mem_manager.get_metrics(self.input_queue)
        self.metrics_label.config(text=f"Memory Utilization: {util:.1f}% | Ext. Frag: {ext_frag}K | Int. Frag: {int_frag}K")
        self.time_label.config(text=f"Current Time: {self.time} ms")

# this part uhh idk
    def init_simulation(self):
        if not self.processes: return
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")

        tot = self.total_mem_var.get()
        os_sz = self.os_size_var.get()
        self.strategy = self.strategy_var.get()
        self.quantum = self.quantum_var.get()

        self.mem_manager = MemoryManager(tot, os_sz)
        self.time = 0
        self.completed_count = 0
        self.current_quantum_tick = 0
        self.input_queue = []
        self.ready_queue = []
        
        for p in self.processes:
            p.remaining_burst = p.burst_time
            p.in_memory = False
            p.start_time = -1
            p.end_time = 0

        self.sim_running = True
        self.step_btn.config(state="normal")
        self.fast_btn.config(state="normal")
        
        self.log(f"--- INITIALIZED: {self.strategy} | RR Q={self.quantum} ---")
        self.draw_memory()
        self.update_metrics()
        self.update_table()

    def step_simulation(self):
        if self.completed_count >= len(self.processes):
            self.finish_simulation()
            return

        # 1. Check for new arrivals
        for p in self.processes:
            if p.arrival_time == self.time and p not in self.input_queue and not p.in_memory and p.remaining_burst > 0:
                self.input_queue.append(p)
                self.log(f"[T={self.time}] {p.pid} arrived. Added to Wait Queue.")

        # 2. Memory Allocation
        loaded = True
        while loaded and self.input_queue:
            loaded = False
            for p in list(self.input_queue):
                if self.mem_manager.allocate(p, self.strategy):
                    self.input_queue.remove(p)
                    self.ready_queue.append(p)
                    self.log(f"[T={self.time}] {p.pid} loaded into memory at {p.memory_start}K")
                    loaded = True
                    break

        # 3. CPU Execution
        if self.ready_queue:
            curr = self.ready_queue[0]
            if curr.start_time == -1:
                curr.start_time = self.time
            
            # Execute for 1ms
            curr.remaining_burst -= 1
            self.current_quantum_tick += 1
            
            if curr.remaining_burst == 0:
                curr.end_time = self.time + 1
                curr.turnaround_time = curr.end_time - curr.arrival_time
                curr.waiting_time = curr.turnaround_time - curr.burst_time
                self.completed_count += 1
                self.mem_manager.deallocate(curr)
                self.ready_queue.pop(0)
                self.current_quantum_tick = 0
                self.log(f"[T={self.time+1}] {curr.pid} finished! Memory Released.")
            
            elif self.current_quantum_tick == self.quantum:
                # Time quantum expired, rotate queue
                rotated = self.ready_queue.pop(0)
                self.ready_queue.append(rotated)
                self.current_quantum_tick = 0
                self.log(f"[T={self.time+1}] Quantum expired for {rotated.pid}. Context Switch.")
        
        self.time += 1
        self.draw_memory()
        self.update_metrics()
        self.update_table()

    def run_to_end(self):
        while self.completed_count < len(self.processes):
            self.step_simulation()
            
    def finish_simulation(self):
        self.sim_running = False
        self.step_btn.config(state="disabled")
        self.fast_btn.config(state="disabled")
        self.log("\n--- SIMULATION COMPLETE ---")
        
        total_tat = sum(p.turnaround_time for p in self.processes)
        total_wt = sum(p.waiting_time for p in self.processes)
        n = len(self.processes)
        
        self.log(f"Average Turnaround Time: {total_tat/n:.2f} ms")
        self.log(f"Average Waiting Time: {total_wt/n:.2f} ms")
        self.update_table()

if __name__ == "__main__":
    root = tk.Tk()
    app = OSSimulatorApp(root)
    root.mainloop()
