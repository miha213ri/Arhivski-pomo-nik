"""Pomožne funkcije za varnost, nastavitve, datoteke in spletni prenos."""
from .common import *
from .constants import *

def log_startup_error(exc_type, exc_value, exc_tb):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(error_msg)
    except: pass
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Kritična napaka ob zagonu", f"Program se ni mogel zagnati:\n\n{error_msg}")
        root.destroy()
    except: pass

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

def secure_encrypt(data: str) -> str:
    if not data: return ""
    try:
        crypt32 = ctypes.windll.crypt32
        b_data = data.encode('utf-8')
        blob_in = DATA_BLOB(len(b_data), ctypes.cast(b_data, ctypes.POINTER(ctypes.c_byte)))
        blob_out = DATA_BLOB()
        if crypt32.CryptProtectData(ctypes.byref(blob_in), None, None, None, None, 0x01, ctypes.byref(blob_out)):
            encrypted = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            crypt32.LocalFree(blob_out.pbData)
            return "DPAPI:" + base64.b64encode(encrypted).decode('utf-8')
    except Exception: pass
    return "B64:" + base64.b64encode(data.encode('utf-8')).decode('utf-8')

def secure_decrypt(data: str) -> str:
    if not data: return ""
    if data.startswith("DPAPI:"):
        try:
            crypt32 = ctypes.windll.crypt32
            b_data = base64.b64decode(data[6:])
            blob_in = DATA_BLOB(len(b_data), ctypes.cast(b_data, ctypes.POINTER(ctypes.c_byte)))
            blob_out = DATA_BLOB()
            if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
                decrypted = ctypes.string_at(blob_out.pbData, blob_out.cbData).decode('utf-8')
                crypt32.LocalFree(blob_out.pbData)
                return decrypted
        except Exception: pass
    elif data.startswith("B64:"):
        try:
            return base64.b64decode(data[4:]).decode('utf-8')
        except: pass
    return data 

def sanitize_name(name):
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).strip().replace(" ", "-") or "Neznano"

def decode_urlsafe_base64(data: str) -> str:
    data = data.replace("-", "+").replace("_", "/")
    data += "=" * ((4 - len(data) % 4) % 4)
    return base64.b64decode(data).decode("utf-8")

def is_valid_jpeg(path):
    try:
        if not os.path.exists(path) or os.path.getsize(path) < 100: return False
        with open(path, "rb") as f: 
            start = f.read(3)
            if start != b"\xff\xd8\xff": return False
            f.seek(-2, os.SEEK_END)
            end = f.read(2)
            return end == b"\xff\xd9"
    except OSError: return False

def safe_remove(path):
    try:
        if os.path.exists(path): os.remove(path)
    except OSError: pass

def write_text_atomic(path, content):
    temp_path = path + ".part"
    try:
        with open(temp_path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
        return True
    except Exception:
        safe_remove(temp_path)
        raise

def normalize_download_settings(settings):
    result = dict(DL_PRESETS["POČASI"])
    if isinstance(settings, dict):
        result.update({k: v for k, v in settings.items() if k in result})
        result["profile"] = settings.get("profile", "POČASI")
    try:
        for k in ["min_delay", "max_delay", "pause_duration"]: result[k] = max(0.0, float(result[k]))
        result["max_delay"] = max(result["min_delay"], result["max_delay"])
        for k in ["pause_every", "timeout", "retries", "max_session", "concurrent"]: result[k] = max(0, int(result[k]))
        result["concurrent"] = min(4, max(1, result["concurrent"]))
    except (TypeError, ValueError):
        result = dict(DL_PRESETS["POČASI"])
        result["profile"] = "POČASI"
    return result

def expand_parish_url(base_url):
    req = urllib.request.Request(base_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(f"Napaka pri povezavi (Zbiranje župnije): {e}")

    parsed_base = urllib.parse.urlsplit(base_url)
    base_path = parsed_base.path
    if not base_path.endswith("/"): base_path += "/"

    pattern = r'href="(' + re.escape(base_path) + r'[^"/]+/?)"'
    links = set(re.findall(pattern, html))
    
    final_urls = []
    for link in links:
        full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{link}"
        if full_url not in final_urls and full_url != base_url:
            final_urls.append(full_url)
    
    return final_urls

def get_book_metadata_and_urls(base_detail_url):
    parsed = urllib.parse.urlsplit(base_detail_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not (host == "matricula-online.eu" or host.endswith(".matricula-online.eu")):
        raise RuntimeError("URL ni veljaven naslov portala Matricula Online.")

    req = urllib.request.Request(base_detail_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404: raise RuntimeError("Napaka 404: Knjiga ne obstaja.")
        if e.code == 403: raise RuntimeError("Napaka 403: Dostop zavrnjen.")
        raise RuntimeError(f"HTTP napaka: {e.code}")
    except Exception as e:
        raise RuntimeError(f"Napaka pri povezavi: {e}")

    entries = re.findall(r"/image/([A-Za-z0-9_\-]+)", html)
    if not entries: 
        raise ValueError("PARISH_PAGE")

    decoded_urls = []
    for entry in entries:
        try:
            decoded = decode_urlsafe_base64(entry)
            decoded_parts = urllib.parse.urlsplit(decoded)
            if decoded_parts.scheme in ("http", "https") and decoded_parts.netloc:
                decoded_urls.append(decoded)
        except Exception: continue

    unique_image_urls = list(dict.fromkeys(decoded_urls))
    if not unique_image_urls: raise RuntimeError("URL-jev slik ni bilo mogoče razbrati.")

    path_parts = [part for part in parsed.path.rstrip("/").split("/") if part]
    if len(path_parts) >= 2: parish_raw, book_id = path_parts[-2], path_parts[-1]
    else: parish_raw, book_id = "Neznana-Cerkev", "Knjiga"

    parish_name = sanitize_name(parish_raw)
    
    # Odstranjevanje vodilnih ničel
    book_signature = sanitize_name(book_id)
    book_signature = book_signature.lstrip('0') or "0"

    years = None
    if unique_image_urls:
        first_url = unique_image_urls[0]
        unquoted_url = urllib.parse.unquote(first_url)
        filename_part = unquoted_url.split("/")[-1]
        
        # POPRAVEK REGEX-a: zdaj išče obliko "1833-1864" brez pogojevanja s presledki!
        img_range_match = re.search(r'(\d{4})\s*[-–—]\s*(\d{4})', filename_part)
        if img_range_match:
            years = f"{img_range_match.group(1)}-{img_range_match.group(2)}"
        else:
            img_single_match = re.findall(r'\b([12]\d{3})\b', filename_part)
            img_candidates = [c for c in img_single_match if c != book_id and not c.startswith('0')]
            if img_candidates:
                years = img_candidates[-1]
    
    if not years:
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title_text = title_match.group(1).strip()
            range_match = re.search(r'(\d{4})\s*[-–—]\s*(\d{4})', title_text)
            if range_match:
                years = f"{range_match.group(1)}-{range_match.group(2)}"
            else:
                candidates = re.findall(r'\b([12]\d{3})\b', title_text)
                candidates = [c for c in candidates if c != book_id and not c.startswith('0')]
                if candidates:
                    years = candidates[-1]
                    
    if not years:
        clean_html = re.sub(r'<[^>]+>', ' ', html)
        range_m = re.search(r'(\d{4})\s*[-–—]\s*(\d{4})', clean_html)
        if range_m:
            years = f"{range_m.group(1)}-{range_m.group(2)}"
        else:
            single_m = re.search(r"(" + re.escape(book_id) + r".{1,30}?)\b([12]\d{3})\b", clean_html)
            if single_m:
                years = single_m.group(2)

    html_lower = html.lower()
    types = []
    if re.search(r"(tauf|krst|bapt)", html_lower): types.append("KRSTNE")
    if re.search(r"(trauung|poro[cč]|copul|marri)", html_lower): types.append("POROCNE")
    if re.search(r"(sterb|mrl|mrtv|defunct|smrt|death)", html_lower): types.append("KNJIGE_MRTVIH")
    book_category = "_".join(types) if types else "OSTALE_KNJIGE"

    base_folder_name = f"{book_signature}_{years}" if years else book_signature
    book_folder = f"[{book_category}] {base_folder_name}"

    return parish_name, book_category, book_folder, unique_image_urls

def load_settings():
    default_settings = {
        "active_provider": "Gemini",
        "budget_limit_eur": 2.00,
        "Gemini": {"api_key": "", "model": "gemini-1.5-flash", "limits": dict(API_LIMIT_PRESETS["NORMALNO"]), "profile": "NORMALNO"},
        "OpenAI": {"api_key": "", "model": "gpt-4o-mini", "limits": dict(API_LIMIT_PRESETS["NORMALNO"]), "profile": "NORMALNO"},
        "Anthropic": {"api_key": "", "model": "claude-3-5-sonnet-20241022", "limits": dict(API_LIMIT_PRESETS["NORMALNO"]), "profile": "NORMALNO"},
        "CustomAPI": {"api_key": "", "model": "llama-3.2-90b-vision-preview", "base_url": "https://api.groq.com/openai/v1/chat/completions", "limits": dict(API_LIMIT_PRESETS["NORMALNO"]), "profile": "NORMALNO"},
        "DownloadSettings": dict(DL_PRESETS["POČASI"]),
        "LiveDB": {"host": "localhost", "user": "root", "password": "", "database": "maticne_knjige_db", "port": 3306}
    }
    default_settings["DownloadSettings"]["profile"] = "POČASI"
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.startswith("{"):
                    data = json.loads(content)
                    for k, v in data.items():
                        if k in default_settings and isinstance(v, dict):
                            default_settings[k].update(v)
                        else:
                            default_settings[k] = v
        except: pass
        
    for prov in ["Gemini", "OpenAI", "Anthropic", "CustomAPI"]:
        if "limits" not in default_settings[prov]:
            default_settings[prov]["limits"] = dict(API_LIMIT_PRESETS["NORMALNO"])
        if "profile" not in default_settings[prov]:
            default_settings[prov]["profile"] = "NORMALNO"
        if "api_key" in default_settings[prov]:
            default_settings[prov]["api_key"] = secure_decrypt(default_settings[prov]["api_key"])
            
    if "LiveDB" in default_settings and "password" in default_settings["LiveDB"]:
         default_settings["LiveDB"]["password"] = secure_decrypt(default_settings["LiveDB"]["password"])

    return default_settings

def save_settings(settings_dict):
    try:
        save_data = json.loads(json.dumps(settings_dict))
        for prov in ["Gemini", "OpenAI", "Anthropic", "CustomAPI"]:
            if prov in save_data and "api_key" in save_data[prov]:
                save_data[prov]["api_key"] = secure_encrypt(save_data[prov]["api_key"])
        if "LiveDB" in save_data and "password" in save_data["LiveDB"]:
            save_data["LiveDB"]["password"] = secure_encrypt(save_data["LiveDB"]["password"])
            
        json_str = json.dumps(save_data, indent=4)
        write_text_atomic(SETTINGS_FILE, json_str)
        return True
    except Exception as e:
        messagebox.showerror("Napaka", f"Nastavitev ni bilo mogoče shraniti:\n{e}")
        return False

def load_prompt():
    if os.path.exists(PROMPT_FILE):
        try:
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return content
        except: pass
    return DEFAULT_PROMPT

def save_prompt(prompt_text):
    try:
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            f.write(prompt_text)
        return True
    except Exception as e:
        messagebox.showerror("Napaka", f"Navodil ni bilo mogoče shraniti:\n{e}")
        return False

def is_valid_json_schema(text, required_keys):
    try:
        match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if not match: return False, "Ni najdenega JSON seznama."
        data = json.loads(match.group(0))
        if not isinstance(data, list) or len(data) == 0: return False, "JSON ne vsebuje seznama objektov."
        for idx, item in enumerate(data):
            if not isinstance(item, dict): return False, f"Zapis {idx} ni objekt."
            missing = [k for k in required_keys if k not in item]
            if missing: return False, f"Zapisu {idx} manjkajo polja: {', '.join(missing)}"
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"Sintaktična napaka v JSON: {str(e)}"

def parse_page_range(value, total_pages=None):
    text = str(value or '').strip()
    if not text:
        return []

    selected = set()
    for token in re.split(r'[;,]+', text):
        token = token.strip()
        if not token:
            continue
        match = re.fullmatch(r'(\d+)(?:\s*[-–]\s*(\d+))?', token)
        if not match:
            raise ValueError(f"Nepravilen obseg strani: '{token}'. Uporabi npr. 5, 10-13 ali 1-3, 7.")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start < 1 or end < 1:
            raise ValueError('Številke strani morajo biti večje od 0.')
        if end < start:
            raise ValueError(f'Nepravilen razpon strani: {token}. Začetna stran je večja od končne.')
        if total_pages is not None and (start > total_pages or end > total_pages):
            raise ValueError(f'Vpisana stran presega število strani v knjigi ({total_pages}).')
        selected.update(range(start, end + 1))

    return sorted(selected)

sys.excepthook = log_startup_error