"""ArchiveMixin: funkcionalni sklop Arhivskega pomočnika."""
from ..common import *
from ..constants import *
from ..helpers import *

class ArchiveMixin:
    def build_archive_tab(self):
        top_frame = tk.Frame(self.tab_archive)
        top_frame.pack(padx=10, pady=10, fill="x")

        tk.Label(top_frame, text="Korenska mapa:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.arc_ent_dir = tk.Entry(top_frame, font=("Arial", 10))
        self.arc_ent_dir.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.arc_ent_dir.insert(0, r"D:\Matricula")

        tk.Button(top_frame, text="Brskaj...", command=lambda: self.browse_directory(self.arc_ent_dir)).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="🔄 Osveži kazalo", bg="#2196F3", fg="white", font=("Arial", 9, "bold"), command=self.refresh_archive).pack(side=tk.LEFT, padx=5)

        columns = ("parish", "book", "images", "txts", "status")
        self.tree = ttk.Treeview(self.tab_archive, columns=columns, show="headings", height=20)
        self.tree.heading("parish", text="Župnija")
        self.tree.heading("book", text="Knjiga (Signatura in Leta)")
        self.tree.heading("images", text="Slika (.jpg)")
        self.tree.heading("txts", text="Prepisi (.txt)")
        self.tree.heading("status", text="Status")
        self.tree.column("parish", width=150)
        self.tree.column("book", width=250)
        self.tree.column("images", width=80, anchor="center")
        self.tree.column("txts", width=80, anchor="center")
        self.tree.column("status", width=150, anchor="center")
        
        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(padx=10, pady=5, fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh_archive(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        base_dir = self.arc_ent_dir.get().strip()
        if not os.path.exists(base_dir): return

        try:
            for parish in sorted(os.listdir(base_dir)):
                parish_path = os.path.join(base_dir, parish)
                if os.path.isdir(parish_path):
                    for cat in sorted(os.listdir(parish_path)):
                        cat_path = os.path.join(parish_path, cat)
                        if os.path.isdir(cat_path):
                            for book in sorted(os.listdir(cat_path)):
                                book_path = os.path.join(cat_path, book)
                                if os.path.isdir(book_path):
                                    files = set(os.listdir(book_path))
                                    jpgs = len([n for n in files if n.lower().endswith(".jpg")])
                                    txts = sum(1 for n in files if n.lower().endswith(".jpg") and os.path.splitext(n)[0]+".txt" in files)
                                    status = "Popolnoma prepisano ✅" if os.path.exists(os.path.join(book_path, "_DONE")) else f"Delno ({txts}/{jpgs})"
                                    self.tree.insert("", "end", values=(parish, f"[{cat}] {book}", jpgs, txts, status))
        except Exception as e: messagebox.showerror("Napaka", f"Napaka pri pregledu diska:\n{e}")
