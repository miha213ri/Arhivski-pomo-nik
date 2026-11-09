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
            
        self.root.after(0, lambda: self.uvoz_log(f"Povezujem se na MySQL strežnik {self.live_db_config['host']} in začenjam uvoz... (V ozadju)"))
        self.root.after(0, lambda: self.uvoz_progress.config(value=0))

        try:
            wb = openpyxl.load_workbook(excel_file)
            
            # Izračun vrstic za progress bar
            total_rows = sum(wb[sheet].max_row - 1 for sheet in ["KRSTNE", "POROCNE", "KNJIGE_MRTVIH"] if sheet in wb.sheetnames and wb[sheet].max_row > 1)
            self.root.after(0, lambda: self.uvoz_progress.config(maximum=max(1, total_rows)))

            conn = self.get_live_db_connection()
            cursor = conn.cursor()
            new_records, skipped_records, err_records, processed_rows = 0, 0, 0, 0
            
            for sheet_name in ["KRSTNE", "POROCNE", "KNJIGE_MRTVIH"]:
                if sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    header = []
                    fields = SCHEMA_FIELDS[sheet_name]
                    json_keys = [f[0] for f in fields]
                    excel_names = [f[1] for f in fields]
                    table_name = {"KRSTNE": "krsti", "POROCNE": "poroke", "KNJIGE_MRTVIH": "mrtvi"}[sheet_name]

                    placeholders = ",".join(["%s"] * len(json_keys))
                    query = f"INSERT IGNORE INTO {table_name} ({','.join(json_keys)}) VALUES ({placeholders})"
                    
                    for i, row in enumerate(ws.iter_rows(values_only=True)):
                        if i == 0:
                            header = [str(c) if c else "" for c in row]
                            continue
                        r = {header[j]: (val if val is not None else "") for j, val in enumerate(row)}
                        
                        values = [str(r.get(col_name, "")) for col_name in excel_names]
                        try:
                            cursor.execute(query, values)
                            if cursor.rowcount > 0: new_records += 1
                            else: skipped_records += 1
                        except Exception as e:
                            err_records += 1
                            self.root.after(0, lambda e=e, row_id=r.get("zp. št.", "?"): self.uvoz_log(f"Napaka pri zapisu št. {row_id}: {e}"))
                        
                        processed_rows += 1
                        if processed_rows % 20 == 0:
                            self.root.after(0, lambda v=processed_rows: self.uvoz_progress.config(value=v))

            conn.commit()
            conn.close()
            self.root.after(0, lambda: self.uvoz_progress.config(value=total_rows))
            msg = f"ŽIVI UVOZ ZAKLJUČEN. Novi: {new_records}, Dvojniki (ali preskočeni): {skipped_records}, Napake: {err_records}"
            self.root.after(0, lambda msg=msg: self.uvoz_log(msg))
            self.root.after(0, lambda: messagebox.showinfo("Uvoz končan", f"Podatki poslani na MySQL strežnik!\nDodani: {new_records}\nPreskočeni: {skipped_records}"))
        except Exception as e:
            self.root.after(0, lambda e=e: self.uvoz_log(f"Napaka pri uvozu v živo bazo: {e}"))
            self.root.after(0, lambda e=e: messagebox.showerror("Napaka z bazo", str(e)))

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
                messagebox.showinfo("Uspeh", "Povezava na strežnik je uspešna!")
            except Exception as e:
                messagebox.showerror("Napaka", f"Neuspešna povezava:\n{e}")

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
        ttk.Button(btn_frame, text="Preveri povezavo", command=test_connection).pack(side=tk.LEFT, padx=5)
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
                        UNIQUE KEY unique_zapis (zupnija, knjiga, slika, zp_st)
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
