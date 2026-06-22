import tkinter as tk
from tkinter import ttk

class ProcessTableManager:
    def __init__(self, main_canvas, parent, base_x, base_y, col_x):
        self.main_canvas = main_canvas
        self.parent = parent
        
        self.bg_color = "#193c54" 
        
        self.container = tk.Frame(self.parent, bg=self.bg_color, bd=0)

        self.main_canvas.create_window(
            base_x, base_y, 
            window=self.container, 
            anchor="nw", 
            tags="ui", 
            width=285, 
            height=270 
        )
        
        self.canvas = tk.Canvas(self.container, bg=self.bg_color, bd=0, highlightthickness=0, width=260)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=270)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # FIX 2: Pack the scrollbar FIRST so it claims the right edge, THEN pack the canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas.bind("<Enter>", self._bound_to_mousewheel)
        self.canvas.bind("<Leave>", self._unbound_to_mousewheel)
        
        self.rows = []
        self.entries = []
        self.process_count = 0
        self.max_rows = 999  # Virtually unlimited now!
        self._lock = False

        # 4. Draw Headers using Grid Layout
        headers = ["Process", "Arrival", "Burst", "Priority"]
        for i, h in enumerate(headers):
            lbl = tk.Label(self.scrollable_frame, text=h, font=("Arial", 12, "bold"), bg=self.bg_color, fg="white")
            lbl.grid(row=0, column=i, padx=4, pady=4, sticky="w")
            self.scrollable_frame.grid_columnconfigure(i, minsize=70)
        self.scrollable_frame.grid_columnconfigure(0, minsize=40)

        # Initialize the first row
        self.add_row()

    # --- Mousewheel Helpers ---
    def _bound_to_mousewheel(self, event):
        # Windows/Mac scroll binding
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        # Adjust scrolling sensitivity if needed
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # --- Validation & Row Logic ---
    def validate_number(self, value_if_allowed):
        return value_if_allowed == "" or value_if_allowed.isdigit()

    def add_row(self):
        if self.process_count >= self.max_rows:
            return

        row_index = self.process_count
        self.process_count += 1
        process_name = f"P{row_index + 1}"
        
        grid_row = row_index + 1  # Offset by 1 because row 0 is headers

        # Process Label
        lbl = tk.Label(
            self.scrollable_frame,
            text=process_name,
            width=2,
            anchor="w",
            font=("Arial", 11, "bold"),
            bg=self.bg_color,
            fg="white"
        )
        lbl.grid(row=grid_row, column=0, padx=4, pady=4)

        vcmd = (self.parent.register(self.validate_number), "%P")

        arrival = tk.Entry(self.scrollable_frame, width=5, font=("Arial", 11), validate="key", validatecommand=vcmd)
        burst = tk.Entry(self.scrollable_frame, width=5, font=("Arial", 11), validate="key", validatecommand=vcmd)
        priority = tk.Entry(self.scrollable_frame, width=5, font=("Arial", 11), validate="key", validatecommand=vcmd)

        # Place inputs in grid
        arrival.grid(row=grid_row, column=1, padx=4, pady=4, sticky="w")
        burst.grid(row=grid_row, column=2, padx=4, pady=4, sticky="w")
        priority.grid(row=grid_row, column=3, padx=4, pady=4, sticky="w")

        self.rows.append((process_name, arrival, burst, priority))
        self.entries.append((arrival, burst, priority))

        # Auto-add next row
        arrival.bind("<KeyRelease>", lambda e: self.smart_add_row())
        burst.bind("<KeyRelease>", lambda e: self.smart_add_row())
        priority.bind("<KeyRelease>", lambda e: self.smart_add_row())

    def smart_add_row(self):
        if self._lock or len(self.rows) == 0:
            return

        last_arrival, last_burst, last_priority = self.entries[-1]
        
        # If the user starts typing in the latest row, generate the next one
        if last_arrival.get().strip() != "" or last_burst.get().strip() != "":
            if len(self.rows) < self.max_rows:
                self._lock = True
                self.add_row()
                self._lock = False

    def get_data(self):
        data = []
        for name, arr, burst, prio in self.rows:
            a = arr.get().strip()
            b = burst.get().strip()
            p = prio.get().strip()

            if a != "" and b != "":
                priority_val = int(p) if p != "" else None
                data.append([name, int(b), int(a), priority_val])

        return data
    
    def redraw(self):
        # Left empty intentionally. 
        # With the grid+frame system, Tkinter handles the redrawing automatically!
        pass
