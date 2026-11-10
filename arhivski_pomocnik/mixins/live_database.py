"""LiveDatabaseMixin: funkcionalni sklop Arhivskega pomočnika."""
from ..common import *
from ..constants import *
from ..helpers import *

class LiveDatabaseMixin:
    def import_to_live_db(self):
        excel_file = self.excel_output_path.get()
        if not os.path.exists(excel_file):
            self.root.after(0, lambda: messagebox.showerror("Napaka", "Excel datoteka ne obstaja!"))
            return

        self.root.after(0, lambda: self.uvoz_log(
            f"Povezujem se na MySQL strežnik {self.live_db_config['host']} in začenjam uvoz... (V ozadju)"
        ))
        self.root.after(0, lambda: self.uvoz_progress.config(value=0))

        conn = None
        try:
            wb = openpyxl.load_workbook(excel_file, data_only=True)
            table_names = {"KRSTNE": "krsti", "POROCNE": "poroke", "KNJIGE_MRTVIH": "mrtvi"}
            total_rows = sum(
                wb[sheet].max_row - 1
                for sheet in table_names
                if sheet in wb.sheetnames and wb[sheet].max_row > 1
            )
            self.root.after(0, lambda: self.uvoz_progress.config(maximum=max(1, total_rows)))

            conn = self.get_live_db_connection()
            cursor = conn.cursor()
            new_records = updated_records = unchanged_records = err_records = processed_rows = 0

            for sheet_name, table_name in table_names.items():
                if sheet_name not in wb.sheetnames:
                    continue
                ws = wb[sheet_name]
                rows_iter = ws.iter_rows(values_only=True)
                header_row = next(rows_iter, None)
                if not header_row:
                    continue
                header = [str(cell) if cell is not None else "" for cell in header_row]
                required = {"zap. št. v knjigi", "zap. št. na strani", "župnija", "knjiga", "slika"}
                missing = sorted(required - set(header))
                if missing:
                    raise RuntimeError(
                        f"Excel list {sheet_name} je iz stare različice. Manjkajo stolpci: "
                        + ", ".join(missing)
                        + ". Ponovno zaženi pretvorbo JSON v Excel."
                    )

                fields = SCHEMA_FIELDS[sheet_name]
                json_keys = [field[0] for field in fields]
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                db_columns = {
                    column.get("Field") if isinstance(column, dict) else column[0]
                    for column in cursor.fetchall()
                }
                missing_db_columns = sorted(set(json_keys) - db_columns)
                if missing_db_columns:
                    raise RuntimeError(
                        f"MySQL tabela '{table_name}' ima staro strukturo. "
                        f"Manjkajo stolpci: {', '.join(missing_db_columns)}. "
                        "Odstrani stare testne tabele in jih ponovno ustvari z gumbom 'Ustvari tabele'."
                    )
                excel_names = [field[1] for field in fields]
                placeholders = ",".join(["%s"] * len(json_keys))
                mutable_keys = [
                    key for key in json_keys
                    if key not in ("zupnija", "knjiga", "slika", "vpis_st_na_strani")
                ]
                update_sql = ", ".join(
                    f"{key}=COALESCE(NULLIF(VALUES({key}), ''), {key})"
                    for key in mutable_keys
                )
                query = (
                    f"INSERT INTO {table_name} ({','.join(json_keys)}) VALUES ({placeholders}) "
                    "ON DUPLICATE KEY UPDATE " + update_sql
                )

                zupnija_idx = excel_names.index("župnija") if "župnija" in excel_names else -1

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

                        if zupnija_idx != -1:
                            values[zupnija_idx] = values[zupnija_idx].strip().lower() or "neznana_zupnija"

                        identity = (
                            values[json_keys.index("zupnija")],
                            values[json_keys.index("knjiga")],
                            values[json_keys.index("slika")],
                            values[json_keys.index("vpis_st_na_strani")],
                        )
                        cursor.execute(
                            f"SELECT {','.join(json_keys)} FROM {table_name} "
                            "WHERE zupnija=%s AND knjiga=%s AND slika=%s AND vpis_st_na_strani=%s LIMIT 1",
                            identity,
                        )
                        existing_row = cursor.fetchone()
                        if existing_row is None:
                            new_records += 1
                        else:
                            has_changes = any(
                                str(values[json_keys.index(key)]).strip() != ""
                                and str(values[json_keys.index(key)]) != str(existing_row.get(key) or "")
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
                    if processed_rows % 20 == 0:
                        self.root.after(0, lambda v=processed_rows: self.uvoz_progress.config(value=v))

            conn.commit()
            self.root.after(0, lambda: self.uvoz_progress.config(value=total_rows))
            msg = (
                f"ŽIVI UVOZ ZAKLJUČEN. Novi: {new_records}, Posodobljeni: {updated_records}, "
                f"Nespremenjeni: {unchanged_records}, Napake: {err_records}"
            )
            self.root.after(0, lambda msg=msg: self.uvoz_log(msg))
            self.root.after(0, lambda: messagebox.showinfo(
                "Uvoz končan",
                f"Novi: {new_records}\nPosodobljeni: {updated_records}\n"
                f"Nespremenjeni: {unchanged_records}\nNapake: {err_records}"
            ))
        except Exception as e:
            self.root.after(0, lambda e=e: self.uvoz_log(f"Napaka pri uvozu v živo bazo: {e}"))
            self.root.after(0, lambda e=e: messagebox.showerror("Napaka z bazo", str(e)))
        finally:
            if conn is not None:
                conn.close()

    def open_live_db_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Nastavitve Žive Baze (MySQL/MariaDB)")
        settings_win.geometry("420x350")
        ttk.Label(settings_win, text="Host / IP strežnika:").pack(pady=(10,0))
        host_entry = ttk.Entry(settings_win, width=40)
        host_entry.insert(0, self.live_db_config["host"]); host_entry.pack()
        ttk.Label(settings_win, text="Uporabniško ime (User):").pack(pady=(10,0))
        user_entry = ttk.Entry(settings_win, width=40)
        user_entry.insert(0, self.live_db_config["user"]); user_entry.pack()
        ttk.Label(settings_win, text="Geslo:").pack(pady=(10,0))
        pwd_entry = ttk.Entry(settings_win, width=40, show="*")
        pwd_entry.insert(0, self.live_db_config["password"]); pwd_entry.pack()
        ttk.Label(settings_win, text="Ime baze (Database):").pack(pady=(10,0))
        db_entry = ttk.Entry(settings_win, width=40)
        db_entry.insert(0, self.live_db_config["database"]); db_entry.pack()

        def test_connection():
            try:
                conn = pymysql.connect(
                    host=host_entry.get(), user=user_entry.get(), password=pwd_entry.get(),
                    database=db_entry.get(), port=int(self.live_db_config["port"]), connect_timeout=5
                )
                conn.close()
                messagebox.showinfo("Uspeh", "Povezava na strežnik je uspešna in podatki za prijavo delujejo!")
            except Exception as e:
                messagebox.showerror("Napaka pri povezavi", f"Neuspešna povezava z bazo:\n{e}")

        def save_settings_db():
            self.live_db_config["host"] = host_entry.get()
            self.live_db_config["user"] = user_entry.get()
            self.live_db_config["password"] = pwd_entry.get()
            self.live_db_config["database"] = db_entry.get()
            
            global_settings = load_settings()
            global_settings["LiveDB"] = self.live_db_config
            save_settings(global_settings)
            
            self.uvoz_log("Nastavitve za živo bazo so trajno shranjene.")
            settings_win.destroy()
            
        btn_frame = ttk.Frame(settings_win)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Preveri povezavu", command=test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Shrani", command=save_settings_db).pack(side=tk.LEFT, padx=5)

    def get_live_db_connection(self):
        if not MYSQL_AVAILABLE: raise Exception("Paket PyMySQL ni nameščen!")
        return pymysql.connect(
            host=self.live_db_config["host"], 
            user=self.live_db_config["user"], 
            password=self.live_db_config["password"], 
            database=self.live_db_config["database"], 
            port=int(self.live_db_config["port"]),
            charset='utf8mb4',
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )

    def start_create_live_db_tables(self):
        threading.Thread(target=self.create_live_db_tables, daemon=True).start()

    def create_live_db_tables(self):
        try:
            conn = self.get_live_db_connection()
            cursor = conn.cursor()
            
            for b_type in ["KRSTNE", "POROCNE", "KNJIGE_MRTVIH"]:
                fields = SCHEMA_FIELDS[b_type]
                cols_def = ", ".join([f"{f[0]} {f[2]}" for f in fields])
                table_name = {"KRSTNE": "krsti", "POROCNE": "poroke", "KNJIGE_MRTVIH": "mrtvi"}[b_type]
                
                query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY, {cols_def},
                        UNIQUE KEY unique_zapis (zupnija(75), knjiga(75), slika(20), vpis_st_na_strani)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """
                cursor.execute(query)
            
            conn.commit()
            conn.close()
            self.root.after(0, lambda: self.uvoz_log("Struktura vseh tabel (krsti, poroke, mrtvi) je uspešno ustvarjena na živi bazi!"))
            self.root.after(0, lambda: messagebox.showinfo("Uspeh", "Tabele so uspešno kreirane na strežniku."))
        except Exception as e:
            self.root.after(0, lambda e=e: self.uvoz_log(f"Napaka pri povezavi/kreiranju tabel: {e}"))
            self.root.after(0, lambda e=e: messagebox.showerror("Napaka z bazo", str(e)))

    def start_import_to_live_db(self):
         threading.Thread(target=self.import_to_live_db, daemon=True).start()