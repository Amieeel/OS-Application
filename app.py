import tkinter as tk
from PIL import Image, ImageTk
from img_loader import get_images
from cpuschedulingv2 import scheduling_algorithm


class App(tk.Tk):
    DESIGN_W = 1920
    DESIGN_H = 1080

    def __init__(self):
        super().__init__()

        self.title("Go Rhythm")
        self.geometry("1420x780")

        # assets
        self.imgs = get_images()

        # canvas
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # background
        self.bg_id = None
        self.bg_tk = None
        self.bg_name = "home"

        # UI state
        self.scale = 1
        self.updating_ui = False
        self.buttons = {}

        # scheduler 
        self.scheduler = None

        self.bind("<Configure>", self.on_resize)

        self.set_background("home")
        self.create_main_menu()

    # ---------------- SCALE ----------------
    def update_scale(self):
        self.scale = min(
            self.winfo_width() / self.DESIGN_W,
            self.winfo_height() / self.DESIGN_H
        )

    # ---------------- SCREEN SWITCH ----------------
    def switch_screen(self, bg, builder):
        self.updating_ui = True
        self.clear_buttons()
        self.canvas.delete("ui")  
        self.set_background(bg)
        builder()
        self.updating_ui = False
        self.render_buttons()

    # ---------------- BACKGROUND ----------------
    def set_background(self, name):
        self.bg_name = name
        self.render_background()

    def render_background(self):
        w, h = self.winfo_width(), self.winfo_height()

        img = self.imgs[self.bg_name].resize((w, h), Image.Resampling.LANCZOS)

        self.bg_tk = ImageTk.PhotoImage(img)

        if self.bg_id is None:
            self.bg_id = self.canvas.create_image(
                0, 0, anchor="nw", image=self.bg_tk
            )
        else:
            self.canvas.itemconfig(self.bg_id, image=self.bg_tk)

    # ---------------- RESIZE ----------------
    def on_resize(self, event):
        if event.widget != self:
            return

        self.update_scale()
        self.render_background()
        self.render_buttons()

    # ---------------- BUTTON SYSTEM ----------------
    def create_button(self, name, img_name, rx, ry, command):
        btn_id = self.canvas.create_image(0, 0, anchor="nw")

        self.canvas.tag_bind(btn_id, "<Button-1>", lambda e: command())

        self.buttons[name] = {
            "img": self.imgs[img_name],
            "id": btn_id,
            "pos": (rx, ry),
            "tk": None
        }

    def clear_buttons(self):
        for b in self.buttons.values():
            self.canvas.delete(b["id"])
        self.buttons.clear()

    # ---------------- BUTTON RENDER ----------------
    def render_buttons(self):
        if self.updating_ui or not self.buttons:
            return

        w, h = self.winfo_width(), self.winfo_height()

        for b in self.buttons.values():
            img = b["img"]

            x = int(b["pos"][0] * w)
            y = int(b["pos"][1] * h)

            size = (
                int(img.width * self.scale),
                int(img.height * self.scale)
            )

            tk_img = ImageTk.PhotoImage(
                img.resize(size, Image.Resampling.LANCZOS)
            )

            b["tk"] = tk_img

            self.canvas.itemconfig(b["id"], image=tk_img)
            self.canvas.coords(b["id"], x, y)

    # ---------------- ACTIONS ----------------
    def on_start(self):
        self.switch_screen("select", self.create_select_menu)

    def on_back(self):
        self.switch_screen("home", self.create_main_menu)

    def on_CPU(self):
        self.switch_screen("cpu_bg", self.create_cpu_view)

    def on_learn(self): pass
    def on_about(self): pass
    def on_MAIN(self): pass
    def on_VIRT(self): pass
    def on_DISK(self): pass

    # ---------------- MENUS ----------------
    def create_main_menu(self):
        self.create_button("start", "start_button", 0.4, 0.45, self.on_start)
        self.create_button("learn", "learn_button", 0.41, 0.59, self.on_learn)
        self.create_button("about", "about_button", 0.41, 0.69, self.on_about)

    def create_select_menu(self):
        self.create_button("back", "back_button", 0.01, 0.1, self.on_back)
        self.create_button("CPU", "CPU_sched_button", 0.049, 0.25, self.on_CPU)
        self.create_button("MAIN", "Main_mem_button", 0.28, 0.25, self.on_MAIN)
        self.create_button("VIRT", "Virt_mem_button", 0.52, 0.25, self.on_VIRT)
        self.create_button("DISK", "Disk_sched_button", 0.75, 0.25, self.on_DISK)

    # ---------------- CPU VIEW ----------------
    def create_cpu_view(self):
        if self.scheduler is None:
            self.scheduler = scheduling_algorithm([
                ["P1", 5, 0, 3],
                ["P2", 3, 2, 1],
                ["P3", 8, 4, 2],
                ["P4", 6, 6, 4],
            ])

        result = self.scheduler.NonPreemptivePriority()

        w = self.winfo_width()
        x = w // 2


        # FORMULAS
        self.canvas.create_text(
            x, 120,
            text="TAT = Completion Time - Arrival Time | WT = TAT - Burst Time",
            font=("Arial", 14),
            fill="lightgray",
            tags="ui"
        )

        # TABLE
        table = "PROCESS   TAT   WT\n-------------------\n"
        for i in range(len(result["process"])):
            table += f"{result['process'][i]}     {result['tat'][i]}     {result['wt'][i]}\n"

        self.canvas.create_text(
            x, 250,
            text=table,
            font=("Courier", 14),
            fill="white",
            tags="ui"
        )

        # AVERAGES
        avg = f"AVG TAT: {result['avg_tat']:.2f} ms | AVG WT: {result['avg_wt']:.2f} ms"

        self.canvas.create_text(
            x, 400,
            text=avg,
            font=("Arial", 16, "bold"),
            fill="yellow",
            tags="ui"
        )

        # GANTT CHART
        start_x = 500
        y = 200

        for p in result["process"]:
            self.canvas.create_rectangle(
                start_x, y,
                start_x + 80, y + 40,
                fill="white",
                tags="ui"
            )

            self.canvas.create_text(
                start_x + 40, y + 20,
                text=p,
                fill="black",
                tags="ui"
            )

            start_x += 80


if __name__ == "__main__":
    App().mainloop()