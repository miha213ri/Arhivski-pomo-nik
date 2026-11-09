"""Pogovorna okna za nastavitve AI, prenosa in promptov."""
from .common import *
from .constants import *
from .helpers import *

class ApiLimitsDialog(tk.Toplevel):
    def __init__(self, parent, settings, on_save_callback):
        super().__init__(parent)
        self.title("Nadzor API Porabe in Omejitve")
        self.geometry("450x450")
        self.resizable(False, False)
        self.grab_set()
        self.settings = settings
        self.on_save = on_save_callback
        
        lbl_info = tk.Label(self, text="Nastavite omejitve hitrosti klicev po posameznih ponudnikih.", pady=10)
        lbl_info.pack()

        frame_top = tk.Frame(self)
        frame_top.pack(padx=20, fill="x", pady=5)
        tk.Label(frame_top, text="Ponudnik:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.cb_provider = ttk.Combobox(frame_top, values=["Gemini", "OpenAI", "Anthropic"], state="readonly", width=25)
        self.cb_provider.grid(row=0, column=1, padx=10, pady=5)
        self.cb_provider.set(self.settings.get("active_provider", "Gemini"))
        self.cb_provider.bind("<<ComboboxSelected>>", self.on_provider_change)
        
        tk.Label(frame_top, text="Profil:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.cb_profile = ttk.Combobox(frame_top, values=["VARČNO", "NORMALNO", "PO MERI"], state="readonly", width=25)
        self.cb_profile.grid(row=1, column=1, padx=10, pady=5)
        self.cb_profile.bind("<<ComboboxSelected>>", self.on_profile_change)

        self.entries = {}
        frame_inputs = tk.Frame(self)
        frame_inputs.pack(padx=20, pady=10, fill="x")
        fields = [("rpm", "Zahtevkov na minuto (RPM):"), ("tpm", "Tokenov na minuto (TPM):"), ("rpd", "Max zahtevkov na dan (RPD):")]
        for i, (key, label_text) in enumerate(fields):
            tk.Label(frame_inputs, text=label_text, anchor="w", width=26).grid(row=i, column=0, sticky="w", pady=5)
            ent = tk.Entry(frame_inputs, width=15)
            ent.grid(row=i, column=1, pady=5)
            ent.bind("<KeyRelease>", lambda e: self.cb_profile.set("PO MERI"))
            self.entries[key] = ent
            
        frame_budget = tk.Frame(self)
        frame_budget.pack(padx=20, pady=10, fill="x")
        tk.Label(frame_budget, text="Mesečni finančni limit (€):", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self.ent_budget = tk.Entry(frame_budget, width=10)
        self.ent_budget.pack(side=tk.LEFT, padx=10)
        self.ent_budget.insert(0, str(self.settings.get("budget_limit_eur", 5.0)))

        self.load_provider_data(self.cb_provider.get())
        tk.Button(self, text="Shrani omejitve", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.save_and_close).pack(pady=15)

    def load_provider_data(self, prov):
        prov_settings = self.settings.get(prov, {})
        limits = prov_settings.get("limits", API_LIMIT_PRESETS["NORMALNO"])
        self.cb_profile.set(prov_settings.get("profile", "NORMALNO"))
        for key, ent in self.entries.items():
            ent.delete(0, tk.END)
            ent.insert(0, str(limits.get(key, API_LIMIT_PRESETS["NORMALNO"][key])))

    def on_provider_change(self, event):
        self.load_provider_data(self.cb_provider.get())

    def on_profile_change(self, event):
        sel = self.cb_profile.get()
        if sel in API_LIMIT_PRESETS and sel != "PO MERI":
            for key, ent in self.entries.items():
                ent.delete(0, tk.END)
                ent.insert(0, str(API_LIMIT_PRESETS[sel][key]))

    def save_and_close(self):
        prov = self.cb_provider.get()
        try:
            rpm, tpm, rpd, budget = int(self.entries["rpm"].get()), int(self.entries["tpm"].get()), int(self.entries["rpd"].get()), float(self.ent_budget.get())
            if rpm < 1 or tpm < 1 or rpd < 1: raise ValueError("Vrednosti > 0.")
        except ValueError:
            return messagebox.showerror("Napaka", "Preverite vnose.")
        self.settings[prov]["limits"] = {"rpm": rpm, "tpm": tpm, "rpd": rpd}
        self.settings[prov]["profile"] = self.cb_profile.get()
        self.settings["budget_limit_eur"] = budget
        self.on_save(self.settings)
        self.destroy()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, on_save_callback=None):
        super().__init__(parent)
        self.title("Nastavitve AI API (Ključi)")
        self.geometry("480x280")
        self.resizable(False, False)
        self.grab_set() 
        self.on_save_callback = on_save_callback
        self.settings = load_settings()
        self.current_provider = self.settings.get("active_provider", "Gemini")

        frame_inputs = tk.Frame(self)
        frame_inputs.pack(padx=20, fill="x", pady=20)
        tk.Label(frame_inputs, text="Ponudnik AI:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="e", pady=10, padx=5)
        self.cb_provider = ttk.Combobox(frame_inputs, values=["Gemini", "OpenAI", "Anthropic"], state="readonly", width=37)
        self.cb_provider.grid(row=0, column=1, pady=10, sticky="w")
        self.cb_provider.set(self.current_provider)
        self.cb_provider.bind("<<ComboboxSelected>>", self.on_provider_change)

        tk.Label(frame_inputs, text="API Ključ:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.ent_key = tk.Entry(frame_inputs, width=40, show="*")
        self.ent_key.grid(row=1, column=1, columnspan=2, pady=5, sticky="w")

        tk.Label(frame_inputs, text="Ime modela:", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.cb_model = ttk.Combobox(frame_inputs, width=25)
        self.cb_model.grid(row=2, column=1, pady=5, sticky="w")
        
        self.btn_refresh = tk.Button(frame_inputs, text="🔄 Osveži", font=("Arial", 8), command=self.refresh_models)
        self.btn_refresh.grid(row=2, column=2, padx=5)

        self.update_ui_for_provider(self.current_provider)
        tk.Button(self, text="Shrani nastavitve", bg="#2196F3", fg="white", font=("Arial", 10, "bold"), command=self.save_and_close).pack(pady=20)

    def update_ui_for_provider(self, prov):
        self.ent_key.delete(0, tk.END)
        self.ent_key.insert(0, self.settings[prov].get("api_key", ""))
        self.cb_model.set(self.settings[prov].get("model", ""))

    def on_provider_change(self, event):
        old_prov = self.current_provider
        self.settings[old_prov]["api_key"] = self.ent_key.get().strip()
        self.settings[old_prov]["model"] = self.cb_model.get().strip()
        self.current_provider = self.cb_provider.get()
        self.update_ui_for_provider(self.current_provider)

    def refresh_models(self):
        prov = self.cb_provider.get()
        api_key = self.ent_key.get().strip()
        if not api_key: return messagebox.showwarning("Napaka", "Najprej vnesi API ključ!")
        self.btn_refresh.config(state=tk.DISABLED, text="Iščem...")
        threading.Thread(target=self._fetch_models_thread, args=(prov, api_key), daemon=True).start()

    def _fetch_models_thread(self, prov, api_key):
        modeli = []
        try:
            if prov == "Gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                with urllib.request.urlopen(urllib.request.Request(url), timeout=15) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    modeli = [m.get("name", "").replace("models/", "") for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
            elif prov == "OpenAI":
                url = "https://api.openai.com/v1/models"
                with urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"}), timeout=15) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    modeli = [m["id"] for m in data.get("data", []) if "gpt" in m["id"]]
            elif prov == "Anthropic":
                modeli = ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]
            
            if modeli:
                modeli.sort()
                self.cb_model.after(0, lambda: self._update_models_ui(modeli))
            else:
                self.cb_model.after(0, lambda: messagebox.showinfo("Napaka", "Ni bilo mogoče najti modelov."))
        except Exception as e:
            self.cb_model.after(0, lambda err=e: messagebox.showerror("Napaka API", str(err)))
        finally:
            self.cb_model.after(0, lambda: self.btn_refresh.config(state=tk.NORMAL, text="🔄 Osveži"))

    def _update_models_ui(self, modeli):
        self.cb_model['values'] = modeli
        if modeli: self.cb_model.set(modeli[0])

    def save_and_close(self):
        prov = self.cb_provider.get().strip()
        self.settings[prov]["api_key"] = self.ent_key.get().strip()
        self.settings[prov]["model"] = self.cb_model.get().strip()
        self.settings["active_provider"] = prov
        if save_settings(self.settings):
            if self.on_save_callback: self.on_save_callback()
            self.destroy()

class DownloadSettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_dl_settings, on_save_callback):
        super().__init__(parent)
        self.title("Nastavitve Hitrosti Prenosa")
        self.geometry("500x480")
        self.resizable(False, False)
        self.grab_set()
        self.on_save = on_save_callback
        self.settings = current_dl_settings
        
        frame_prof = tk.Frame(self)
        frame_prof.pack(padx=20, fill="x", pady=10)
        tk.Label(frame_prof, text="Profil hitrosti:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        self.cb_profile = ttk.Combobox(frame_prof, values=["POČASI", "NORMALNO", "HITRO", "PO MERI"], state="readonly", width=20)
        self.cb_profile.pack(side=tk.LEFT, padx=5)
        self.cb_profile.set(self.settings.get("profile", "POČASI"))
        self.cb_profile.bind("<<ComboboxSelected>>", self.on_profile_change)

        self.entries = {}
        frame_inputs = tk.Frame(self)
        frame_inputs.pack(padx=20, pady=10, fill="x")
        fields = [
            ("min_delay", "Minimalni premor (s):"), ("max_delay", "Maksimalni premor (s):"),
            ("pause_every", "Premor po številu slik:"), ("pause_duration", "Trajanje daljšega premora (s):"),
            ("timeout", "Časovna omejitev zahteve (s):"), ("retries", "Število ponovnih poskusov:"),
            ("max_session", "Največje število slik v seji:"), ("concurrent", "Vzporednih prenosov:")
        ]
        for i, (key, label_text) in enumerate(fields):
            tk.Label(frame_inputs, text=label_text, anchor="w", width=28).grid(row=i, column=0, sticky="w", pady=4)
            ent = tk.Entry(frame_inputs, width=15)
            ent.grid(row=i, column=1, pady=4)
            ent.insert(0, str(self.settings.get(key, "")))
            ent.bind("<KeyRelease>", lambda e: self.cb_profile.set("PO MERI"))
            self.entries[key] = ent

        tk.Button(self, text="Shrani nastavitve prenosa", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.save_and_close).pack(pady=15)

    def on_profile_change(self, event):
        sel = self.cb_profile.get()
        if sel in DL_PRESETS:
            for key, ent in self.entries.items():
                ent.delete(0, tk.END)
                ent.insert(0, str(DL_PRESETS[sel][key]))

    def save_and_close(self):
        new_settings = {"profile": self.cb_profile.get()}
        try:
            for key in ["min_delay", "max_delay", "pause_duration"]: new_settings[key] = float(self.entries[key].get())
            for key in ["pause_every", "timeout", "retries", "max_session", "concurrent"]: new_settings[key] = int(self.entries[key].get())
        except ValueError:
            return messagebox.showerror("Napaka vnosov", "Preverite vnose.")
        self.on_save(new_settings)
        self.destroy()

class PromptDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Urejanje navodil za AI (Prompt)")
        self.geometry("600x550")
        self.grab_set()

        tk.Label(self, text="Vnesite vaša osnovna navodila (specifična JSON shema se doda samodejno glede na vrsto knjige):", font=("Arial", 9, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
        self.txt_prompt = scrolledtext.ScrolledText(self, width=70, height=20, font=("Arial", 10))
        self.txt_prompt.pack(padx=10, pady=5, fill="both", expand=True)
        self.txt_prompt.insert(tk.END, load_prompt())

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Shrani navodila", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.save_and_close).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Ponastavi na privzeto", font=("Arial", 9), command=self.reset_default).pack(side=tk.LEFT, padx=10)

    def reset_default(self):
        self.txt_prompt.delete("1.0", tk.END)
        self.txt_prompt.insert(tk.END, DEFAULT_PROMPT)

    def save_and_close(self):
        new_prompt = self.txt_prompt.get("1.0", tk.END).strip()
        if save_prompt(new_prompt): self.destroy()
