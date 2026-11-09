"""Evidenca porabe, hitrosti in omejitev klicev AI API."""
from .common import *
from .constants import *

class ApiLedgerManager:
    def __init__(self, ledger_path):
        self.ledger_path = ledger_path
        self.lock = threading.Lock()
        self.req_history = deque()
        self.monthly_cost = 0.0
        self.daily_requests = 0
        self.warned_80 = False
        self.current_month = datetime.now().strftime("%Y-%m")
        self.current_day = datetime.now().strftime("%Y-%m-%d")
        self._ensure_ledger_exists()
        self._calculate_current_usage()

    def _ensure_ledger_exists(self):
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Datum_Cas", "Ponudnik", "Model", "In_Tokens", "Out_Tokens", "Cena_EUR", "Status"])

    def _calculate_current_usage(self):
        with self.lock:
            now_month = datetime.now().strftime("%Y-%m")
            now_day = datetime.now().strftime("%Y-%m-%d")
            
            if self.current_day != now_day or self.current_month != now_month:
                self.current_day = now_day
                self.current_month = now_month
            
            self.monthly_cost = 0.0
            self.daily_requests = 0
            if not os.path.exists(self.ledger_path): return
            with open(self.ledger_path, "r", newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        date_str = row["Datum_Cas"]
                        if date_str.startswith(self.current_month):
                            self.monthly_cost += float(row["Cena_EUR"])
                        if date_str.startswith(self.current_day):
                            self.daily_requests += 1 # Štejejo vse zahteve za limit!
                    except Exception: pass

    def wait_for_capacity(self, rpm_limit, tpm_limit, rpd_limit, estimated_tokens, check_cancel_event, ui_update_callback):
        self._calculate_current_usage() # Obvezno osvežimo števce glede na trenutni čas
        while True:
            if check_cancel_event.is_set(): return False
            with self.lock:
                now = time.time()
                while self.req_history and self.req_history[0]['time'] < now - 60:
                    self.req_history.popleft()
                if self.daily_requests >= rpd_limit:
                    ui_update_callback(log=f"[!] DOSEŽEN DNEVNI LIMIT ZAHTEV (RPD: {rpd_limit}). Program se ustavlja.", api="Dnevni limit!")
                    return False
                current_rpm = len(self.req_history)
                current_tpm = sum(item['in'] + item['out'] for item in self.req_history)
                if current_rpm < rpm_limit and (current_tpm + estimated_tokens) <= tpm_limit:
                    return True
                if self.req_history:
                    oldest_time = self.req_history[0]['time']
                    wait_time = (oldest_time + 60.1) - now
                else:
                    wait_time = 1.0
            if wait_time > 0:
                ui_update_callback(api=f"API Omejitev: čakam {wait_time:.1f}s...")
                check_cancel_event.wait(wait_time)

    def record_usage(self, provider, model, in_tok, out_tok, cost, status):
        now = time.time()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            # Zabeležimo vsako zahtevo (uspešno ali ne) v RPM zgodovino, da preprečimo spam ob napakah
            self.req_history.append({'time': now, 'in': in_tok, 'out': out_tok})
            self.daily_requests += 1
            if status == "OK":
                self.monthly_cost += cost
            try:
                with open(self.ledger_path, "a", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([now_str, provider, model, in_tok, out_tok, f"{cost:.6f}", status])
            except: pass
