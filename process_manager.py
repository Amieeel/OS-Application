import tkinter as tk

class ProcessTableManager:
    def __init__(self, canvas, parent, base_x, base_y, col_x):
        self.canvas = canvas
        self.parent = parent

        self.base_x = base_x
        self.base_y = base_y
        self.col_x = col_x

        self.rows = []
        self.entries = []

        self.process_count = 0
        self.max_rows = 10

        self._lock = False  # prevents spam row creation

        # IMPORTANT: start with first row immediately
        self.add_row()

    # ---------------- numeric validation ----------------
    def validate_number(self, value_if_allowed):
        return value_if_allowed == "" or value_if_allowed.isdigit()

    # ---------------- create row ----------------
    def add_row(self):
        if self.process_count >= self.max_rows:
            return

        row_index = self.process_count
        self.process_count += 1

        process_name = f"P{row_index + 1}"

        # label
        self.canvas.create_text(
            self.base_x + self.col_x[0],
            self.base_y + 40 + row_index * 30,
            text=process_name,
            font=("Arial", 11),
            fill="black",
            tags="ui"
        )

        vcmd = (self.parent.register(self.validate_number), "%P")

        arrival = tk.Entry(
            self.parent,
            width=10,
            font=("Arial", 11),
            validate="key",
            validatecommand=vcmd
        )

        burst = tk.Entry(
            self.parent,
            width=10,
            font=("Arial", 11),
            validate="key",
            validatecommand=vcmd
        )

        self.canvas.create_window(
            self.base_x + self.col_x[1],
            self.base_y + 40 + row_index * 30,
            window=arrival,
            tags="ui"
        )

        self.canvas.create_window(
            self.base_x + self.col_x[2],
            self.base_y + 40 + row_index * 30,
            window=burst,
            tags="ui"
        )

        self.rows.append((process_name, arrival, burst))
        self.entries.append((arrival, burst))

        # safe trigger (NOT spammy)
        arrival.bind("<KeyRelease>", lambda e: self.smart_add_row())
        burst.bind("<KeyRelease>", lambda e: self.smart_add_row())

    # ---------------- auto add logic ----------------
    def smart_add_row(self):
        if self._lock:
            return

        if len(self.rows) == 0:
            return

        last_arrival, last_burst = self.entries[-1]

        if last_arrival.get().strip() != "" or last_burst.get().strip() != "":
            if len(self.rows) < self.max_rows:
                self._lock = True
                self.add_row()
                self._lock = False

    # ---------------- get data ----------------
    def get_data(self):
        data = []

        for name, arr, burst in self.rows:
            a = arr.get().strip()
            b = burst.get().strip()

            if a != "" and b != "":
                data.append([name, int(a), int(b)])

        return data
    
    def redraw(self):
        for i, (name, arr, burst) in enumerate(self.rows):
            y = self.base_y + 40 + i * 30

            self.canvas.coords(
                self.canvas.find_withtag("ui")[0],
                self.base_x,
                y
            )