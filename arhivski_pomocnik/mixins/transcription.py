"""TranscriptionMixin: funkcionalni sklop Arhivskega pomočnika."""
from ..common import *
from ..constants import *
from ..helpers import *
from ..dialogs import ApiLimitsDialog, SettingsDialog, PromptDialog

class TranscriptionMixin:
    def build_ai_tab(self):
        dir_frame = tk.LabelFrame(self.tab_ai, text=" 1. Izberi mapo s prenesenimi slikami ", font=("Arial", 10, "bold"))
        dir_frame.pack(padx=10, pady=10, fill="x")
        dir_sub = tk.Frame(dir_frame)
        dir_sub.pack(padx=10, pady=10, fill="x")
        self.ai_ent_dir = tk.Entry(dir_sub, font=("Arial", 10))
        self.ai_ent_dir.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        tk.Button(dir_sub, text="Brskaj...", command=lambda: self.browse_directory(self.ai_ent_dir), width=10).pack(side=tk.RIGHT)

        opt_frame = tk.Frame(self.tab_ai)
        opt_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(opt_frame, text="Obseg strani:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self.ai_ent_range = tk.Entry(opt_frame, font=("Arial", 9), width=10)
        self.ai_ent_range.pack(side=tk.LEFT, padx=5)

        tk.Button(opt_frame, text="⚙ Omejitve in Poraba", bg="#009688", fg="white", font=("Arial", 9, "bold"), command=self.open_limits_dialog).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(opt_frame, text="🔑 Nastavitve API", bg="#2196F3", fg="white", font=("Arial", 9, "bold"), command=lambda: SettingsDialog(self.root)).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(opt_frame, text="📝 Navodila", bg="#FF9800", fg="white", font=("Arial", 9, "bold"), command=lambda: PromptDialog(self.root)).pack(side=tk.RIGHT)

        stats_frame = tk.LabelFrame(self.tab_ai, text=" Prikaz delovanja in stroškov ", font=("Arial", 10, "bold"), bg="#f8f9fa")
        stats_frame.pack(padx=10, pady=10, fill="x")

        self.ai_lbl_total = tk.Label(stats_frame, text="Skupaj slik: 0", font=("Arial", 9), bg="#f8f9fa", width=20, anchor="w")
        self.ai_lbl_total.grid(row=0, column=0, padx=10, pady=5)
        self.ai_lbl_current = tk.Label(stats_frame, text="Trenutna stran: -", font=("Arial", 9), bg="#f8f9fa", width=40, anchor="w")
        self.ai_lbl_current.grid(row=0, column=1, padx=10, pady=5, columnspan=2)

        self.ai_lbl_success = tk.Label(stats_frame, text="Uspešno: 0", font=("Arial", 9), fg="green", bg="#f8f9fa", width=20, anchor="w")
        self.ai_lbl_success.grid(row=1, column=0, padx=10, pady=5)
        self.ai_lbl_fail = tk.Label(stats_frame, text="Neuspešno: 0", font=("Arial", 9), fg="red", bg="#f8f9fa", width=20, anchor="w")
        self.ai_lbl_fail.grid(row=1, column=1, padx=10, pady=5)

        self.ai_lbl_api = tk.Label(stats_frame, text="Status API: Pripravljen", font=("Arial", 9, "bold"), fg="blue", bg="#f8f9fa", anchor="w")
        self.ai_lbl_api.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.ai_lbl_cost = tk.Label(stats_frame, text=f"Poraba v tem mesecu: {self.api_ledger.monthly_cost:.4f} €", font=("Arial", 9, "bold"), fg="purple", bg="#f8f9fa", anchor="w")
        self.ai_lbl_cost.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="w")

        btn_frame_ai = tk.Frame(self.tab_ai)
        btn_frame_ai.pack(padx=10, pady=5, fill="x")
        self.ai_btn_start = tk.Button(btn_frame_ai, text="Začni AI Transkripcijo", bg="#9C27B0", fg="white", font=("Arial", 11, "bold"), height=2, command=self.start_ai)
        self.ai_btn_start.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        self.ai_btn_cancel = tk.Button(btn_frame_ai, text="Prekini", bg="#f44336", fg="white", font=("Arial", 11, "bold"), height=2, width=12, command=self.cancel_ai, state=tk.DISABLED)
        self.ai_btn_cancel.pack(side=tk.RIGHT)

        self.ai_progress = ttk.Progressbar(self.tab_ai, orient="horizontal", mode="determinate")
        self.ai_progress.pack(padx=10, pady=5, fill="x")

        self.ai_txt_log = scrolledtext.ScrolledText(self.tab_ai, width=70, height=8, font=("Consolas", 9))
        self.ai_txt_log.pack(padx=10, pady=5, fill="both", expand=True)

    def open_limits_dialog(self):
        settings = load_settings()
        ApiLimitsDialog(self.root, settings, self.on_limits_saved)

    def on_limits_saved(self, new_settings):
        save_settings(new_settings)
        messagebox.showinfo("Shranjeno", "Omejitve in profili uspešno shranjeni!")

    def ai_log(self, message):
        self.ai_txt_log.insert(tk.END, message + "\n")
        self.ai_txt_log.see(tk.END)

    def ai_ui_update(self, **kwargs):
        def task():
            if 'total' in kwargs: self.ai_lbl_total.config(text=f"Skupaj slik: {kwargs['total']}")
            if 'current' in kwargs: self.ai_lbl_current.config(text=f"Trenutna stran: {kwargs['current']}")
            if 'success' in kwargs: self.ai_lbl_success.config(text=f"Uspešno: {kwargs['success']}")
            if 'fail' in kwargs: self.ai_lbl_fail.config(text=f"Neuspešno: {kwargs['fail']}")
            if 'api' in kwargs: self.ai_lbl_api.config(text=f"Status API: {kwargs['api']}")
            if 'cost' in kwargs: self.ai_lbl_cost.config(text=kwargs['cost'])
            if 'log' in kwargs: self.ai_log(kwargs['log'])
            if 'prog_val' in kwargs: self.ai_progress['value'] = kwargs['prog_val']
            if 'prog_max' in kwargs: self.ai_progress['maximum'] = kwargs['prog_max']
        self.root.after(0, task)

    def cancel_ai(self):
        self.ai_cancel_event.set()
        self.ai_ui_update(log="\n[!] Uporabnik je prekinil transkripcijo...", api="Prekinjeno")

    def start_ai(self):
        target_dir = self.ai_ent_dir.get().strip()
        settings = load_settings()
        provider = settings.get("active_provider", "Gemini")
        if not target_dir or not os.path.exists(target_dir): return messagebox.showerror("Napaka", "Neveljavna mapa!")
        
        self.ai_cancel_event.clear()
        self.ai_btn_start.config(state=tk.DISABLED, text="Obdelujem...")
        self.ai_btn_cancel.config(state=tk.NORMAL)
        
        threading.Thread(target=self.ai_worker, args=(target_dir, self.ai_ent_range.get().strip(), provider, settings), daemon=True).start()

    def ai_worker(self, target_dir, page_range_str, provider, settings):
        api_key = settings.get(provider, {}).get("api_key", "")
        model_name = settings.get(provider, {}).get("model", "")
        limits = settings.get(provider, {}).get("limits", API_LIMIT_PRESETS["NORMALNO"])
        budget = settings.get("budget_limit_eur", 5.0)
        
        rpm, tpm, rpd = limits.get("rpm", 15), limits.get("tpm", 100000), limits.get("rpd", 1500)
        success_c = fail_c = 0
        self.api_ledger._calculate_current_usage()

        try:
            # 1. POIŠČI VSE PODMAPE, KI VSEBUJEJO SLIKE (.jpg)
            dirs_to_process = []
            for root_path, dirs, files in os.walk(target_dir):
                if any(f.lower().endswith(".jpg") for f in files):
                    dirs_to_process.append(root_path)
                    
            if not dirs_to_process:
                self.ai_ui_update(log="[!] V izbrani mapi in njenih podmapah ni bilo najdenih .jpg slik.")
                return

            # Izračunamo skupno število slik za celoten progress bar
            all_valid_files = []
            allowed_pages = parse_page_range(page_range_str)
            for d in dirs_to_process:
                files = sorted(f for f in os.listdir(d) if f.lower().endswith(".jpg"))
                valid = [os.path.join(d, f) for f in files if not allowed_pages or (re.search(r"_(\d+)\.jpg$", f) and int(re.search(r"_(\d+)\.jpg$", f).group(1)) in allowed_pages)]
                all_valid_files.extend(valid)

            total_files = len(all_valid_files)
            self.ai_ui_update(total=total_files, prog_max=total_files, prog_val=0)

            global_idx = 0

            # 2. OBDELAVA VSAKE POSAMEZNE MAPE
            for current_book_dir in dirs_to_process:
                if self.ai_cancel_event.is_set(): break
                
                # Preberemo metapodatke iz _source.txt za trenutno mapo
                source_path = os.path.join(current_book_dir, "_source.txt")
                book_type = "KRSTNE" # Default
                if os.path.exists(source_path):
                    with open(source_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("Vrsta:"):
                                val = line.replace("Vrsta:", "").strip()
                                if "POROCNE" in val: book_type = "POROCNE"
                                elif "MRTVIH" in val: book_type = "KNJIGE_MRTVIH"
                                break
                
                self.ai_ui_update(log=f"\n[*] Prehajam v mapo: {os.path.basename(current_book_dir)}")
                self.ai_ui_update(log=f"[*] Detektiran tip knjige: {book_type}. Nastavljam prompt...")
                # Vsaka vrsta knjige ima svoj JSON-shema prompt.
                # Fallback določimo ločeno, da Python ne išče ključa "KRSTNE"
                # že med vrednotenjem privzetega argumenta metode dict.get().
                schema_prompt = PROMPT_JSON_SCHEMAS.get(book_type)
                if not schema_prompt:
                    self.ai_ui_update(log=(
                        f"[!] OPOZORILO: Za tip '{book_type}' ni posebnega prompta. "
                        "Uporabljam privzeti prompt za krstne knjige."
                    ))
                    schema_prompt = PROMPT_JSON_SCHEMAS.get("KRSTNE", "")
                if not schema_prompt:
                    raise RuntimeError(
                        "JSON-sheme za AI transkripcijo niso bile ustvarjene. "
                        "Preveri datoteko arhivski_pomocnik/constants.py."
                    )
                ai_prompt = load_prompt() + schema_prompt

                # Filtriramo slike za to mapo (obseg strani)
                files = sorted(f for f in os.listdir(current_book_dir) if f.lower().endswith(".jpg"))
                valid_files = [f for f in files if not allowed_pages or (re.search(r"_(\d+)\.jpg$", f) and int(re.search(r"_(\d+)\.jpg$", f).group(1)) in allowed_pages)]
                
                for filename in valid_files:
                    if self.ai_cancel_event.is_set(): break
                    global_idx += 1
                    
                    current_monthly_cost = self.api_ledger.monthly_cost
                    if current_monthly_cost >= budget * 0.8 and not self.api_ledger.warned_80:
                        self.api_ledger.warned_80 = True
                        self.ai_ui_update(log="[!] OPOZORILO: Dosegli ste 80% mesečnega limita stroškov!")
                    if current_monthly_cost >= budget:
                        self.ai_ui_update(log=f"\n[!] LIMIT DOSEŽEN ({budget} €). Program se ustavlja.", api="Mesečni limit!")
                        self.root.after(0, lambda: messagebox.showinfo("Limit", "Mesečni limit stroškov je bil dosežen."))
                        return

                    img_path = os.path.join(current_book_dir, filename)
                    txt_path = os.path.join(current_book_dir, os.path.splitext(filename)[0] + ".txt")
                    err_path = os.path.join(current_book_dir, os.path.splitext(filename)[0] + ".err")

                    if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
                        self.ai_ui_update(log=f"[-] Preskakujem (uspešen prepis že obstaja): {filename}", prog_val=global_idx)
                        continue

                    if not is_valid_jpeg(img_path):
                        self.ai_ui_update(log=f"[!] Neveljaven JPG: {filename}", prog_val=global_idx)
                        continue

                    est_tokens = 4000
                    if not self.api_ledger.wait_for_capacity(rpm, tpm, rpd, est_tokens, self.ai_cancel_event, self.ai_ui_update):
                        return

                    self.ai_ui_update(log=f"\n[+] AI obdelava ({provider}): {filename}", api=f"Povezava: {provider}...")
                    
                    try:
                        if provider == "OpenAI":
                            success, res_txt, in_tok, out_tok = self.call_openai(api_key, model_name, img_path, ai_prompt)
                        elif provider == "Anthropic":
                            success, res_txt, in_tok, out_tok = self.call_anthropic(api_key, model_name, img_path, ai_prompt)
                        else:
                            success, res_txt, in_tok, out_tok = self.call_gemini(api_key, model_name, img_path, ai_prompt)
                    except Exception as api_err:
                        self.ai_ui_update(log=f"[!] Napaka pri API klicu: {api_err}")
                        success, res_txt, in_tok, out_tok = False, str(api_err), 0, 0

                    if self.ai_cancel_event.is_set(): break

                    # Validacija JSON strukture pred shranjevanjem
                    if success and res_txt:
                        expected_keys = [c[0] for c in SCHEMA_FIELDS[book_type] if c[0] not in ('zupnija', 'knjiga', 'slika')]
                        is_valid, err_msg = is_valid_json_schema(res_txt, expected_keys)
                        if not is_valid:
                            success = False
                            res_txt = f"NEVELJAVEN JSON: {err_msg}\n\n{res_txt}"

                    cost = 0.0
                    if in_tok > 0 or out_tok > 0:
                        c_in = PRICING.get(provider, {}).get(model_name, PRICING[provider]).get("in", PRICING[provider]["default_in"])
                        c_out = PRICING.get(provider, {}).get(model_name, PRICING[provider]).get("out", PRICING[provider]["default_out"])
                        cost = ((in_tok / 1_000_000 * c_in) + (out_tok / 1_000_000 * c_out)) * USD_TO_EUR

                    if success and res_txt:
                        write_text_atomic(txt_path, res_txt.strip() + "\n")
                        safe_remove(err_path)
                        success_c += 1
                        self.api_ledger.record_usage(provider, model_name, in_tok, out_tok, cost, "OK")
                        self.ai_ui_update(success=success_c, log=f"  -> Uspešno validirano in shranjeno", api="Uspešno", cost=f"Poraba ta mesec: {self.api_ledger.monthly_cost:.4f} €")
                    else:
                        fail_c += 1
                        write_text_atomic(err_path, str(res_txt).strip() + "\n")
                        self.api_ledger.record_usage(provider, model_name, in_tok, out_tok, cost, "ERROR")
                        self.ai_ui_update(fail=fail_c, log=f"  -> NAPAKA: Shranjeno v .err", api="Napaka")
                    
                    self.ai_ui_update(prog_val=global_idx)

            if not self.ai_cancel_event.is_set():
                self.ai_ui_update(log="\n[✔] Obdelava vseh izbranih map in slik je zaključena!", api="Zaključeno")

        except Exception as exc:
            self.ai_ui_update(log=f"[KRITIČNA NAPAKA]: {exc}")
        finally:
            self.root.after(0, lambda: self.ai_btn_start.config(state=tk.NORMAL, text="Začni AI Transkripcijo"))
            self.root.after(0, lambda: self.ai_btn_cancel.config(state=tk.DISABLED))

    def _encode_img(self, path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")

    def call_gemini(self, api_key, model_name, img_path, prompt):
        try: img_b64 = self._encode_img(img_path)
        except Exception as e: return False, str(e), 0, 0
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}, {"text": prompt}]}]}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        return self.execute_api_request("Gemini", req)

    def call_openai(self, api_key, model_name, img_path, prompt):
        try: img_b64 = self._encode_img(img_path)
        except Exception as e: return False, str(e), 0, 0
        url = "https://api.openai.com/v1/chat/completions"
        payload = {"model": model_name, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}], "max_tokens": 8192}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")
        return self.execute_api_request("OpenAI", req)

    def call_anthropic(self, api_key, model_name, img_path, prompt):
        try: img_b64 = self._encode_img(img_path)
        except Exception as e: return False, str(e), 0, 0
        url = "https://api.anthropic.com/v1/messages"
        payload = {"model": model_name, "max_tokens": 8192, "messages": [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}}, {"type": "text", "text": prompt}]}]}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"}, method="POST")
        return self.execute_api_request("Anthropic", req)

    def execute_api_request(self, provider, req, max_retries=3):
        for attempt in range(max_retries + 1):
            if self.ai_cancel_event.is_set(): return False, "Prekinjeno", 0, 0
            try:
                with urllib.request.urlopen(req, timeout=240) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    in_t = out_t = 0
                    if provider == "Gemini":
                        usage = res_data.get("usageMetadata", {})
                        in_t, out_t = usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)
                        c = res_data.get("candidates", [])
                        if c:
                            parts = [p.get("text", "") for p in c[0].get("content", {}).get("parts", []) if p.get("text")]
                            # Gemini lahko konča z max_tokens, kar pomeni odrezan tekst
                            if c[0].get("finishReason") == "MAX_TOKENS":
                                return False, "Besedilo je bilo odrezano (MAX_TOKENS)", in_t, out_t
                            return True, "\n".join(parts), in_t, out_t
                    elif provider == "OpenAI":
                        usage = res_data.get("usage", {})
                        in_t, out_t = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
                        c = res_data.get("choices", [])
                        if c: 
                            if c[0].get("finish_reason") == "length":
                                return False, "Besedilo je bilo odrezano (LENGTH)", in_t, out_t
                            return True, c[0].get("message", {}).get("content", ""), in_t, out_t
                    elif provider == "Anthropic":
                        usage = res_data.get("usage", {})
                        in_t, out_t = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
                        if res_data.get("stop_reason") == "max_tokens":
                             return False, "Besedilo je bilo odrezano (MAX_TOKENS)", in_t, out_t
                        c = res_data.get("content", [])
                        parts = [b.get("text", "") for b in c if b.get("type") == "text"]
                        if parts: return True, "\n".join(parts), in_t, out_t
                    return False, "Prazen odziv modela", 0, 0
            except urllib.error.HTTPError as he:
                if he.code in (400, 401, 403, 404): return False, f"HTTP {he.code}: Preveri ključ/model.", 0, 0
                if he.code == 429:
                    retry_after = he.headers.get("Retry-After")
                    wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 30
                    self.ai_ui_update(api=f"Rate Limit (429)! Čakam {wait_time}s...")
                    self.ai_cancel_event.wait(wait_time)
                    continue
                if attempt < max_retries:
                    self.ai_cancel_event.wait(5 * (attempt + 1))
                    continue
                return False, f"Napaka strežnika HTTP {he.code}", 0, 0
            except Exception as e:
                if attempt < max_retries:
                    self.ai_cancel_event.wait(5 * (attempt + 1))
                    continue
                return False, f"Omrežna napaka: {e}", 0, 0
        return False, "Neznana napaka", 0, 0
