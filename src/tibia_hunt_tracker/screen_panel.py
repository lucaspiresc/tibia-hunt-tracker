"""User-selected inventory region; screen images stay in memory."""
import tkinter as tk
from tkinter import ttk
from queue import Empty
from .inventory_area import capture_area, load_area, save_area


class ScreenPanel:
    def __init__(self, parent, alerts):
        self.window = tk.Toplevel(parent)
        self.window.title("Anel e colar — área do inventário")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.alerts = alerts
        self.reader = None
        self.after_id = None
        self.area = None
        self.area_status = tk.StringVar(value="Nenhuma área selecionada.")
        self.status = tk.StringVar(value="Leitura desligada.")
        ttk.Label(self.window, text="Selecione o monitor e marque a área do inventário.\nA leitura acompanha somente essa área. Se mover o inventário, selecione novamente.", wraplength=650).pack(padx=12, pady=8)
        ttk.Label(self.window, text="Ao esvaziar, avisa uma vez. Remover manualmente também avisa.\nSem leitura, aguarda reconhecer novamente um item equipado.", wraplength=650).pack(padx=12)
        ttk.Label(self.window, text="Referência: inventário cinza do manual oficial. Outras aparências podem não ser reconhecidas.\nUso não homologado pela CipSoft; não há garantia contra punições.", wraplength=650).pack(padx=12, pady=8)
        self.combo = ttk.Combobox(self.window, state="readonly", width=42)
        self.combo.pack(padx=12, pady=8)
        self.combo.bind("<<ComboboxSelected>>", self.monitor_changed)
        self.select_button = ttk.Button(self.window, text="Selecionar área do inventário", command=self.select_area)
        self.select_button.pack(pady=4)
        ttk.Label(self.window, textvariable=self.area_status, wraplength=650).pack(padx=12)
        bar = ttk.Frame(self.window)
        bar.pack(padx=12, pady=8)
        self.start_button = ttk.Button(bar, text="Iniciar leitura", command=self.start)
        self.start_button.pack(side="left", padx=4)
        ttk.Button(bar, text="Parar", command=self.stop).pack(side="left")
        ttk.Button(bar, text="Testar áudio", command=self.test_audio).pack(side="left", padx=4)
        ttk.Label(self.window, textvariable=self.status, wraplength=650).pack(padx=12, pady=12)
        ttk.Label(self.window, text="Capturas ficam somente em memória. Não há comandos ao jogo.\nMantenha o tracker fora da área do inventário.", wraplength=650).pack(padx=12, pady=8)
        try:
            from .screen_reader import list_monitors
            self.monitors = list_monitors()
            self.combo.configure(values=[f"Monitor {i+1}: {m['width']} × {m['height']}" for i, m in enumerate(self.monitors)])
            if not self.monitors:
                raise RuntimeError("Nenhum monitor disponível.")
            self.combo.current(0)
            self.monitor_changed()
        except Exception as exc:
            self.monitors = []
            self.status.set(f"Captura indisponível: {exc}")
            self.start_button.configure(state="disabled")
            self.select_button.configure(state="disabled")

    def monitor_changed(self, _event=None):
        self.stop()
        self.area = load_area(self.monitors[self.combo.current()])
        self.describe_area()

    def describe_area(self):
        if self.area:
            x, y, w, h = self.area
            self.area_status.set(f"Área salva: {w} × {h}, posição {x}, {y} neste monitor.")
        else:
            self.area_status.set("Nenhuma área selecionada. Marque o inventário antes de iniciar.")

    def select_area(self):
        self.stop()
        if self.combo.current() < 0:
            return
        self.window.withdraw()
        self.after_id = self.window.after(400, self.capture_selection)

    def capture_selection(self):
        self.after_id = None
        try:
            import mss
            import numpy as np
            from PIL import Image, ImageTk
            monitor = self.monitors[self.combo.current()]
            with mss.mss() as capture:
                frame = np.asarray(capture.grab(monitor))[:, :, :3].copy()
            self.window.deiconify()
            dialog = tk.Toplevel(self.window)
            dialog.title("Arraste ao redor de TODO o inventário — Esc cancela")
            hint = tk.StringVar(value="Inclua os slots, bordas e botões superiores. Pode deixar uma pequena margem.")
            ttk.Label(dialog, textvariable=hint).pack(padx=8, pady=8)
            width = min(1100, dialog.winfo_screenwidth()-60)
            height = min(650, dialog.winfo_screenheight()-140)
            scale = min(1., width/frame.shape[1], height/frame.shape[0])
            photo = ImageTk.PhotoImage(Image.fromarray(frame[:, :, ::-1]).resize((round(frame.shape[1]*scale), round(frame.shape[0]*scale))))
            canvas = tk.Canvas(dialog, width=photo.width(), height=photo.height(), highlightthickness=0)
            canvas.pack()
            canvas.create_image(0, 0, image=photo, anchor="nw")
            canvas.photo = photo
            drag = {}

            def down(event):
                canvas.delete("selection")
                drag["start"] = (event.x, event.y)

            def move(event):
                if "start" in drag:
                    canvas.delete("selection")
                    canvas.create_rectangle(*drag["start"], event.x, event.y, outline="yellow", width=2, tags="selection")

            def up(event):
                if "start" not in drag:
                    return
                sx, sy = drag.pop("start")
                ex = max(0, min(photo.width(), event.x))
                ey = max(0, min(photo.height(), event.y))
                box = (round(min(sx,ex)/scale), round(min(sy,ey)/scale), round(abs(ex-sx)/scale), round(abs(ey-sy)/scale))
                try:
                    save_area(monitor, box)
                except (ValueError, OSError) as exc:
                    hint.set(str(exc))
                    return
                self.area = box
                self.describe_area()
                self.status.set("Área selecionada. Clique em Iniciar leitura.")
                dialog.destroy()

            canvas.bind("<ButtonPress-1>", down)
            canvas.bind("<B1-Motion>", move)
            canvas.bind("<ButtonRelease-1>", up)
            dialog.bind("<Escape>", lambda _event: dialog.destroy())
            dialog.transient(self.window)
            dialog.grab_set()
            dialog.focus_set()
        except Exception as exc:
            self.window.deiconify()
            self.status.set(f"Não foi possível selecionar a área: {exc}")

    def test_audio(self):
        self.alerts.equipment_empty("anel")
        self.alerts.equipment_empty("colar")

    def start(self):
        if self.reader is not None or self.combo.current() < 0:
            return
        if self.area is None:
            self.status.set("Selecione a área do inventário antes de iniciar.")
            return
        from .screen_reader import ScreenReader
        self.alerts.prepare_equipment()
        self.reader = ScreenReader(capture_area(self.monitors[self.combo.current()], self.area))
        self.reader.start()
        self.combo.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.status.set("Lendo a área selecionada…")
        self.poll()

    def poll(self):
        if self.reader is None:
            return
        result = self.reader.poll()
        if result:
            if result.status.startswith("Leitura interrompida:"):
                self.stop()
                self.status.set(result.status)
                return
            self.status.set(f"{result.status} | processamento: {result.elapsed_ms:.0f} ms")
        try:
            while True:
                self.alerts.equipment_empty(self.reader.events.get_nowait())
        except Empty:
            pass
        self.after_id = self.window.after(200, self.poll)

    def stop(self):
        if self.after_id is not None:
            self.window.after_cancel(self.after_id)
            self.after_id = None
        if self.reader:
            self.reader.stop()
            self.reader = None
        self.combo.configure(state="readonly")
        if getattr(self, "monitors", []):
            self.start_button.configure(state="normal")
        self.status.set("Leitura desligada.")

    def close(self):
        self.stop()
        self.window.destroy()
