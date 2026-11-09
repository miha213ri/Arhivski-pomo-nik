"""MergeMixin: funkcionalni sklop Arhivskega pomočnika."""
from ..common import *
from ..constants import *
from ..helpers import *

class MergeMixin:
    def build_zdruzevanje_tab(self):
        frame_merge_top = ttk.LabelFrame(self.tab_zdruzevanje, text=" Izbira datotek za združevanje ", padding=15)
        frame_merge_top.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_merge_top, text="Izberi več Excel (.xlsx) datotek, ki jih želiš združiti v eno glavno bazo/Excel:").pack(anchor="w", pady=(0, 5))
        
        btn_frame = ttk.Frame(frame_merge_top)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Dodaj Excel datoteke...", command=self.add_merge_files).pack(side="left", padx=(0, 10))
        ttk.Button(btn_frame, text="Počisti seznam", command=self.clear_merge_files).pack(side="left")

        frame_list = ttk.LabelFrame(self.tab_zdruzevanje, text=" Seznam datotek za združitev ", padding=10)
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)

        self.merge_listbox = tk.Listbox(frame_list, selectmode=tk.EXTENDED, height=8)
        self.merge_listbox.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        list_scroll = ttk.Scrollbar(frame_list, orient="vertical", command=self.merge_listbox.yview)
        list_scroll.pack(side="right", fill="y")
        self.merge_listbox.configure(yscrollcommand=list_scroll.set)

        frame_merge_bottom = ttk.LabelFrame(self.tab_zdruzevanje, text=" Izhodna združena datoteka ", padding=15)
        frame_merge_bottom.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_merge_bottom, text="Združena Excel datoteka:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame_merge_bottom, textvariable=self.merge_output_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame_merge_bottom, text="Spremeni...", command=self.browse_merge_output).grid(row=0, column=2, pady=5)

        ttk.Button(frame_merge_bottom, text="Združi izbrane datoteke v mega Excel", command=self.start_execute_merge_files, width=45).grid(row=1, column=0, columnspan=3, pady=15)

        # DODANO: Progress bar za združevanje datotek
        self.merge_progress = ttk.Progressbar(frame_merge_bottom, orient="horizontal", mode="determinate")
        self.merge_progress.grid(row=2, column=0, columnspan=3, sticky="we", padx=5, pady=(0, 5))

    def add_merge_files(self):
        files = filedialog.askopenfilenames(title="Izberi Excel datoteke za združevanje", filetypes=[("Excel datoteke", "*.xlsx")], initialdir=self.excel_dir)
        for f in files:
            if f not in self.merge_files_list:
                self.merge_files_list.append(f)
                self.merge_listbox.insert(tk.END, f)

    def clear_merge_files(self):
        self.merge_files_list.clear()
        self.merge_listbox.delete(0, tk.END)

    def browse_merge_output(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel datoteke", "*.xlsx")], initialdir=self.excel_dir)
        if file_path: self.merge_output_path.set(file_path)

    def start_execute_merge_files(self):
        threading.Thread(target=self.execute_merge_files, daemon=True).start()

    def execute_merge_files(self):
        if not self.merge_files_list: 
            self.root.after(0, lambda: messagebox.showwarning("Opozorilo", "Najprej izberi datoteke!"))
            return
        
        data_by_type = {"KRSTNE": [], "POROCNE": [], "KNJIGE_MRTVIH": []}
        seen_keys = {"KRSTNE": set(), "POROCNE": set(), "KNJIGE_MRTVIH": set()}
        
        for file_path in self.merge_files_list:
            try:
                wb = openpyxl.load_workbook(file_path)
                for b_type in ["KRSTNE", "POROCNE", "KNJIGE_MRTVIH"]:
                    if b_type in wb.sheetnames:
                        ws = wb[b_type]
                        header = []
                        for i, row in enumerate(ws.iter_rows(values_only=True)):
                            if i == 0:
                                header = [str(c) if c else "" for c in row]
                                continue
                            row_dict = {header[j]: (val if val is not None else "") for j, val in enumerate(row)}
                            unique_key = (str(row_dict.get("župnija", "")), str(row_dict.get("knjiga", "")), str(row_dict.get("slika", "")), str(row_dict.get("zp. št.", "")))
                            if unique_key not in seen_keys[b_type] or unique_key == ("", "", "", ""):
                                seen_keys[b_type].add(unique_key)
                                data_by_type[b_type].append(row_dict)
            except Exception as e:
                self.root.after(0, lambda f=file_path, e=e: messagebox.showerror("Napaka", f"Napaka pri branju datoteke {os.path.basename(f)}:\n{e}"))
                return

        output_file = self.merge_output_path.get()
        try:
            wb_out = openpyxl.Workbook()
            if "Sheet" in wb_out.sheetnames: wb_out.remove(wb_out["Sheet"])
            
            all_rows_for_stats = []
            total = 0
            for b_type, cols in EXCEL_COLUMNS.items():
                if data_by_type[b_type]:
                    ws = wb_out.create_sheet(title=b_type)
                    ws.append(cols)
                    for row in data_by_type[b_type]:
                        ws.append([row.get(col, "") for col in cols])
                        all_rows_for_stats.append(row)
                        total += 1
                        
            self.update_surname_statistics(all_rows_for_stats, wb_out)
            
            wb_out.save(output_file)
            self.root.after(0, lambda: messagebox.showinfo("Uspeh", f"Uspešno združenih {total} zapisov (izločeni dvojniki)!\nShranjeno v:\n{output_file}"))
        except Exception as e: 
            self.root.after(0, lambda e=e: messagebox.showerror("Napaka", f"Napaka shranjevanja: {e}"))
