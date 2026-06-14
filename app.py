import tkinter as tk
from PIL import Image, ImageTk
from img_loader import get_images
from cpuschedulingv2 import scheduling_algorithm
from process_manager import ProcessTableManager


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
        btn_id = self.canvas.create_image(0, 0, anchor="nw")

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

    # ---------------- MENUS ----------------
    def create_main_menu(self): 
        self.create_button("start", "start_button", 0.4, 0.45, self.on_start, scale=0.65) 
        self.create_button("learn", "learn_button", 0.41, 0.59, lambda: None, scale=0.6) 
        self.create_button("about", "about_button", 0.41, 0.69, lambda: None, scale=0.6) 
        
    def create_select_menu(self): 
        self.create_button("back", "back_button", 0.03, 0.11, self.on_back, scale=0.6) 
        self.create_button("CPU", "CPU_sched_button", 0.05, 0.25, self.on_CPU, scale=0.8)

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
                base_y=170,
                col_x=[40, 110, 200]
            )

        if len(self.cpu_table_manager.rows) == 0:
            self.cpu_table_manager.add_row()

        # start button
        self.create_button("run_algo", "start_button", 0.15, 0.6, self.run_scheduler, scale=0.3)

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
