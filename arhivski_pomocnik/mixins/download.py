"""DownloadMixin: funkcionalni sklop Arhivskega pomočnika."""
from ..common import *
from ..constants import *
from ..helpers import *
from ..dialogs import DownloadSettingsDialog

class DownloadMixin:
    def build_download_tab(self):
        top_frame = tk.Frame(self.tab_dl)
        top_frame.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(top_frame, text="URL-ji matičnih knjig (ali župnijske strani):", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(top_frame, text="⚙ Nastavitve Hitrosti Prenosa", bg="#2196F3", fg="white", font=("Arial", 9, "bold"), command=self.open_download_settings).pack(side=tk.RIGHT)
        self.dl_txt_urls = scrolledtext.ScrolledText(self.tab_dl, width=70, height=4, font=("Consolas", 9))
        self.dl_txt_urls.pack(padx=10, pady=2, fill="x")

        range_frame = tk.Frame(self.tab_dl)
        range_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(range_frame, text="Strani za prenos (npr. '5' ali '10-13'):", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        self.dl_ent_range = tk.Entry(range_frame, font=("Arial", 9), width=25)
        self.dl_ent_range.pack(side=tk.LEFT)

        tk.Label(self.tab_dl, text="Izhodna korenska mapa:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(5, 2))
        dir_frame = tk.Frame(self.tab_dl)
        dir_frame.pack(padx=10, pady=2, fill="x")
        self.dl_ent_dir = tk.Entry(dir_frame, font=("Arial", 10))
        self.dl_ent_dir.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        self.dl_ent_dir.insert(0, r"D:\Matricula")
        tk.Button(dir_frame, text="Brskaj...", command=lambda: self.browse_directory(self.dl_ent_dir), width=10).pack(side=tk.RIGHT)

        btn_frame = tk.Frame(self.tab_dl)
        btn_frame.pack(padx=10, pady=10, fill="x")
        self.dl_btn_start = tk.Button(btn_frame, text="Začni prenos", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), height=2, command=self.start_download)
        self.dl_btn_start.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        self.dl_btn_cancel = tk.Button(btn_frame, text="Prekini", bg="#f44336", fg="white", font=("Arial", 11, "bold"), height=2, width=12, command=self.cancel_download, state=tk.DISABLED)
        self.dl_btn_cancel.pack(side=tk.RIGHT)
        
        dl_stats_frame = tk.LabelFrame(self.tab_dl, text=" Prikaz delovanja ", font=("Arial", 9, "bold"), bg="#f8f9fa")
        dl_stats_frame.pack(padx=10, pady=5, fill="x")
        self.dl_lbl_speed = tk.Label(dl_stats_frame, text="Trenutna hitrost: -", font=("Arial", 9), bg="#f8f9fa", width=25, anchor="w")
        self.dl_lbl_speed.grid(row=0, column=0, padx=10, pady=5)
        self.dl_lbl_next = tk.Label(dl_stats_frame, text="Čas do naslednjega: -", font=("Arial", 9), bg="#f8f9fa", width=25, anchor="w")
        self.dl_lbl_next.grid(row=0, column=1, padx=10, pady=5)
        self.dl_lbl_status = tk.Label(dl_stats_frame, text="Stanje: Pripravljen", font=("Arial", 9, "bold"), fg="blue", bg="#f8f9fa", anchor="w")
        self.dl_lbl_status.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        prog_frame = tk.Frame(self.tab_dl)
        prog_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(prog_frame, text="Celoten napredek:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 2))
        self.dl_progress_books = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate")
        self.dl_progress_books.pack(fill="x", pady=(0, 10))
        tk.Label(prog_frame, text="Napredek trenutne knjige:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 2))
        self.dl_progress_pages = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate")
        self.dl_progress_pages.pack(fill="x", pady=(0, 5))

        tk.Label(self.tab_dl, text="Dnevnik prenosov:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(2, 2))
        self.dl_txt_log = scrolledtext.ScrolledText(self.tab_dl, width=70, height=8, font=("Consolas", 9))
        self.dl_txt_log.pack(padx=10, pady=(0, 10), fill="both", expand=True)

    def ui_update_dl(self, **kwargs):
        def task():
            if 'speed' in kwargs: self.dl_lbl_speed.config(text=kwargs['speed'])
            if 'next_time' in kwargs: self.dl_lbl_next.config(text=kwargs['next_time'])
            if 'status' in kwargs: self.dl_lbl_status.config(text=kwargs['status'])
            if 'log' in kwargs: self.dl_log(kwargs['log'])
            if 'prog_val_book' in kwargs: self.dl_progress_books['value'] = kwargs['prog_val_book']
            if 'prog_max_book' in kwargs: self.dl_progress_books['maximum'] = kwargs['prog_max_book']
            if 'prog_val_page' in kwargs: self.dl_progress_pages['value'] = kwargs['prog_val_page']
            if 'prog_max_page' in kwargs: self.dl_progress_pages['maximum'] = kwargs['prog_max_page']
        self.root.after(0, task)

    def dl_log(self, message):
        self.dl_txt_log.insert(tk.END, message + "\n")
        self.dl_txt_log.see(tk.END)

    def open_download_settings(self):
        settings = load_settings()
        dl_settings = settings.get("DownloadSettings", DL_PRESETS["POČASI"])
        DownloadSettingsDialog(self.root, dl_settings, self.on_dl_settings_saved)

    def on_dl_settings_saved(self, new_dl_settings):
        settings = load_settings()
        settings["DownloadSettings"] = new_dl_settings
        save_settings(settings)

    def cancel_download(self):
        self.dl_cancel_event.set()
        self.ui_update_dl(log="\n[!] Prekinjam...", status="Stanje: Prekinjanje...", next_time="-")

    def smart_sleep(self, seconds, msg="Čas do naslednjega"):
        end_time = time.time() + max(0.0, seconds)
        while time.time() < end_time:
            if self.dl_cancel_event.is_set(): return False
            remaining = end_time - time.time()
            self.ui_update_dl(next_time=f"{msg}: {remaining:.1f} s")
            self.dl_cancel_event.wait(min(0.2, remaining))
        self.ui_update_dl(next_time=f"{msg}: 0.0 s")
        return not self.dl_cancel_event.is_set()

    def write_book_manifest(self, target_dir, detail_url, parish_name, book_category, book_folder, image_urls):
        lines = [
            "MATRIKULA ONLINE – PODATKI O KNJIGI",
            f"Župnija: {parish_name}", f"Vrsta: {book_category}",
            f"Knjiga: {book_folder}", f"URL knjige: {detail_url}",
            f"Število slik: {len(image_urls)}", "", "URL-ji slik:"
        ]
        lines.extend(f"{i:04d}\t{url}" for i, url in enumerate(image_urls, start=1))
        write_text_atomic(os.path.join(target_dir, "_source.txt"), "\n".join(lines) + "\n")

    def start_download(self):
        raw_text = self.dl_txt_urls.get("1.0", tk.END).strip()
        base_dir = self.dl_ent_dir.get().strip()
        urls = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not urls: return
        settings = load_settings()
        dl_settings = normalize_download_settings(settings.get("DownloadSettings", {}))

        self.dl_cancel_event.clear()
        self.dl_btn_start.config(state=tk.DISABLED, text="Prenos poteka...")
        self.dl_btn_cancel.config(state=tk.NORMAL)
        
        self.dl_progress_books.config(maximum=100, value=0)
        self.dl_progress_pages.config(value=0)
        self.dl_session_images = 0
        self.dl_session_start = time.time()
        
        threading.Thread(target=self.download_coordinator, args=(urls, base_dir, self.dl_ent_range.get().strip(), dl_settings), daemon=True).start()

    def download_coordinator(self, initial_urls, base_output_dir, page_range_str, dl_settings):
        urls = []
        for url in initial_urls:
            if "/image/" not in url and "?pg=" not in url:
                try:
                    self.ui_update_dl(log=f"[*] Razširjam župnijski URL: {url}")
                    found = expand_parish_url(url)
                    urls.extend(found)
                    self.ui_update_dl(log=f"  -> Najdenih {len(found)} knjig.")
                except Exception as e:
                    self.ui_update_dl(log=f"[!] Napaka pri iskanju knjig na {url}: {e}")
                    urls.append(url)
            else:
                urls.append(url)

        urls = list(dict.fromkeys(urls))
        total_books = len(urls)
        all_books_ok = True
        
        self.ui_update_dl(
            log=f"[*] Skupaj knjig za prenos: {total_books}.\n[*] Profil hitrosti: {dl_settings.get('profile', 'PO MERI')}\n" + "=" * 50,
            status="Stanje: Priprava"
        )

        for book_index, detail_url in enumerate(urls, start=1):
            if self.dl_cancel_event.is_set(): 
                all_books_ok = False
                break
                
            self.ui_update_dl(log=f"\n[Knjiga {book_index}/{total_books}] Obdelujem URL: {detail_url}")
            
            try:
                parish_name, book_category, book_folder, image_urls = get_book_metadata_and_urls(detail_url)
                total_pages = len(image_urls)
                target_pages = parse_page_range(page_range_str, total_pages) or list(range(1, total_pages + 1))
                
                self.ui_update_dl(log=f"[*] Župnija: {parish_name} | Knjiga: {book_folder} | Izbrane strani: {len(target_pages)}/{total_pages}")
                
                target_dir = os.path.join(base_output_dir, parish_name, book_category, book_folder)
                os.makedirs(target_dir, exist_ok=True)
                self.write_book_manifest(target_dir, detail_url, parish_name, book_category, book_folder, image_urls)
                
                if not target_pages:
                    self.ui_update_dl(prog_val_book=(book_index / total_books) * 100)
                    continue

                self.ui_update_dl(prog_max_page=len(target_pages), prog_val_page=0)
                tasks = []
                for queue_index, page_number in enumerate(target_pages, start=1):
                    image_filename = f"{parish_name}_{book_folder}_{page_number:04d}.jpg"
                    tasks.append((page_number, image_urls[page_number - 1], os.path.join(target_dir, image_filename), queue_index, len(target_pages), total_pages, book_index, total_books, dl_settings))

                completed = 0
                book_ok = True
                
                with ThreadPoolExecutor(max_workers=dl_settings["concurrent"]) as executor:
                    futures = [executor.submit(self.download_page_task, *task) for task in tasks]
                    for future in as_completed(futures):
                        try:
                            if not bool(future.result()): book_ok = False
                        except Exception as exc:
                            book_ok = False
                            self.ui_update_dl(log=f"[!] Napaka delovne niti: {exc}")
                        completed += 1
                        
                        overall = ((book_index - 1) + completed / len(target_pages)) / total_books * 100
                        self.ui_update_dl(prog_val_page=completed, prog_val_book=overall)
                
                if self.dl_cancel_event.is_set(): book_ok = False

                all_pages_valid = all(is_valid_jpeg(os.path.join(target_dir, f"{parish_name}_{book_folder}_{page_no:04d}.jpg")) for page_no in range(1, total_pages + 1))
                done_path = os.path.join(target_dir, "_DONE")
                
                if all_pages_valid:
                    write_text_atomic(done_path, f"Prenos vseh {total_pages} slik je preverjeno zaključen.\n")
                    self.ui_update_dl(log=f"✅ Knjiga {book_folder}: vse slike so prisotne in preverjene.")
                else:
                    safe_remove(done_path)
                    self.ui_update_dl(log=f"[*] Knjiga {book_folder}: obdelano, vendar celotna knjiga še nima vseh {total_pages} JPG slik.")

                if not book_ok: all_books_ok = False
                else: self.ui_update_dl(log=f"✅ Knjiga {book_index} obdelana!")
                
            except Exception as exc:
                if str(exc) == "PARISH_PAGE":
                     self.ui_update_dl(log=f"[-] Stran ni knjiga, ampak župnija/okrožje brez knjig: {detail_url}")
                else:
                     all_books_ok = False
                     self.ui_update_dl(log=f"[!] Napaka pri knjigi {book_index}: {exc}")

            self.ui_update_dl(prog_val_book=(book_index / total_books) * 100)

        if self.dl_cancel_event.is_set():
            self.ui_update_dl(log="\n[!] Prenosi so bili prekinjeni.", status="Stanje: Prekinjeno")
        elif all_books_ok:
            self.ui_update_dl(
                prog_val_book=100, status="Stanje: Zaključeno", next_time="Čas do naslednjega: -",
                speed="Trenutna hitrost: -", log="\n" + "=" * 50 + "\n✅ Vsi izbrani prenosi so zaključeni."
            )

        self.root.after(0, lambda: self.dl_btn_start.config(state=tk.NORMAL, text="Začni prenos"))
        self.root.after(0, lambda: self.dl_btn_cancel.config(state=tk.DISABLED))

    def download_page_task(self, page_idx, img_url, img_filepath, current_in_queue, target_count, total_pages, current_book, total_books, dl_settings):
        if self.dl_cancel_event.is_set(): return False
        
        img_filename = os.path.basename(img_filepath)
        if is_valid_jpeg(img_filepath):
            self.ui_update_dl(log=f"[-] Preskakujem (obstoječa JPG je veljavna): {img_filename}")
            return True
            
        if os.path.exists(img_filepath): safe_remove(img_filepath)

        with self.dl_lock:
            if self.dl_cancel_event.is_set(): return False
            
            # Popravek deljenja z 0
            if dl_settings["pause_every"] > 0 and self.dl_session_images > 0 and self.dl_session_images % dl_settings["pause_every"] == 0:
                if not self.smart_sleep(dl_settings["pause_duration"], "Daljši premor"): return False
            else:
                if not self.smart_sleep(random.uniform(dl_settings["min_delay"], dl_settings["max_delay"]), "Čakanje"): return False
                
            # Omejitev seje
            if dl_settings["max_session"] > 0 and self.dl_session_images >= dl_settings["max_session"]:
                self.ui_update_dl(log=f"[!] Omejitev seje ({dl_settings['max_session']}) presežena. Premor pred nadaljevanjem...")
                if not self.smart_sleep(60, "Osveževanje seje"): return False
                self.dl_session_images = 0 # reset za novo sejo
            
            self.dl_session_images += 1
            elapsed = time.time() - self.dl_session_start
            speed = (self.dl_session_images / elapsed) * 60 if elapsed > 0 else 0
            self.ui_update_dl(speed=f"Trenutna hitrost: {speed:.1f} zahtev/min", status=f"Stanje: Prenašam stran {page_idx}...")

        self.ui_update_dl(log=f"[+] Prenašam stran {page_idx}/{total_pages} -> {img_filename}")
        
        temp_path = img_filepath + ".part"
        retries = dl_settings["retries"]
        success = False

        for attempt in range(retries + 1):
            if self.dl_cancel_event.is_set():
                safe_remove(temp_path)
                return False
            try:
                req = urllib.request.Request(img_url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=dl_settings["timeout"]) as response:
                    with open(temp_path, "wb") as output:
                        while True:
                            if self.dl_cancel_event.is_set(): raise InterruptedError("Prekinjeno")
                            chunk = response.read(64 * 1024)
                            if not chunk: break
                            output.write(chunk)
                if is_valid_jpeg(temp_path):
                    os.replace(temp_path, img_filepath)
                    success = True
                    break
            except Exception as e:
                safe_remove(temp_path)
                if attempt < retries:
                    self.ui_update_dl(log=f"[!] Napaka pri {img_filename}: {e}. Ponovni poskus {attempt+1}/{retries}.")
                    if not self.smart_sleep(min(15, 3 * (attempt + 1)), "Ponovni poskus"): return False
                else:
                    self.ui_update_dl(log=f"[!] Prenos {img_filename} ni uspel po {retries} poskusih.")

        if success:
            self.ui_update_dl(log=f"[✓] Shranjeno in preverjeno: {img_filename}")
            return True
        return False
