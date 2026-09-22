"""Passive equipment monitoring. No user calibration or screen image storage."""
import tkinter as tk
from tkinter import ttk
from queue import Empty


class ScreenPanel:
    def __init__(self, parent, alerts):
        self.window = tk.Toplevel(parent)
        self.window.title("Anel e colar — leitura automática experimental")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.alerts = alerts
        self.reader = None
        self.after_id = None
        self.status = tk.StringVar(value="Leitura desligada.")
        ttk.Label(self.window, text="Deixe o inventário visível, selecione o monitor e inicie.\nOs slots são localizados automaticamente, mesmo já equipados.", wraplength=650).pack(padx=12, pady=8)
        ttk.Label(self.window, text="Ao esvaziar, avisa uma vez. Remover manualmente também avisa.\nSem leitura, aguarda reconhecer novamente um item equipado.", wraplength=650).pack(padx=12)
        ttk.Label(self.window, text="Referência: inventário cinza do manual oficial. Outras aparências podem não ser reconhecidas.\nUso não homologado pela CipSoft; não há garantia contra punições.", wraplength=650).pack(padx=12, pady=8)
        self.combo = ttk.Combobox(self.window, state="readonly", width=42)
        self.combo.pack(padx=12, pady=8)
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
        except Exception as exc:
            self.monitors = []
            self.status.set(f"Captura indisponível: {exc}")
            self.start_button.configure(state="disabled")

    def test_audio(self):
        self.alerts.equipment_empty("anel")
        self.alerts.equipment_empty("colar")

    def start(self):
        if self.reader is not None or self.combo.current() < 0:
            return
        from .screen_reader import ScreenReader
        self.alerts.prepare_equipment()
        self.reader = ScreenReader(self.monitors[self.combo.current()])
        self.reader.start()
        self.combo.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.status.set("Procurando inventário…")
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
