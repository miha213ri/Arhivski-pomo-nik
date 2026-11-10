"""ImportExportMixin: funkcionalni sklop Arhivskega pomočnika."""
from ..common import *
from ..constants import *
from ..helpers import *

def _natural_sort_key(value):
    return tuple(
        (1, int(part)) if part.isdigit() else (0, part.casefold())
        for part in re.split(r"(\d+)", str(value))
    )

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
        
        ttk.Button(frame_live, text="Nastavitve Povezave", command=self.open_live_db_settings, width=20).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(frame_live, text="Ustvari tabele", command=self.start_create_live_db_tables, width=15).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(frame_live, text="Uvozi v Živo Bazo", command=self.start_import_to_live_db, width=20).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(frame_live, text="Uvozi tuj Excel v ŽB", command=self.start_import_external_excel_to_live_db, width=20).grid(row=0, column=3, padx=4, pady=4)

        if not MYSQL_AVAILABLE:
            ttk.Label(frame_live, text="⚠️ Manjka PyMySQL!", foreground="red").grid(row=0, column=4, padx=6, pady=4)

        frame_log = ttk.LabelFrame(self.tab_uvoz, text=" Poročilo o izvedbi in kontroli ", padding=12)
        frame_log.pack(fill="both", expand=True, padx=10, pady=8)

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
                dirs.sort(key=_natural_sort_key)
                files.sort(key=_natural_sort_key)
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
                    dirs.sort(key=_natural_sort_key)
                    files.sort(key=_natural_sort_key)
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
        filename_stem = os.path.splitext(os.path.basename(filename))[0]
        page_match = re.search(r"_(\d+)$", filename_stem)
        slika_val = page_match.group(1) if page_match else "Neznano"
        
        b_type = meta.get("vrsta", "KRSTNE")
        excel_cols = EXCEL_COLUMNS.get(b_type, EXCEL_COLUMNS["KRSTNE"])
        schema = SCHEMA_FIELDS.get(b_type, SCHEMA_FIELDS["KRSTNE"])
        
        col_to_json_key = {c[1]: c[0] for c in schema}

        for rec in records:
            zp_value = rec.get("zp_st")
            zp_st = "" if zp_value is None else str(zp_value).replace("*", "").strip()
            row_data = {}
            for col in excel_cols:
                if col == "župnija": row_data[col] = meta["župnija"]
                elif col == "knjiga": row_data[col] = meta["knjiga"]
                elif col == "slika": row_data[col] = slika_val
                elif col in ("zap. št. v knjigi", "zap. št. na strani"):
                    row_data[col] = ""
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
        book_counters = {}

        for current_path, dirs, files in os.walk(root_dir):
            dirs.sort(key=_natural_sort_key)
            files.sort(key=_natural_sort_key)

            if "_source.txt" not in files:
                continue

            meta = {"župnija": "Neznano", "knjiga": "Neznano", "vrsta": "KRSTNE"}
            try:
                with open(os.path.join(current_path, "_source.txt"), "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("Župnija:"):
                            meta["župnija"] = line.replace("Župnija:", "", 1).strip()
                        elif line.startswith("Knjiga:"):
                            meta["knjiga"] = line.replace("Knjiga:", "", 1).strip()
                        elif line.startswith("Vrsta:"):
                            meta["vrsta"] = line.replace("Vrsta:", "", 1).strip()
            except Exception as e:
                self.root.after(0, lambda e=e: self.uvoz_log(f"Napaka pri branju _source.txt: {e}"))
                continue

            raw_type = meta["vrsta"].upper()
            if "POROCNE" in raw_type or "POROČNE" in raw_type:
                b_type = "POROCNE"
            elif "MRTVIH" in raw_type or "MRLI" in raw_type:
                b_type = "KNJIGE_MRTVIH"
            else:
                b_type = "KRSTNE"
            meta["vrsta"] = b_type

            book_key = (
                b_type,
                meta["župnija"].strip().casefold(),
                meta["knjiga"].strip().casefold(),
            )
            book_number = book_counters.get(book_key, 0)

            data_files = sorted(
                [f for f in files if f.lower().endswith((".txt", ".json")) and not f.startswith("_source")],
                key=_natural_sort_key,
            )
            for filename in data_files:
                filepath = os.path.join(current_path, filename)
                try:
                    rows = self.parse_json_content(filepath, filename, meta)
                    for page_number, row_data in enumerate(rows, start=1):
                        book_number += 1
                        row_data["zap. št. v knjigi"] = book_number
                        row_data["zap. št. na strani"] = page_number
                    data_by_type[b_type].extend(rows)
                except Exception as e:
                    self.root.after(0, lambda fn=filename, e=e: self.uvoz_log(f"Preskočeno - {fn}: {e}"))

            book_counters[book_key] = book_number

        total_records = sum(len(lst) for lst in data_by_type.values())
        if total_records == 0:
            self.root.after(0, lambda: messagebox.showwarning("Opozorilo", "Ni bilo uspešno prebranih zapisov!"))
            return

        output_file = self.excel_output_path.get()
        try:
            wb = openpyxl.Workbook()
            if "Sheet" in wb.sheetnames:
                wb.remove(wb["Sheet"])

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
            self.root.after(0, lambda: self.uvoz_log(
                f"\nUspešno ustvarjen Excel: {output_file} (Skupaj {total_records} zapisov)."
            ))
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

        conn = None
        try:
            wb = openpyxl.load_workbook(excel_file, data_only=True)
            
            sheet_mapper = {
                "KRSTNE": "KRSTNE", "Krsti": "KRSTNE", "krsti": "KRSTNE",
                "POROCNE": "POROCNE", "Poroke": "POROCNE", "poroke": "POROCNE",
                "KNJIGE_MRTVIH": "KNJIGE_MRTVIH", "Umrli": "KNJIGE_MRTVIH", "umrli": "KNJIGE_MRTVIH"
            }

            total_rows = sum(
                wb[sheet].max_row - 1
                for sheet in wb.sheetnames
                if sheet in sheet_mapper and wb[sheet].max_row > 1
            )
            self.root.after(0, lambda: self.uvoz_progress.config(maximum=max(1, total_rows)))

            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            table_names = {"KRSTNE": "krsti", "POROCNE": "poroke", "KNJIGE_MRTVIH": "mrtvi"}

            for b_type, table_name in table_names.items():
                fields = SCHEMA_FIELDS[b_type]
                cols_def = ", ".join([f"{field[0]} {field[2]}" for field in fields])
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {table_name} ("
                    f"id INTEGER PRIMARY KEY AUTOINCREMENT, {cols_def}, "
                    "UNIQUE(zupnija, knjiga, slika, vpis_st_na_strani))"
                )
                cursor.execute(f"PRAGMA table_info({table_name})")
                db_columns = {info[1] for info in cursor.fetchall()}
                required_db_columns = {field[0] for field in fields}
                missing_db_columns = sorted(required_db_columns - db_columns)
                if missing_db_columns:
                    raise RuntimeError(
                        f"Lokalna baza '{table_name}' ima staro strukturo. "
                        f"Manjkajo stolpci: {', '.join(missing_db_columns)}. "
                        "Zapri program in izbriši staro datoteko SQLite baze, nato ponovi uvoz."
                    )

            new_records = updated_records = unchanged_records = err_records = processed_rows = 0

            for actual_sheet_name in wb.sheetnames:
                if actual_sheet_name not in sheet_mapper:
                    continue
                
                b_type = sheet_mapper[actual_sheet_name]
                table_name = table_names[b_type]
                
                ws = wb[actual_sheet_name]
                rows_iter = ws.iter_rows(values_only=True)
                header_row = next(rows_iter, None)
                if not header_row:
                    continue
                header = [str(cell) if cell is not None else "" for cell in header_row]
                required = {"zap. št. v knjigi", "zap. št. na strani", "župnija", "knjiga", "slika"}
                missing = sorted(required - set(header))
                if missing:
                    raise RuntimeError(
                        f"Excel list {actual_sheet_name} je iz stare različice. Manjkajo stolpci: "
                        + ", ".join(missing)
                        + ". Ponovno zaženi pretvorbo JSON v Excel."
                    )

                fields = SCHEMA_FIELDS[b_type]
                json_keys = [field[0] for field in fields]
                excel_names = [field[1] for field in fields]
                placeholders = ",".join(["?"] * len(json_keys))
                mutable_keys = [
                    key for key in json_keys
                    if key not in ("zupnija", "knjiga", "slika", "vpis_st_na_strani")
                ]
                update_sql = ", ".join(
                    f"{key} = CASE WHEN excluded.{key} IS NOT NULL "
                    f"AND TRIM(CAST(excluded.{key} AS TEXT)) <> '' "
                    f"THEN excluded.{key} ELSE {table_name}.{key} END"
                    for key in mutable_keys
                )
                query = (
                    f"INSERT INTO {table_name} ({','.join(json_keys)}) VALUES ({placeholders}) "
                    "ON CONFLICT(zupnija, knjiga, slika, vpis_st_na_strani) "
                    f"DO UPDATE SET {update_sql}"
                )

                for row in rows_iter:
                    r = {
                        header[j]: (value if value is not None else "")
                        for j, value in enumerate(row)
                        if j < len(header)
                    }
                    try:
                        values = []
                        for field_key, column_name in zip(json_keys, excel_names):
                            value = r.get(column_name, "")
                            if field_key in ("vpis_st_knjige", "vpis_st_na_strani"):
                                if value is None or str(value).strip() == "":
                                    raise ValueError(f"Manjka interna zaporedna številka v stolpcu '{column_name}'.")
                                number = float(value)
                                if not number.is_integer() or number < 1:
                                    raise ValueError(f"Neveljavna zaporedna številka: {value}")
                                value = int(number)
                            else:
                                value = "" if value is None else str(value)
                            values.append(value)

                        row_values = dict(zip(json_keys, values))
                        row_values["zupnija"] = row_values["zupnija"].strip().casefold() or "neznana_zupnija"
                        values[json_keys.index("zupnija")] = row_values["zupnija"]
                        identity = (
                            row_values["zupnija"], row_values["knjiga"],
                            row_values["slika"], row_values["vpis_st_na_strani"],
                        )
                        cursor.execute(
                            f"SELECT {','.join(json_keys)} FROM {table_name} "
                            "WHERE zupnija=? AND knjiga=? AND slika=? AND vpis_st_na_strani=? LIMIT 1",
                            identity,
                        )
                        existing_row = cursor.fetchone()
                        if existing_row is None:
                            new_records += 1
                        else:
                            existing_values = dict(zip(json_keys, existing_row))
                            has_changes = any(
                                str(row_values.get(key, "")).strip() != ""
                                and str(row_values.get(key, "")) != str(existing_values.get(key, "") or "")
                                for key in mutable_keys
                            )
                            if has_changes:
                                updated_records += 1
                            else:
                                unchanged_records += 1
                        cursor.execute(query, values)
                    except Exception as e:
                        err_records += 1
                        row_id = r.get("zap. št. v knjigi", r.get("zp. št.", "?"))
                        self.root.after(0, lambda e=e, row_id=row_id: self.uvoz_log(
                            f"Napaka pri zapisu št. {row_id}: {e}"
                        ))

                    processed_rows += 1
                    
                    # POPRAVEK: Vmesno shranjevanje SQLite transakcije na vsakih 50 zapisov
                    if processed_rows % 50 == 0:
                        conn.commit()
                        self.root.after(0, lambda v=processed_rows: self.uvoz_progress.config(value=v))

            conn.commit()
            self.root.after(0, lambda: self.uvoz_progress.config(value=total_rows))
            msg = (
                f"LOKALNI UVOZ ZAKLJUČEN. Novi: {new_records}, "
                f"Posodobljeni: {updated_records}, Nespremenjeni: {unchanged_records}, Napake: {err_records}"
            )
            self.root.after(0, lambda msg=msg: self.uvoz_log(msg))
            self.root.after(0, lambda: messagebox.showinfo(
                "Uvoz končan",
                f"Novi: {new_records}\nPosodobljeni: {updated_records}\n"
                f"Nespremenjeni: {unchanged_records}\nNapake: {err_records}"
            ))
        except Exception as e:
            self.root.after(0, lambda e=e: self.uvoz_log(f"Napaka pri lokalnem uvozu: {e}"))
            self.root.after(0, lambda e=e: messagebox.showerror("Napaka", f"Napaka pri lokalnem uvozu: {e}"))
        finally:
            if conn is not None:
                conn.close()

    def start_import_external_excel_to_live_db(self):
        try:
            file_path = filedialog.askopenfilename(
                title="Izberi zunanji Excel za uvoz v MySQL",
                filetypes=[("Excel datoteke", "*.xlsx")]
            )
            if file_path:
                threading.Thread(target=self.import_to_live_db, args=(file_path,), daemon=True).start()
        except Exception as e:
            self.uvoz_log(f"Napaka pri odpiranju okna: {e}")

    def start_import_to_live_db(self):
        excel_file = self.excel_output_path.get()
        threading.Thread(target=self.import_to_live_db, args=(excel_file,), daemon=True).start()

    def import_to_live_db(self, excel_file):
        if not MYSQL_AVAILABLE:
            self.root.after(0, lambda: messagebox.showerror("Napaka", "PyMySQL ni na voljo. MySQL uvoz ni mogoč."))
            return
            
        if not os.path.exists(excel_file):
            self.root.after(0, lambda: messagebox.showerror("Napaka", "Izbrana Excel datoteka ne obstaja!"))
            return

        settings = load_settings()
        db_conf = settings.get("LiveDB", {})
        if not all([db_conf.get("host"), db_conf.get("user"), db_conf.get("database")]):
            self.root.after(0, lambda: messagebox.showerror("Napaka", "Preverite nastavitve MySQL baze!"))
            return

        self.root.after(0, lambda: self.uvoz_log(f"Uvažam v ŽIVO (MySQL) bazo datoteko: {os.path.basename(excel_file)}..."))
        self.root.after(0, lambda: self.uvoz_progress.config(value=0))

        conn = None
        try:
            wb = openpyxl.load_workbook(excel_file, data_only=True)
            
            sheet_mapper = {
                "KRSTNE": "KRSTNE", "Krsti": "KRSTNE", "krsti": "KRSTNE",
                "POROCNE": "POROCNE", "Poroke": "POROCNE", "poroke": "POROCNE",
                "KNJIGE_MRTVIH": "KNJIGE_MRTVIH", "Umrli": "KNJIGE_MRTVIH", "umrli": "KNJIGE_MRTVIH"
            }

            total_rows = sum(
                wb[sheet].max_row - 1
                for sheet in wb.sheetnames
                if sheet in sheet_mapper and wb[sheet].max_row > 1
            )
            self.root.after(0, lambda: self.uvoz_progress.config(maximum=max(1, total_rows)))

            conn = pymysql.connect(
                host=db_conf["host"], user=db_conf["user"], password=db_conf.get("password", ""),
                database=db_conf["database"], port=int(db_conf.get("port", 3306)),
                charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
            )
            
            with conn.cursor() as cursor:
                table_names = {"KRSTNE": "krsti", "POROCNE": "poroke", "KNJIGE_MRTVIH": "mrtvi"}
                new_records = updated_records = unchanged_records = err_records = processed_rows = 0

                for t_name in table_names.values():
                    cursor.execute(f"SHOW TABLES LIKE '{t_name}'")
                    if not cursor.fetchone():
                        raise RuntimeError(f"Tabela '{t_name}' ne obstaja v Živi Bazi! Najprej klikni 'Ustvari tabele'.")

                for actual_sheet_name in wb.sheetnames:
                    if actual_sheet_name not in sheet_mapper:
                        continue
                        
                    b_type = sheet_mapper[actual_sheet_name]
                    table_name = table_names[b_type]
                    
                    ws = wb[actual_sheet_name]
                    rows_iter = ws.iter_rows(values_only=True)
                    header_row = next(rows_iter, None)
                    if not header_row:
                        continue
                        
                    header = [str(cell) if cell is not None else "" for cell in header_row]
                    required = {"župnija"} 
                    missing = sorted(required - set(header))
                    if missing:
                        self.root.after(0, lambda ms=missing, ash=actual_sheet_name: self.uvoz_log(f"Napaka: List {ash} nima stolpcev {ms}."))
                        continue

                    fields = SCHEMA_FIELDS[b_type]
                    json_keys = [field[0] for field in fields]
                    excel_names = [field[1] for field in fields]
                    mutable_keys = [k for k in json_keys if k not in ("zupnija", "knjiga", "slika", "vpis_st_na_strani")]
                    
                    placeholders = ", ".join(["%s"] * len(json_keys))
                    update_sql = ", ".join([f"{key} = VALUES({key})" for key in mutable_keys])
                    
                    query = f"""
                        INSERT INTO {table_name} ({','.join(json_keys)}) 
                        VALUES ({placeholders}) 
                        ON DUPLICATE KEY UPDATE {update_sql}
                    """

                    for row in rows_iter:
                        r = {header[j]: (value if value is not None else "") for j, value in enumerate(row) if j < len(header)}
                        try:
                            values = []
                            for field_key, column_name in zip(json_keys, excel_names):
                                value = r.get(column_name, "")
                                if field_key in ("vpis_st_knjige", "vpis_st_na_strani"):
                                    if value is None or str(value).strip() == "":
                                        value = 1
                                    else:
                                        value = int(float(value))
                                else:
                                    value = "" if value is None else str(value)
                                values.append(value)

                            row_values = dict(zip(json_keys, values))
                            row_values["zupnija"] = row_values.get("zupnija", "neznana_zupnija").strip().casefold()
                            row_values["knjiga"] = row_values.get("knjiga", "neznana_knjiga").strip().casefold()
                            row_values["slika"] = row_values.get("slika", "1").strip().casefold()
                            
                            values[json_keys.index("zupnija")] = row_values["zupnija"]
                            values[json_keys.index("knjiga")] = row_values["knjiga"]
                            values[json_keys.index("slika")] = row_values["slika"]
                            
                            identity = (row_values["zupnija"], row_values["knjiga"], row_values["slika"], row_values["vpis_st_na_strani"])
                            
                            cursor.execute(f"SELECT {','.join(json_keys)} FROM {table_name} WHERE zupnija=%s AND knjiga=%s AND slika=%s AND vpis_st_na_strani=%s LIMIT 1", identity)
                            existing_row = cursor.fetchone()
                            
                            if existing_row is None:
                                new_records += 1
                            else:
                                updated_records += 1
                                
                            cursor.execute(query, tuple(values))
                        except Exception as e:
                            err_records += 1
                            row_id = r.get("zp. št.", "?")
                            self.root.after(0, lambda e=e, row_id=row_id: self.uvoz_log(f"SQL Napaka pri vrstici št. {row_id}: {e}"))

                        processed_rows += 1
                        
                        # POPRAVEK: Vmesno shranjevanje MySQL transakcije na vsakih 50 zapisov
                        if processed_rows % 50 == 0:
                            conn.commit()
                            self.root.after(0, lambda v=processed_rows: self.uvoz_progress.config(value=v))

                conn.commit()
                self.root.after(0, lambda: self.uvoz_progress.config(value=total_rows))
                msg = f"MYSQL UVOZ ZAKLJUČEN. Novi: {new_records}, Posodobljeni: {updated_records}, Napake: {err_records}"
                self.root.after(0, lambda msg=msg: self.uvoz_log(msg))
                self.root.after(0, lambda: messagebox.showinfo("MySQL uvoz končan", msg))

        except Exception as e:
            self.root.after(0, lambda e=e: self.uvoz_log(f"Napaka pri MySQL uvozu: {e}"))
            self.root.after(0, lambda e=e: messagebox.showerror("Napaka", f"Napaka pri MySQL uvozu:\n{e}"))
        finally:
            if conn is not None:
                conn.close()