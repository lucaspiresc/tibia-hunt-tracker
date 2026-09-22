"""Explicit empty-slot calibration and passive equipment monitoring."""
import tkinter as tk
from tkinter import messagebox, ttk
from queue import Empty

from .presets import default_data_dir


class ScreenPanel:
    def __init__(self, parent, alerts):
        self.window = tk.Toplevel(parent)
        self.window.title("Anel e colar — leitura visual experimental")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.alerts = alerts
        self.reader = None
        self.after_id = None
        self.references = {}
        self.path = default_data_dir() / "equipment.npz"
        self.status = tk.StringVar(value="Leitura desligada.")
        ttk.Label(self.window, text="1. Deixe o slot vazio. 2. Configure sua referência. 3. Inicie e equipe o item.", wraplength=650).pack(padx=12, pady=8)
        ttk.Label(self.window, text="Ao esvaziar, avisa uma vez. Remover manualmente também avisa.\nSem leitura, aguarda reconhecer novamente um item equipado.", wraplength=650).pack(padx=12)
        ttk.Label(self.window, text="Uso no Tibia não homologado pela CipSoft; não há garantia contra punições.", wraplength=650).pack(padx=12, pady=8)
        self.combo = ttk.Combobox(self.window, state="readonly", width=42)
        self.combo.pack(padx=12, pady=8)
        self.buttons = []
        bar = ttk.Frame(self.window)
        bar.pack(padx=12, pady=8)
        for name in ("anel", "colar"):
            button = ttk.Button(bar, text=f"Configurar {name} vazio", command=lambda n=name: self.calibrate(n))
            button.pack(side="left", padx=4)
            self.buttons.append(button)
        self.start_button = ttk.Button(bar, text="Iniciar leitura", command=self.start)
        self.start_button.pack(side="left", padx=4)
        ttk.Button(bar, text="Parar", command=self.stop).pack(side="left")
        ttk.Button(self.window, text="Testar áudio", command=self.test_audio).pack()
        ttk.Label(self.window, textvariable=self.status, wraplength=650).pack(padx=12, pady=12)
        ttk.Label(self.window, text="Somente pequenos recortes de referência são salvos localmente.\nA leitura usa pixels; não controla o jogo nem consulta seus processos.", wraplength=650).pack(padx=12, pady=8)
        try:
            from .screen_reader import list_monitors
            self.monitors = list_monitors()
            self.combo.configure(values=[f"Monitor {i+1}: {m['width']} × {m['height']}" for i, m in enumerate(self.monitors)])
            if not self.monitors:
                raise RuntimeError("Nenhum monitor disponível.")
            self.combo.current(0)
            self.load_references()
        except Exception as exc:
            self.monitors = []
            self.status.set(f"Captura indisponível: {exc}")
            self.start_button.configure(state="disabled")
            for button in self.buttons:
                button.configure(state="disabled")

    def load_references(self):
        if not self.path.exists():
            return
        import numpy as np
        from .equipment import SlotReference
        try:
            with np.load(self.path, allow_pickle=False) as data:
                for name in ("anel", "colar"):
                    if name in data:
                        image, box = data[name], tuple(int(v) for v in data[name+"_box"])
                        x, y, w, h = box
                        if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
                            raise ValueError("Imagem inválida")
                        if not (0 <= x < x+w <= image.shape[1] <= 400 and 0 <= y < y+h <= image.shape[0] <= 400 and w >= 20 and h >= 20):
                            raise ValueError("Dimensões inválidas")
                        self.references[name] = SlotReference(name, image.copy(), box)
            self.status.set("Referências carregadas: " + ", ".join(self.references))
        except (OSError, ValueError, KeyError):
            self.references.clear()
            self.status.set("Referências inválidas. Configure os slots novamente.")

    def calibrate(self, name):
        self.stop()
        if self.combo.current() < 0:
            return
        if not messagebox.askokcancel("Referência do slot vazio", f"Deixe o slot de {name} VAZIO e visível no monitor selecionado.\nNa captura, arraste um retângulo justo ao redor do slot, incluindo a borda.\nMantenha as janelas do tracker fora da área do inventário.", parent=self.window):
            return
        self.window.withdraw()
        self.after_id = self.window.after(500, lambda: self.capture_reference(name))

    def capture_reference(self, name):
        self.after_id = None
        try:
            import mss
            import numpy as np
            from PIL import Image, ImageTk
            with mss.mss() as capture:
                frame = np.asarray(capture.grab(self.monitors[self.combo.current()]))[:, :, :3].copy()
            self.window.deiconify()
            dialog = tk.Toplevel(self.window)
            dialog.title(f"Marque o slot de {name} vazio — arraste incluindo a borda")
            scale = min(1., 1100/frame.shape[1], 650/frame.shape[0])
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
                from .equipment import SlotReference
                sx, sy = drag.pop("start")
                box = (round(min(sx,event.x)/scale), round(min(sy,event.y)/scale), round(abs(event.x-sx)/scale), round(abs(event.y-sy)/scale))
                try:
                    reference = SlotReference.capture(name, frame, box)
                    refs = dict(self.references, **{name: reference})
                    payload = {}
                    for key, ref in refs.items():
                        payload[key], payload[key+"_box"] = ref.image, np.array(ref.box)
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    temporary = self.path.with_suffix(".tmp")
                    with temporary.open("wb") as output:
                        np.savez_compressed(output, **payload)
                    temporary.replace(self.path)
                    self.references = refs
                except (ValueError, OSError) as exc:
                    messagebox.showerror("Referência não salva", str(exc), parent=dialog)
                    return
                dialog.destroy()
                self.status.set(f"{name.capitalize()} configurado. Pode iniciar a leitura e equipar o item.")

            canvas.bind("<ButtonPress-1>", down)
            canvas.bind("<B1-Motion>", move)
            canvas.bind("<ButtonRelease-1>", up)
            dialog.transient(self.window)
            dialog.grab_set()
        except Exception as exc:
            self.window.deiconify()
            self.status.set(f"Não foi possível capturar: {exc}")

    def test_audio(self):
        self.alerts.equipment_empty("anel")
        self.alerts.equipment_empty("colar")

    def start(self):
        if self.reader is not None or self.combo.current() < 0:
            return
        if not self.references:
            self.status.set("Configure pelo menos um slot vazio antes de iniciar.")
            return
        from .screen_reader import ScreenReader
        self.alerts.prepare_equipment()
        self.reader = ScreenReader(self.monitors[self.combo.current()], list(self.references.values()))
        self.reader.start()
        self.combo.configure(state="disabled")
        self.start_button.configure(state="disabled")
        for button in self.buttons:
            button.configure(state="disabled")
        self.status.set("Procurando os slots configurados…")
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
            for button in self.buttons:
                button.configure(state="normal")
        self.status.set("Leitura desligada.")

    def close(self):
        self.stop()
        self.window.destroy()
