from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from .alerts import AlertDispatcher
from .catalog import load_catalog
from .models import CatalogEntry, TimerConfig
from .presets import PresetStore
from .timer_engine import EventKind, TimerEngine


BG = "#101318"
PANEL = "#171c24"
PANEL_2 = "#202733"
TEXT = "#eef2f7"
MUTED = "#9aa6b5"
ACCENT = "#5ec4ff"
WARNING = "#ffbf47"
DANGER = "#ff667a"
SUCCESS = "#5bd6a2"


def format_seconds(value: float | int) -> str:
    seconds = max(0, int(math.ceil(value)))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def parse_duration(value: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError("Informe uma duração.")
    parts = text.split(":")
    if len(parts) > 3 or any(not part.isdigit() for part in parts):
        raise ValueError("Use segundos, MM:SS ou HH:MM:SS.")
    numbers = [int(part) for part in parts]
    if len(numbers) == 1:
        total = numbers[0]
    elif len(numbers) == 2:
        total = numbers[0] * 60 + numbers[1]
    else:
        total = numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    if total <= 0:
        raise ValueError("A duração deve ser maior que zero.")
    return total


class HuntTrackerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tibia Hunt Tracker")
        self.root.geometry("1040x760")
        self.root.minsize(760, 560)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.catalog = load_catalog()
        self.catalog_by_id = {entry.id: entry for entry in self.catalog}
        self.configs: dict[str, TimerConfig] = {}
        self.engine = TimerEngine()
        self.alerts = AlertDispatcher()
        self.presets = PresetStore()
        self.current_preset = self.presets.names[0]
        self.timer_widgets: dict[str, dict[str, tk.Widget]] = {}

        self.search_var = tk.StringVar()
        self.preset_var = tk.StringVar(value=self.current_preset)
        self.duration_var = tk.StringVar()
        self.warning_var = tk.StringVar()
        self.voice_label_var = tk.StringVar()
        self.audio_var = tk.BooleanVar(value=True)
        self.topmost_var = tk.BooleanVar(value=True)
        self.compact_var = tk.BooleanVar(value=False)
        self.hunt_time_var = tk.StringVar(value="Hunt 00:00")
        self.status_var = tk.StringVar(value="Configure os timers e inicie a hunt.")

        self._configure_style()
        self._build_ui()
        self._refresh_presets()
        self._load_preset(self.current_preset)
        self._refresh_catalog()
        self._apply_topmost()
        self.root.after(200, self._tick)

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Card.TFrame", background=PANEL_2)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 18))
        style.configure("Clock.TLabel", background=BG, foreground=ACCENT, font=("Consolas", 15, "bold"))
        style.configure("TimerName.TLabel", background=PANEL_2, foreground=TEXT, font=("Segoe UI Semibold", 10))
        style.configure("TimerClock.TLabel", background=PANEL_2, foreground=ACCENT, font=("Consolas", 13, "bold"))
        style.configure("TButton", font=("Segoe UI Semibold", 9), padding=(10, 6))
        style.configure("Accent.TButton", background=ACCENT, foreground="#081017")
        style.map("Accent.TButton", background=[("active", "#8ed7ff"), ("disabled", "#40505c")])
        style.configure("Danger.TButton", background=DANGER, foreground="#ffffff")
        style.map("Danger.TButton", background=[("active", "#ff8d9c")])
        style.configure("Treeview", background=PANEL_2, fieldbackground=PANEL_2, foreground=TEXT, rowheight=27, borderwidth=0)
        style.configure("Treeview.Heading", background="#293242", foreground=TEXT, font=("Segoe UI Semibold", 9))
        style.map("Treeview", background=[("selected", "#244b66")])
        style.configure("Horizontal.TProgressbar", troughcolor="#303947", background=ACCENT, bordercolor="#303947")
        style.configure("TCheckbutton", background=BG, foreground=TEXT)
        style.map("TCheckbutton", background=[("active", BG)], foreground=[("disabled", MUTED)])

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=1)

        header = ttk.Frame(self.root, padding=(18, 14, 18, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ttk.Label(header, text="Tibia Hunt Tracker", style="Title.TLabel").grid(row=0, column=0, sticky="w")

        preset_bar = ttk.Frame(header)
        preset_bar.grid(row=0, column=1, sticky="e")
        ttk.Label(preset_bar, text="Preset:").pack(side="left", padx=(0, 6))
        self.preset_combo = ttk.Combobox(preset_bar, textvariable=self.preset_var, width=20, state="readonly")
        self.preset_combo.pack(side="left")
        self.preset_combo.bind("<<ComboboxSelected>>", self._preset_selected)
        ttk.Button(preset_bar, text="Novo", command=self._new_preset).pack(side="left", padx=(6, 2))
        ttk.Button(preset_bar, text="Salvar", command=self._save_preset).pack(side="left", padx=2)
        ttk.Button(preset_bar, text="Duplicar", command=self._duplicate_preset).pack(side="left", padx=2)
        ttk.Button(preset_bar, text="Excluir", command=self._delete_preset).pack(side="left", padx=2)

        toggles = ttk.Frame(self.root, padding=(18, 0, 18, 8))
        toggles.grid(row=1, column=0, sticky="ew")
        ttk.Checkbutton(toggles, text="Sempre visível", variable=self.topmost_var, command=self._apply_topmost).pack(side="left")
        ttk.Checkbutton(toggles, text="Modo compacto", variable=self.compact_var, command=self._apply_compact).pack(side="left", padx=(14, 0))
        ttk.Label(toggles, textvariable=self.status_var, style="Muted.TLabel").pack(side="right")

        self.config_panel = ttk.Frame(self.root, style="Panel.TFrame", padding=14)
        self.config_panel.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 10))
        self.config_panel.grid_columnconfigure(0, weight=1)
        self.config_panel.grid_columnconfigure(1, weight=1)
        self.config_panel.grid_rowconfigure(1, weight=1)

        ttk.Label(self.config_panel, text="Itens e spells", style="Panel.TLabel", font=("Segoe UI Semibold", 12)).grid(row=0, column=0, sticky="w")
        ttk.Label(self.config_panel, text="Timers selecionados", style="Panel.TLabel", font=("Segoe UI Semibold", 12)).grid(row=0, column=1, sticky="w", padx=(14, 0))

        catalog_box = ttk.Frame(self.config_panel, style="Panel.TFrame")
        catalog_box.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        catalog_box.grid_columnconfigure(0, weight=1)
        catalog_box.grid_rowconfigure(1, weight=1)
        search_entry = ttk.Entry(catalog_box, textvariable=self.search_var)
        search_entry.grid(row=0, column=0, sticky="ew", pady=(0, 7))
        search_entry.bind("<KeyRelease>", lambda _event: self._refresh_catalog())
        self.catalog_tree = ttk.Treeview(catalog_box, columns=("type", "duration"), show="tree headings", selectmode="browse")
        self.catalog_tree.heading("#0", text="Nome")
        self.catalog_tree.heading("type", text="Tipo")
        self.catalog_tree.heading("duration", text="Duração")
        self.catalog_tree.column("#0", width=255)
        self.catalog_tree.column("type", width=70, anchor="center")
        self.catalog_tree.column("duration", width=80, anchor="center")
        self.catalog_tree.grid(row=1, column=0, sticky="nsew")
        self.catalog_tree.bind("<Double-1>", lambda _event: self._add_catalog_selection())
        catalog_scroll = ttk.Scrollbar(catalog_box, orient="vertical", command=self.catalog_tree.yview)
        catalog_scroll.grid(row=1, column=1, sticky="ns")
        self.catalog_tree.configure(yscrollcommand=catalog_scroll.set)
        ttk.Button(catalog_box, text="Adicionar →", style="Accent.TButton", command=self._add_catalog_selection).grid(row=2, column=0, sticky="e", pady=(8, 0))

        active_box = ttk.Frame(self.config_panel, style="Panel.TFrame")
        active_box.grid(row=1, column=1, sticky="nsew", padx=(14, 0), pady=(8, 0))
        active_box.grid_columnconfigure(0, weight=1)
        active_box.grid_rowconfigure(0, weight=1)
        self.active_tree = ttk.Treeview(active_box, columns=("duration", "warning"), show="tree headings", selectmode="browse")
        self.active_tree.heading("#0", text="Nome")
        self.active_tree.heading("duration", text="Duração")
        self.active_tree.heading("warning", text="Aviso")
        self.active_tree.column("#0", width=230)
        self.active_tree.column("duration", width=82, anchor="center")
        self.active_tree.column("warning", width=72, anchor="center")
        self.active_tree.grid(row=0, column=0, sticky="nsew", columnspan=4)
        self.active_tree.bind("<<TreeviewSelect>>", self._active_selected)
        self.active_tree.bind("<Double-1>", self._active_double_click)
        active_scroll = ttk.Scrollbar(active_box, orient="vertical", command=self.active_tree.yview)
        active_scroll.grid(row=0, column=4, sticky="ns")
        self.active_tree.configure(yscrollcommand=active_scroll.set)

        edit = ttk.Frame(active_box, style="Panel.TFrame")
        edit.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        ttk.Label(edit, text="Duração", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(edit, textvariable=self.duration_var, width=10).grid(row=1, column=0, sticky="w")
        ttk.Label(edit, text="Avisar antes (s)", style="Panel.TLabel").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Entry(edit, textvariable=self.warning_var, width=9).grid(row=1, column=1, sticky="w", padx=(10, 0))
        ttk.Label(edit, text="Texto falado", style="Panel.TLabel").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Entry(edit, textvariable=self.voice_label_var, width=24).grid(row=1, column=2, sticky="ew", padx=(10, 0))
        ttk.Checkbutton(edit, text="Áudio falado", variable=self.audio_var).grid(row=1, column=3, padx=(12, 0))
        ttk.Button(edit, text="Aplicar", command=self._apply_timer_edit).grid(row=1, column=4, padx=(12, 2))
        ttk.Button(edit, text="Remover", command=self._remove_selected_timer).grid(row=1, column=5, padx=2)

        lower = ttk.Frame(self.root, padding=(18, 0, 18, 10))
        lower.grid(row=3, column=0, sticky="nsew")
        lower.grid_columnconfigure(0, weight=1)
        lower.grid_rowconfigure(1, weight=1)
        huntbar = ttk.Frame(lower)
        huntbar.grid(row=0, column=0, sticky="ew", pady=(0, 9))
        self.start_button = ttk.Button(huntbar, text="INICIAR HUNT", style="Accent.TButton", command=self._start_hunt)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(huntbar, text="TERMINAR HUNT", style="Danger.TButton", command=self._stop_hunt, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))
        ttk.Label(huntbar, textvariable=self.hunt_time_var, style="Clock.TLabel").pack(side="right")

        timer_outer = ttk.Frame(lower, style="Panel.TFrame")
        timer_outer.grid(row=1, column=0, sticky="nsew")
        timer_outer.grid_columnconfigure(0, weight=1)
        timer_outer.grid_rowconfigure(0, weight=1)
        self.timer_canvas = tk.Canvas(timer_outer, bg=PANEL, highlightthickness=0)
        self.timer_canvas.grid(row=0, column=0, sticky="nsew")
        timer_scroll = ttk.Scrollbar(timer_outer, orient="vertical", command=self.timer_canvas.yview)
        timer_scroll.grid(row=0, column=1, sticky="ns")
        self.timer_canvas.configure(yscrollcommand=timer_scroll.set)
        self.timer_list = ttk.Frame(self.timer_canvas, style="Panel.TFrame", padding=10)
        self.timer_window = self.timer_canvas.create_window((0, 0), window=self.timer_list, anchor="nw")
        self.timer_list.bind("<Configure>", lambda _event: self.timer_canvas.configure(scrollregion=self.timer_canvas.bbox("all")))
        self.timer_canvas.bind("<Configure>", lambda event: self.timer_canvas.itemconfigure(self.timer_window, width=event.width))

    def _refresh_catalog(self) -> None:
        query = self.search_var.get().strip().casefold()
        selected = set(self.configs)
        self.catalog_tree.delete(*self.catalog_tree.get_children())
        for entry in self.catalog:
            searchable = " ".join((entry.name, entry.words or "", entry.entity_type)).casefold()
            if entry.id in selected or (query and query not in searchable):
                continue
            item_type = "Spell" if entry.entity_type == "spell" else "Item"
            label = entry.name if not entry.words else f"{entry.name} ({entry.words})"
            self.catalog_tree.insert("", "end", iid=entry.id, text=label, values=(item_type, format_seconds(entry.duration_seconds)))

    def _add_catalog_selection(self) -> None:
        if self._configuration_locked():
            return
        selection = self.catalog_tree.selection()
        if not selection:
            return
        entry = self.catalog_by_id[selection[0]]
        self.configs[entry.id] = TimerConfig(
            catalog_id=entry.id,
            name=entry.name,
            voice_label=entry.voice_label,
            duration_seconds=entry.duration_seconds,
            warning_seconds=entry.default_warning_seconds,
        )
        self._refresh_all_timer_views(select_id=entry.id)
        self.status_var.set(f"{entry.name} adicionado.")

    def _refresh_active_tree(self, select_id: str | None = None) -> None:
        self.active_tree.delete(*self.active_tree.get_children())
        for config in self.configs.values():
            self.active_tree.insert(
                "", "end", iid=config.catalog_id, text=config.name,
                values=(format_seconds(config.duration_seconds), f"{config.warning_seconds}s"),
            )
        if select_id and self.active_tree.exists(select_id):
            self.active_tree.selection_set(select_id)
            self.active_tree.focus(select_id)
            self._populate_editor(select_id)

    def _active_selected(self, _event: tk.Event | None = None) -> None:
        selection = self.active_tree.selection()
        if selection:
            self._populate_editor(selection[0])

    def _populate_editor(self, timer_id: str) -> None:
        config = self.configs[timer_id]
        self.duration_var.set(format_seconds(config.duration_seconds))
        self.warning_var.set(str(config.warning_seconds))
        self.voice_label_var.set(config.voice_label)
        self.audio_var.set(config.audio_enabled)

    def _apply_timer_edit(self) -> None:
        if self._configuration_locked():
            return
        selection = self.active_tree.selection()
        if not selection:
            return
        timer_id = selection[0]
        old = self.configs[timer_id]
        try:
            duration = parse_duration(self.duration_var.get())
            warning = int(self.warning_var.get().strip())
            updated = TimerConfig(
                catalog_id=old.catalog_id,
                name=old.name,
                voice_label=self.voice_label_var.get().strip() or old.name,
                duration_seconds=duration,
                warning_seconds=warning,
                audio_enabled=self.audio_var.get(),
            )
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Configuração inválida", str(exc), parent=self.root)
            return
        self.configs[timer_id] = updated
        self._refresh_all_timer_views(select_id=timer_id)
        self.status_var.set(f"Configuração de {updated.name} atualizada.")

    def _remove_selected_timer(self) -> None:
        if self._configuration_locked():
            return
        selection = self.active_tree.selection()
        if not selection:
            return
        timer_id = selection[0]
        name = self.configs[timer_id].name
        self.configs.pop(timer_id)
        self._refresh_all_timer_views()
        self.status_var.set(f"{name} removido.")

    def _refresh_all_timer_views(self, select_id: str | None = None) -> None:
        self._refresh_catalog()
        self._refresh_active_tree(select_id)
        self._rebuild_timer_cards()

    def _rebuild_timer_cards(self) -> None:
        for child in self.timer_list.winfo_children():
            child.destroy()
        self.timer_widgets.clear()
        if not self.configs:
            ttk.Label(self.timer_list, text="Nenhum timer selecionado.", style="Panel.TLabel").pack(pady=24)
            return
        for config in self.configs.values():
            card = ttk.Frame(self.timer_list, style="Card.TFrame", padding=(12, 9))
            card.pack(fill="x", pady=4)
            card.grid_columnconfigure(1, weight=1)
            name = ttk.Label(card, text=config.name, style="TimerName.TLabel")
            name.grid(row=0, column=0, sticky="w", padx=(0, 14))
            progress = ttk.Progressbar(card, maximum=config.duration_seconds, value=config.duration_seconds)
            progress.grid(row=0, column=1, sticky="ew", padx=(0, 14))
            clock = ttk.Label(card, text=format_seconds(config.duration_seconds), style="TimerClock.TLabel", width=9, anchor="e")
            clock.grid(row=0, column=2, sticky="e")
            reset = ttk.Button(card, text="↻", width=3, command=lambda timer_id=config.catalog_id: self._manual_reset(timer_id))
            reset.grid(row=0, column=3, padx=(8, 0))
            for widget in (card, name, clock):
                widget.bind("<Double-1>", lambda _event, timer_id=config.catalog_id: self._manual_reset(timer_id))
            self.timer_widgets[config.catalog_id] = {"clock": clock, "progress": progress}

    def _start_hunt(self) -> None:
        if not self.configs:
            messagebox.showwarning("Sem timers", "Adicione pelo menos um item ou spell.", parent=self.root)
            return
        self.presets.save(self.current_preset, list(self.configs.values()))
        self.alerts.prepare(self.configs.values())
        self.engine.start(list(self.configs.values()))
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Hunt em andamento. Duplo clique reinicia um timer.")
        if self.compact_var.get():
            self._apply_compact()

    def _stop_hunt(self) -> None:
        self.engine.stop()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.hunt_time_var.set("Hunt 00:00")
        self.status_var.set("Hunt finalizada.")
        self._update_timer_cards()

    def _manual_reset(self, timer_id: str) -> None:
        if not self.engine.running:
            return
        try:
            self.engine.reset(timer_id)
        except KeyError:
            return
        self.status_var.set(f"{self.configs[timer_id].name} reiniciado manualmente.")
        self._update_timer_cards()

    def _active_double_click(self, _event: tk.Event) -> None:
        selection = self.active_tree.selection()
        if selection:
            self._manual_reset(selection[0])

    def _tick(self) -> None:
        if self.engine.running:
            for event in self.engine.tick():
                self.alerts.dispatch(event)
                if event.kind is EventKind.WARNING:
                    self.status_var.set(f"{event.config.name}: faltam {event.config.warning_seconds}s.")
                else:
                    self.status_var.set(f"{event.config.name}: renove agora. Timer reiniciado.")
            self.hunt_time_var.set(f"Hunt {format_seconds(self.engine.elapsed())}")
        self._update_timer_cards()
        self.root.after(200, self._tick)

    def _update_timer_cards(self) -> None:
        for timer_id, widgets in self.timer_widgets.items():
            config = self.configs[timer_id]
            remaining = self.engine.remaining(timer_id) if self.engine.running and timer_id in self.engine.timer_ids else config.duration_seconds
            widgets["clock"].configure(text=format_seconds(remaining))
            widgets["progress"].configure(maximum=config.duration_seconds, value=remaining)

    def _refresh_presets(self) -> None:
        self.preset_combo.configure(values=self.presets.names)
        if self.current_preset not in self.presets.names:
            self.current_preset = self.presets.names[0]
        self.preset_var.set(self.current_preset)

    def _preset_selected(self, _event: tk.Event | None = None) -> None:
        if self.engine.running:
            messagebox.showinfo("Hunt em andamento", "Termine a hunt antes de trocar o preset.", parent=self.root)
            self.preset_var.set(self.current_preset)
            return
        self._load_preset(self.preset_var.get())

    def _load_preset(self, name: str) -> None:
        self.current_preset = name
        self.configs = {config.catalog_id: config for config in self.presets.get(name)
                        if config.catalog_id in self.catalog_by_id}
        self.preset_var.set(name)
        self._refresh_all_timer_views()
        self.status_var.set(f"Preset {name} carregado.")

    def _save_preset(self) -> None:
        self.presets.save(self.current_preset, list(self.configs.values()))
        self._refresh_presets()
        self.status_var.set(f"Preset {self.current_preset} salvo.")

    def _new_preset(self) -> None:
        if self._configuration_locked():
            return
        name = simpledialog.askstring("Novo preset", "Nome do preset:", parent=self.root)
        if not name:
            return
        if name.strip() in self.presets.names:
            messagebox.showerror("Preset existente", "Já existe um preset com esse nome.", parent=self.root)
            return
        self.presets.save(name, [])
        self._refresh_presets()
        self._load_preset(name.strip())

    def _duplicate_preset(self) -> None:
        if self._configuration_locked():
            return
        name = simpledialog.askstring("Duplicar preset", "Nome da cópia:", parent=self.root)
        if not name:
            return
        if name.strip() in self.presets.names:
            messagebox.showerror("Preset existente", "Já existe um preset com esse nome.", parent=self.root)
            return
        self.presets.save(name, list(self.configs.values()))
        self._refresh_presets()
        self._load_preset(name.strip())

    def _delete_preset(self) -> None:
        if self._configuration_locked():
            return
        if not messagebox.askyesno("Excluir preset", f"Excluir o preset {self.current_preset}?", parent=self.root):
            return
        self.presets.delete(self.current_preset)
        self._refresh_presets()
        self._load_preset(self.current_preset)

    def _apply_topmost(self) -> None:
        self.root.attributes("-topmost", self.topmost_var.get())

    def _configuration_locked(self) -> bool:
        if not self.engine.running:
            return False
        messagebox.showinfo("Hunt em andamento", "Termine a hunt antes de alterar os timers.", parent=self.root)
        return True

    def _apply_compact(self) -> None:
        if self.compact_var.get():
            self.config_panel.grid_remove()
            self.root.geometry("520x460")
            self.root.minsize(440, 320)
        else:
            self.config_panel.grid()
            self.root.geometry("1040x760")
            self.root.minsize(760, 560)

    def _on_close(self) -> None:
        if self.engine.running and not messagebox.askyesno("Sair", "Há uma hunt em andamento. Deseja sair?", parent=self.root):
            return
        self.alerts.close()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    HuntTrackerApp(root)
    root.mainloop()
