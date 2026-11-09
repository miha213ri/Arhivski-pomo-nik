"""CoreMixin: funkcionalni sklop Arhivskega pomočnika."""
from ..common import *
from ..constants import *
from ..helpers import *
from ..api_usage import ApiLedgerManager
from ..version import VERSION, VERSION_DATE


class CoreMixin:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Arhivski pomočnik – v{VERSION}")
        self.root.geometry("1100x850")
        self.root.minsize(950, 750)

        self.dl_cancel_event = threading.Event()
        self.ai_cancel_event = threading.Event()
        self.dl_lock = threading.Lock()

        self.api_ledger = ApiLedgerManager(LEDGER_FILE)

        self.app_dir = APP_DIR
        self.excel_dir = os.path.join(self.app_dir, "EXCEL DATOTEKE")
        self.baze_dir = os.path.join(self.app_dir, "BAZE")

        os.makedirs(self.excel_dir, exist_ok=True)
        os.makedirs(self.baze_dir, exist_ok=True)

        self.root_folder_path = tk.StringVar()
        self.excel_output_path = tk.StringVar(
            value=os.path.join(self.excel_dir, "maticne_knjige.xlsx")
        )
        self.db_path = tk.StringVar(
            value=os.path.join(self.baze_dir, "maticne_knjige.db")
        )
        self.base_filename = "maticne_knjige"

        loaded_settings = load_settings()
        self.live_db_config = loaded_settings.get("LiveDB", {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "maticne_knjige_db",
            "port": 3306
        })

        self.merge_files_list = []
        self.merge_output_path = tk.StringVar(
            value=os.path.join(self.excel_dir, "zdruzene_maticne_knjige.xlsx")
        )

        self.create_widgets()
        self.check_api_settings_quietly()

    def check_api_settings_quietly(self):
        settings = load_settings()
        prov = settings.get("active_provider", "Gemini")
        if not settings.get(prov, {}).get("api_key", ""):
            self.ai_log(f"[!] Opozorilo: API ključ za {prov} ni nastavljen.")

    def browse_directory(self, entry_widget):
        dir_path = filedialog.askdirectory()
        if dir_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, dir_path)

    def create_widgets(self):
        # GLAVA PROGRAMA
        header = tk.Frame(self.root, bg="#26384A", height=42)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="ARHIVSKI POMOČNIK",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#26384A"
        ).pack(side="left", padx=15)

        tk.Label(
            header,
            text=f"Različica {VERSION}  |  {VERSION_DATE}",
            font=("Arial", 9),
            fg="#DCE6F0",
            bg="#26384A"
        ).pack(side="right", padx=15)

        # GLAVNI ZAVIHKI
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.tab_dl = ttk.Frame(self.notebook)
        self.tab_ai = ttk.Frame(self.notebook)
        self.tab_archive = ttk.Frame(self.notebook)
        self.tab_uvoz = ttk.Frame(self.notebook)
        self.tab_zdruzevanje = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dl, text=" ⬇ PRENOS SLIK ")
        self.notebook.add(self.tab_ai, text=" 🧠 AI TRANSKRIPCIJA ")
        self.notebook.add(self.tab_archive, text=" 📁 LOKALNI ARHIV ")
        self.notebook.add(self.tab_uvoz, text=" 🛠️ UVOZ V EXCEL/SQL ")
        self.notebook.add(self.tab_zdruzevanje, text=" 🔗 ZDRUŽEVANJE ")

        self.build_download_tab()
        self.build_ai_tab()
        self.build_archive_tab()
        self.build_uvoz_tab()
        self.build_zdruzevanje_tab()