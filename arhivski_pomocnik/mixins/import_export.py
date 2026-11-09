"""ImportExportMixin: funkcionalni sklop Arhivskega pomočnika."""
from ..common import *
from ..constants import *
from ..helpers import *

class ImportExportMixin:
    def build_uvoz_tab(self):
        frame_paths = ttk.LabelFrame(self.tab_uvoz, text=" 1. Nastavitev glavne mape in lokalnih datotek ", padding=12)
        frame_paths.pack(fill="x", padx=10, pady=8)
        
        frame_paths.columnconfigure(1, weight=1)

        ttk.Label(frame_paths, text="Glavni direktorij (z _source.txt):").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame_paths, textvariable=self.root_folder_path).grid(row=0, column=1, padx=5, pady=4, sticky="we")
        ttk.Button(frame_paths, text="Prebrskaj...", command=self.browse_root_folder_for_import).grid(row=0, column=2, pady=4, padx=2)
        
        ttk.Label(frame_paths, text="Izhodni Excel:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame_paths, textvariable=self.excel_output_path).grid(row=1, column=1, padx=5, pady=4, sticky="we")
        ttk.Button(frame_paths, text="Odpri Excel", command=self.open_excel_file).grid(row=1, column=2, pady=4, padx=2)
        ttk.Button(frame_paths, text="📁 Mapa", command=self.open_excel_dir).grid(row=1, column=3, pady=4, padx=2)
        ttk.Button(frame_paths, text="Pretvori JSON v Excel", command=self.start_convert_json_to_excel).grid(row=1, column=4, pady=4, padx=5)

        ttk.Label(frame_paths, text="Lokalna SQLite baza:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame_paths, textvariable=self.db_path).grid(row=2, column=1, padx=5, pady=4, sticky="we")
        ttk.Button(frame_paths, text="📁 Mapa", command=self.open_db_dir).grid(row=2, column=3, pady=4, padx=2)
        ttk.Button(frame_paths, text="Uvozi v lokalno bazo", command=self.start_import_to_local_db).grid(row=2, column=4, pady=4, padx=5)

        frame_live = ttk.LabelFrame(self.tab_uvoz, text=" 2. Integracija z Živo Bazo (MySQL / MariaDB) ", padding=12)
        frame_live.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame_live, text="Nastavitve Povezave", command=self.open_live_db_settings, width=22).grid(row=0, column=0, padx=6, pady=4)
        ttk.Button(frame_live, text="Ustvari tabele", command=self.start_create_live_db_tables, width=22).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(frame_live, text="Uvozi v Živo Bazo", command=self.start_import_to_live_db, width=22).grid(row=0, column=2, padx=6, pady=4)

        if not MYSQL_AVAILABLE:
            ttk.Label(frame_live, text="⚠️ Manjka PyMySQL!", foreground="red").grid(row=0, column=3, padx=6, pady=4)

        frame_log = ttk.LabelFrame(self.tab_uvoz, text=" Poročilo o izvedbi in kontroli ", padding=12)
        frame_log.pack(fill="both", expand=True, padx=10, pady=8)

        # DODANO: Progress bar za prikaz napredka uvoza (Lokalno in Živa Baza)
        self.uvoz_progress = ttk.Progressbar(frame_log, orient="horizontal", mode="determinate")
        self.uvoz_progress.pack(fill="x", pady=(0, 5))

        self.import_log_text = tk.Text(frame_log, wrap="word", height=10)
        self.import_log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_log, orient="vertical", command=self.import_log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.import_log_text.configure(yscrollcommand=scrollbar.set)

    def uvoz_log(self, message):
        self.import_log_text.insert(tk.END, message + "\n")
        self.import_log_text.see(tk.END)

    def open_excel_dir(self):
        if os.path.exists(self.excel_dir): os.startfile(self.excel_dir)
        else: messagebox.showerror("Napaka", "Mapa ne obstaja.")

    def open_db_dir(self):
        if os.path.exists(self.baze_dir): os.startfile(self.baze_dir)
        else: messagebox.showerror("Napaka", "Mapa ne obstaja.")

    def browse_root_folder_for_import(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.root_folder_path.set(dir_path)
            self.uvoz_log(f"Izbran glavni direktorij: {dir_path}")
            
            found_meta = None
            for current_path, dirs, files in os.walk(dir_path):
                if "_source.txt" in files:
                    source_path = os.path.join(current_path, "_source.txt")
                    meta = {"župnija": "Neznano", "knjiga": "Neznano", "vrsta": "KRSTNE"}
                    try:
                        with open(source_path, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.startswith("Župnija:"): meta["župnija"] = line.replace("Župnija:", "").strip()
                                elif line.startswith("Knjiga:"): meta["knjiga"] = line.replace("Knjiga:", "").strip()
                                elif line.startswith("Vrsta:"): meta["vrsta"] = line.replace("Vrsta:", "").strip()
                    except Exception as e:
                        self.uvoz_log(f"Napaka pri branju _source.txt: {e}")
                    found_meta = meta
                    break
            
            if found_meta and found_meta['župnija'] != "Neznano":
                zupnija = found_meta.get('župnija', 'Neznano')
                vrsta = found_meta.get('vrsta', 'Neznano')
                knjiga = found_meta.get('knjiga', 'Neznano')
                
                self.base_filename = f"{zupnija}_{vrsta}_{knjiga}"
                
                years = set()
                for current_path, dirs, files in os.walk(dir_path):
                    data_files = [f for f in files if f.endswith(".txt") and not f.startswith("_source")]
                    for df in data_files:
                        try:
                            with open(os.path.join(current_path, df), "r", encoding="utf-8") as f_obj:
                                content = f_obj.read().strip()
                                match = re.search(r'\b(1[5-9]\d\d)\b', content)
                                if match:
                                    j_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                                    if j_match:
                                        records = json.loads(j_match.group(0))
                                        for rec in records:
                                            for d_key in ["datum_rojstva", "datum_krsta", "datum_poroke", "datum_smrti"]:
                                                d_val = str(rec.get(d_key, ""))
                                                m = re.search(r'\b(1[5-9]\d\d)\b', d_val)
                                                if m: years.add(int(m.group(1)))
                        except Exception: pass 
                
                year_suffix = ""
                if years:
                    min_y = min(years)
                    max_y = max(years)
                    if min_y == max_y: year_suffix = f"_{min_y}"
                    else: year_suffix = f"_{min_y}_{max_y}"
                
                filename_base = f"{self.base_filename}{year_suffix}"
                self.excel_output_path.set(os.path.join(self.excel_dir, f"{filename_base}.xlsx"))
                self.db_path.set(os.path.join(self.baze_dir, f"{filename_base}.db"))
                self.uvoz_log(f"Pripravljeno za izvoz: {filename_base}")

    def open_excel_file(self):
        filepath = self.excel_output_path.get()
        if os.path.exists(filepath):
            try:
                os.startfile(filepath)
                self.uvoz_log(f"Odpiram datoteko: {filepath}")
            except Exception as e:
                self.uvoz_log(f"Napaka pri odpiranju: {e}")
        else:
            messagebox.showerror("Napaka", "Excel datoteka še ne obstaja!")

    def parse_json_content(self, filepath, filename, meta):
        try:
            with open(filepath, "r", encoding="utf-8") as f: content = f.read()
            match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
            if not match: raise Exception("Ne najdem JSON seznama.")
            records = json.loads(match.group(0))
        except Exception as e:
            raise Exception(f"Napaka JSON: {e}")
            
        parsed_rows = []
        parts = filename.replace(".txt", "").replace(".json", "").split("_")
        slika_val = parts[-1] if len(parts) >= 1 else "Neznano"
        
        b_type = meta.get("vrsta", "KRSTNE")
        excel_cols = EXCEL_COLUMNS.get(b_type, EXCEL_COLUMNS["KRSTNE"])
        schema = SCHEMA_FIELDS.get(b_type, SCHEMA_FIELDS["KRSTNE"])
        
        # Ustvarimo mapiranje med imenom stolpca in JSON ključem
        col_to_json_key = {c[1]: c[0] for c in schema}

        for rec in records:
            zp_value = rec.get("zp_st")
            zp_st = "" if zp_value is None else str(zp_value).replace("*", "").strip()
            row_data = {}
            for col in excel_cols:
                if col == "župnija": row_data[col] = meta["župnija"]
                elif col == "knjiga": row_data[col] = meta["knjiga"]
                elif col == "slika": row_data[col] = slika_val
                elif col == "zp. št.": row_data[col] = zp_st
                else: 
                    json_key = col_to_json_key.get(col)
                    value = rec.get(json_key) if json_key else None
                    row_data[col] = "" if value is None else str(value)
                
            parsed_rows.append(row_data)
        return parsed_rows

    def update_surname_statistics(self, all_data, workbook):
        surnames_count = {}
        for row in all_data:
            for key in ["priimek očeta", "alt. priimek očeta", "priimek matere", "alt. priimek matere", "priimek ženina", "priimek neveste", "priimek pokojnika"]:
                val = row.get(key, "").strip()
                if val and val.lower() != "neznano":
                    surnames_count[val] = surnames_count.get(val, 0) + 1
        
        if not surnames_count: return
        sorted_surnames = sorted(surnames_count.items(), key=lambda x: x[1], reverse=True)
        ws_stat = workbook.create_sheet(title="Statistika priimkov")
        ws_stat.append(["Priimek", "Število pojavitev"])
        for surname, count in sorted_surnames: ws_stat.append([surname, count])

    def start_convert_json_to_excel(self):
        threading.Thread(target=self.convert_json_to_excel, daemon=True).start()

    def convert_json_to_excel(self):
        root_dir = self.root_folder_path.get()
        if not root_dir or not os.path.isdir(root_dir): 
            self.root.after(0, lambda: messagebox.showerror("Napaka", "Izberite glavni direktorij!"))
            return

        self.root.after(0, lambda: self.uvoz_log("Pregledujem direktorije in obdelujem JSON podatke... (V Ozadju)"))
        data_by_type = {"KRSTNE": [], "POROCNE": [], "KNJIGE_MRTVIH": []}

        for current_path, dirs, files in os.walk(root_dir):
            if "_source.txt" in files:
                meta = {"župnija": "Neznano", "knjiga": "Neznano", "vrsta": "KRSTNE"}
                try:
                    with open(os.path.join(current_path, "_source.txt"), "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("Župnija:"): meta["župnija"] = line.replace("Župnija:", "").strip()
                            elif line.startswith("Knjiga:"): meta["knjiga"] = line.replace("Knjiga:", "").strip()
                            elif line.startswith("Vrsta:"): meta["vrsta"] = line.replace("Vrsta:", "").strip()
                except Exception as e:
                    self.root.after(0, lambda e=e: self.uvoz_log(f"Napaka pri branju _source.txt: {e}"))
                    
                b_type = "KRSTNE"
                if "POROCNE" in meta["vrsta"]: b_type = "POROCNE"
                elif "MRTVIH" in meta["vrsta"]: b_type = "KNJIGE_MRTVIH"
                meta["vrsta"] = b_type 

                data_files = [f for f in files if f.endswith(".txt") and not f.startswith("_source")]
                if data_files:
                    for filename in data_files:
                        try:
                            rows = self.parse_json_content(os.path.join(current_path, filename), filename, meta)
                            data_by_type[b_type].extend(rows)
                        except Exception as e:
                            self.root.after(0, lambda fn=filename, e=e: self.uvoz_log(f"Preskočeno - {fn}: {e}"))

        total_records = sum(len(lst) for lst in data_by_type.values())
        if total_records == 0: 
            self.root.after(0, lambda: messagebox.showwarning("Opozorilo", "Ni bilo uspešno prebranih zapisov!"))
            return

        output_file = self.excel_output_path.get()
        try:
            wb = openpyxl.Workbook()
            if "Sheet" in wb.sheetnames: wb.remove(wb["Sheet"])
            
            all_rows_for_stats = []
            for b_type, cols in EXCEL_COLUMNS.items():
                if data_by_type[b_type]:
                    ws = wb.create_sheet(title=b_type)
                    ws.append(cols)
                    for row in data_by_type[b_type]:
                        ws.append([row.get(col, "") for col in cols])
                        all_rows_for_stats.append(row)
            
            self.update_surname_statistics(all_rows_for_stats, wb)
            wb.save(output_file)
            self.root.after(0, lambda: self.uvoz_log(f"\nUspešno ustvarjen Excel: {output_file} (Skupaj {total_records} zapisov)."))
            self.root.after(0, lambda: messagebox.showinfo("Uspeh", "Excel uspešno shranjen s statistiko!"))
        except Exception as e:
            self.root.after(0, lambda e=e: self.uvoz_log(f"Napaka shranjevanja: {e}"))
            self.root.after(0, lambda e=e: messagebox.showerror("Napaka", f"Napaka: {e}"))

    def start_import_to_local_db(self):
         threading.Thread(target=self.import_to_local_db, daemon=True).start()

    def import_to_local_db(self):
        excel_file = self.excel_output_path.get()
        if not os.path.exists(excel_file): 
            self.root.after(0, lambda: messagebox.showerror("Napaka", "Excel datoteka ne obstaja!"))
            return
            
        db_file = self.db_path.get()
        self.root.after(0, lambda: self.uvoz_log(f"Uvažam v LOKALNO bazo: {db_file}... (V ozadju)"))
        self.root.after(0, lambda: self.uvoz_progress.config(value=0))

        try:
            wb = openpyxl.load_workbook(excel_file)
            
            # Izračun vrstic za progress bar
            total_rows = sum(wb[sheet].max_row - 1 for sheet in ["KRSTNE", "POROCNE", "KNJIGE_MRTVIH"] if sheet in wb.sheetnames and wb[sheet].max_row > 1)
            self.root.after(0, lambda: self.uvoz_progress.config(maximum=max(1, total_rows)))

            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            for b_type in ["KRSTNE", "POROCNE", "KNJIGE_MRTVIH"]:
                fields = SCHEMA_FIELDS[b_type]
                cols_def = ", ".join([f"{f[0]} {f[2]}" for f in fields])
                table_name = {"KRSTNE": "krsti", "POROCNE": "poroke", "KNJIGE_MRTVIH": "mrtvi"}[b_type]
                
                query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {cols_def}, UNIQUE(zupnija, knjiga, slika, zp_st))"
                cursor.execute(query)
            
            new_records, skipped_records, err_records, processed_rows = 0, 0, 0, 0
            for sheet_name in ["KRSTNE", "POROCNE", "KNJIGE_MRTVIH"]:
                if sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    header = []
                    fields = SCHEMA_FIELDS[sheet_name]
                    json_keys = [f[0] for f in fields]
                    excel_names = [f[1] for f in fields]
                    table_name = {"KRSTNE": "krsti", "POROCNE": "poroke", "KNJIGE_MRTVIH": "mrtvi"}[sheet_name]

                    placeholders = ",".join(["?"] * len(json_keys))
                    query = f"INSERT INTO {table_name} ({','.join(json_keys)}) VALUES ({placeholders})"

                    for i, row in enumerate(ws.iter_rows(values_only=True)):
                        if i == 0:
                            header = [str(c) if c else "" for c in row]
                            continue
                        r = {header[j]: (val if val is not None else "") for j, val in enumerate(row)}
                        
                        values = [str(r.get(col_name, "")) for col_name in excel_names]
                        try:
                            cursor.execute(query, values)
                            new_records += 1
                        except sqlite3.IntegrityError:
                            skipped_records += 1
                        except Exception as e:
                            err_records += 1
                            self.root.after(0, lambda e=e, row_id=r.get("zp. št.", "?"): self.uvoz_log(f"Napaka pri zapisu št. {row_id}: {e}"))
                        
                        processed_rows += 1
                        if processed_rows % 20 == 0:
                            self.root.after(0, lambda v=processed_rows: self.uvoz_progress.config(value=v))
            
            conn.commit()
            conn.close()
            self.root.after(0, lambda: self.uvoz_progress.config(value=total_rows))
            msg = f"LOKALNI UVOZ ZAKLJUČEN. Novi: {new_records}, Dvojniki: {skipped_records}, Napake: {err_records}"
            self.root.after(0, lambda msg=msg: self.uvoz_log(msg))
            self.root.after(0, lambda: messagebox.showinfo("Uvoz končan", "Podatki uspešno uvoženi v lokalno bazo."))
        except Exception as e: 
            self.root.after(0, lambda e=e: messagebox.showerror("Napaka", f"Napaka pri lokalnem uvozu: {e}"))
