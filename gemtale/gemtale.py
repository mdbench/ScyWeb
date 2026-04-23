WELCOME_MSG = """
 _______  _______  __   __  _______  _______  ___      _______ 
|       ||       ||  |_|  ||       ||   _   ||   |    |       |
|    ___||    ___||       ||_     _||  |_|  ||   |    |    ___|
|   | __ |   |___ |       |  |   |  |       ||   |    |   |___ 
|   ||  ||    ___||       |  |   |  |       ||   |___ |    ___|
|   |_| ||   |___ | ||_|| |  |   |  |   _   ||       ||   |___ 
|_______||_______||_|   |_|  |___|  |__| |__||_______||_______|

"""

print(WELCOME_MSG)

WELCOME_EXPLANATION = """
Welcome to Gemtale. A data-based AI processing engine that runs using the ScySDK database,
leveraging images to store keyed data entries in a quantum safe methodology.
"""
print(WELCOME_EXPLANATION)

import os
import platform

def patch_git_path():
    current_os = platform.system()
    
    if current_os == "Windows": # Windows
        git_path = r"C:\Program Files\Git\cmd"
    elif current_os == "Darwin":  # macOS
        git_path = "/usr/local/bin" 
    else:  # Linux / Unix
        git_path = "/usr/bin"
        
    if os.path.exists(git_path) and git_path not in os.environ["PATH"]:
        os.environ["PATH"] = git_path + os.pathsep + os.environ["PATH"]

patch_git_path()

import os
import subprocess
import sys

# --- AUTO-DEPENDENCY INSTALLER ---
def install_dependencies():
    required = {
        'torch': 'torch',
        'transformers': 'transformers',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'huggingface_hub': 'huggingface_hub',
        'pillow': 'PIL',
        'numpy': 'numpy',
        'accelerate': 'accelerate',
        'bitsandbytes': 'bitsandbytes',
        'beautifulsoup4': 'bs4',
        'psutil': 'psutil',
        'matplotlib': 'matplotlib',
        'requests': 'requests'
    }
    
    for pkg, imp_name in required.items():
        try:
            __import__(imp_name)
        except ImportError:
            print(f"[*] Missing {pkg}. Installing...")
            # Added the mandatory flag for ChromeOS/Debian 12+
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                pkg, "--break-system-packages"
            ])

install_dependencies()

import getpass
from huggingface_hub import login

def ensure_hf_token():
    # Define your hardcoded path here in case you want persistence
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TOKEN_FILE_PATH = os.path.join(BASE_DIR, "hf_token.txt")
    token = None
    if os.path.exists(TOKEN_FILE_PATH):
        try:
            with open(TOKEN_FILE_PATH, "r") as f:
                token = f.read().strip()
            if token:
                print(f"[*] Found token in {TOKEN_FILE_PATH}")
        except Exception as e:
            print(f"[!] Could not read token file: {e}")
    if not token:
        token = os.environ.get("HF_TOKEN")
    if not token:
        print("[*] HF_TOKEN not found in file or environment.")
        token = input("Enter your Hugging Face Token: ").strip().replace('\r', '').replace('\n', '')
    if token:
        try:
            login(token=token, add_to_git_credential=False)
            print("[+] Authentication successful.")
            if not os.path.exists(TOKEN_FILE_PATH):
                open(TOKEN_FILE_PATH, "w", encoding="utf-8").write(token)
                print(f"[*] Created {TOKEN_FILE_PATH}.")
        except Exception as e:
            print(f"[!] Login failed: {type(e).__name__}: {e}")
            exit(1)
    else:
        print("[!] No token provided. Authentication aborted.")
        exit(1)

ensure_hf_token()

import re
import time
import random
import io
import glob
import torch
import threading
import logging
import base64
import matplotlib.pyplot as plt
import requests
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModelForCausalLM
from PIL import Image
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

# --- SDK PATHING ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SDK_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "sdk", "python"))
sys.path.append(SDK_PATH)
try:
    from ScyKernel import ScyKernel
except ImportError:
    print(f"[!] Critical Error: ScyKernel.py not found at {SDK_PATH}")
    sys.exit(1)

# --- CONFIGURATION ---
GEMTALE_DATA = os.path.join(CURRENT_DIR, "gemtale_data")
MODEL_PATH = os.path.join(GEMTALE_DATA, "models/gemma_core")
URL_FILE = os.path.join(CURRENT_DIR, "URLS.txt")
CIPHER_TABLE = os.path.join(CURRENT_DIR, "CIPHER_TABLE.txt")
PPM_PATH_BASE = os.path.join(GEMTALE_DATA, "quantum_db_vol")
PNG_DB_PATH = os.path.join(GEMTALE_DATA, "quantum_index_vol1.png")
os.makedirs(GEMTALE_DATA, exist_ok=True)

USER_AGENT = 'GemtaleBot/2.0 (Matthew D. Benchimol)'
HEADERS = {'User-Agent': USER_AGENT}
SECURE_PWD = "QUANTUM_SECURE_SALT_2026"

# --- THE ETHICAL CRAWLER ---
class EthicalCrawler:
    def __init__(self):
        self.parsers = {}

    def is_allowed(self, url):
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}/robots.txt"
        if base not in self.parsers:
            rp = RobotFileParser()
            rp.set_url(base)
            try: rp.read()
            except: return True
            self.parsers[base] = rp
        return self.parsers[base].can_fetch(USER_AGENT, url)

# --- THE INDEXING & VOLUME ENGINE ---
class GemtaleIndex:
    def __init__(self):
        self.current_volume = 1
        self.index_buffer = {1: 0} # Key 1: Total Index Count
        self.max_keys = 10000
        self.png_memory_buffer = None 

    def extract_keywords(self, text):
        words = re.findall(r'\b\w{6,}\b', text.lower())
        return list(set(words))[:10]

    def update_index(self):
        if self.index_buffer[1] < self.max_keys:
            self.index_buffer[1] += 1

    def check_for_data(self, kernel_instance, key_id):
        data = kernel_instance.get_from_png(key_id, SECURE_PWD)
        if not data or len(data) == 0:
            return False
        prefix = b'PROM' if isinstance(data, bytes) else 'PROM'
        if len(data) < 4 or not data.startswith(prefix):
            print(f"[!] Slot {key_id} contains corrupt data, treating as free.")
            return False 
        return True

    def get_next_free_slot(self, kernel_instance, cipher_tag):
        print(f"Cipher tag is: {cipher_tag}.")
        key_id = f"KEY_{cipher_tag}"
        if not self.check_for_data(kernel_instance, key_id):
            return key_id
        return "Collision"

    def check_and_rotate_volume(self, file_path, kernel_instance):
        data = kernel_instance.get_from_ppm("10000", SECURE_PWD)
        # 45MB in bytes (45 * 1024 * 1024)
        THRESHOLD_BYTES = 45 * 1024 * 1024
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            if size_bytes > THRESHOLD_BYTES and data and len(data) > 0:
                print(f"[!] Volume limit reached ({size_bytes / (1024*1024):.2f} MB). Rotating...")
                self.current_volume += 1
                return True
        return False

# --- THE GEMTALE AI ENGINE ---
class GemtaleAI:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        # Initialize ScyKernel for PPM and PNG operations
        self.kernel = ScyKernel(password=SECURE_PWD, file_path=f"{PPM_PATH_BASE}1.ppm")
        self.index = GemtaleIndex()
        self.cipher_table = self.load_cipher_table()
        # Variables to help track status & time/duration
        self.success_count = 0     # Total successes
        self.total_gen_time = 0.0  # Sum of all summary durations
        self.summary_count = 0     # Total summaries completed
        
        # Load Existing PNG Index into RAM if it exists
        if os.path.exists(PNG_DB_PATH):
            self.kernel.sync_png(PNG_DB_PATH, "load")
            count_val = self.kernel.get_from_png("INDEX_COUNT", SECURE_PWD)
            self.index.index_buffer[1] = int(count_val) if count_val.isdigit() else 0
        else:
            self.kernel.create_png_db(PNG_DB_PATH)
            self.kernel.put_to_png("INDEX_COUNT", "0", SECURE_PWD)

        self.setup_model()

    def setup_model(self):
        if not os.path.exists(MODEL_PATH) or not os.listdir(MODEL_PATH):
            snapshot_download(repo_id="google/gemma-3-270m-it", local_dir=MODEL_PATH)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH, torch_dtype=torch.bfloat16 if self.device != "cpu" else torch.float32,
            low_cpu_mem_usage=True).to(self.device)

    def process_and_put(self):
        crawler = EthicalCrawler()
        if not os.path.exists(URL_FILE): return
        if not os.path.exists(CIPHER_TABLE): return

        # Wipe old files for new DB update
        data_dir = os.path.join(os.getcwd(), "gemtale_data")
        patterns = [
            os.path.join(data_dir, "quantum_index_vol*.png"),
            os.path.join(data_dir, "quantum_db_vol*.ppm")
        ]
        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    print(f"[*] Removed old database at: {file_path}.")
                except OSError as e:
                    print(f"[!] Error deleting {file_path}: {e.strerror}")

        #Wipe old logs for new tracking
        with open("gemtale_log.txt", "w", encoding="utf-8") as f:
            pass 
        
        with open(URL_FILE, "r") as f:
            seeds = [l.strip() for l in f if l.strip() and not l.startswith("#")]

        print(f"[*] Seeding for crawler.")
        queue = []
        for s in seeds:
            if crawler.is_allowed(s):
                try:
                    res = requests.get(s, headers=HEADERS, timeout=10)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        full = urljoin(s, a['href'])
                        if any(p in full for p in ['/abs/', '/articles/', '/blog/']):
                            queue.append(full)
                except: pass

        print(f"[*] Beginning loop through URLs.")
        for url in list(set(queue))[:2000]:
            if not crawler.is_allowed(url): continue
            time.sleep(random.uniform(5, 15))
            try:
                start_time = time.perf_counter()
                response = requests.get(url, headers=HEADERS, timeout=15)
                if not response.content or response.status_code != 200:
                    print(f"[!] Skipping {url}: Status code {response.status_code}.")
                    continue
                raw = response.content
                text = self.extract_clean_text(url, raw)
                if not text or len(text.strip()) == 0:
                    print(f"[!] Skipping {url}: Extracted text is empty.")
                    continue
                #print(f"[TEXT] {text}")
                prompt = f"""
                    Here is an research paper abstract: {text}
                    Here is why this matters:
                """
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
                outputs = self.model.generate(**inputs, max_new_tokens=450)
                ai_summary = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
                keywords = self.index.extract_keywords(ai_summary)
                summary = ai_summary.replace("<bos>", "").replace("<eos>", "").strip()
                summary = summary.encode('utf-8').hex().replace('0', 'g')
                summary = f"<sof>{summary}<eof>"

                # Duration and time tracking by summary
                duration = time.perf_counter() - start_time
                self.total_gen_time += duration
                self.summary_count += 1
                avg_time = self.total_gen_time / self.summary_count
                remaining_urls = len(queue) - self.index.index_buffer[1]
                eta_seconds = remaining_urls * avg_time

                # Put to PPM (Physical Volume)
                self.index.check_and_rotate_volume(f"{PPM_PATH_BASE}{self.index.current_volume}.ppm", self.kernel)
                ppm_vol_path = f"{PPM_PATH_BASE}{self.index.current_volume}.ppm"
                if not os.path.exists(ppm_vol_path):
                    self.kernel.create_ppm_db(ppm_vol_path)
                
                # Logic to update internal index and put into database
                #key_id = f"KEY_{self.index.index_buffer[1] + 1}"
                # Prevent collision check with cipher_table
                current_index = self.index.index_buffer[1]
                key_id = self.index.get_next_free_slot(self.kernel, self.cipher_table[self.index.index_buffer[1]])
                while key_id == "Collision":
                    current_index += 1
                    key_id = self.index.get_next_free_slot(self.kernel, self.cipher_table[current_index])
                self.index.index_buffer[1] = current_index
                self.kernel.put_to_ppm(key_id, summary, SECURE_PWD)

                # Create hex code reference
                hx_referencer = f"{self.index.index_buffer[1]}:{self.cipher_table[self.index.index_buffer[1]]}\n\n".encode('utf-8').hex().replace('0', 'g')

                # Set summary to gemtale log
                summary_check = summary.replace("<sof>", "").split("<eof>")[0].strip()
                self.add_gemtale_log(f"<[$]STRING ENTRY>{hx_referencer}{summary_check}</END OF STRING ENTRY>")
                
                # Put to PNG Index (RAM Buffer)
                self.index.update_index()
                indexer_keywords = f"{' '.join(keywords)}|quantum_db_vol{self.index.current_volume}.ppm".encode('utf-8').hex().replace('0', 'g')
                self.kernel.put_to_png(key_id, indexer_keywords, SECURE_PWD)

                # Check/confirm PNG & PPM
                png_data = self.kernel.get_from_png(key_id, SECURE_PWD)
                png_data = png_data.replace("<sof>", "").split("<eof>")[0].strip()
                self.add_gemtale_log(f"<[$]STRING ENTRY>{hx_referencer}{png_data}</END OF STRING ENTRY>")
                ppm_data = self.kernel.get_from_ppm(key_id, SECURE_PWD)
                ppm_data = ppm_data.replace("<sof>", "").split("<eof>")[0].strip()
                self.add_gemtale_log(f"<[$]STRING ENTRY>{hx_referencer}{ppm_data}</END OF STRING ENTRY>")
                if ppm_data == summary_check:
                    print(f"[+] Data entry is synchronized between databases.")
                else: 
                    print(f"[!] Data entry is not synchronized properly.")
                
                # Update Key 1 Counter
                new_count = self.index.index_buffer[1]
                self.kernel.put_to_png("INDEX_COUNT", str(new_count), SECURE_PWD)
                print(f"[*] Index is currently {new_count} ({self.success_count}).")

                # Status tracking by success
                self.success_count += 1
                total_urls = len(queue)
                current_url_count = self.success_count
                percentage = (current_url_count / total_urls) * 100

                # Status/log messages
                message1 = f"[+] ({current_url_count}/{total_urls} | {percentage:.1f}%) Data put successfully: {url}"
                print(message1)
                message2 = f"[+] Summarized in {duration:.2f}s | Avg: {avg_time:.2f}s | ETA: {int(eta_seconds/60)}m left"
                print(message2)

            except Exception as e:
                print(f"[!] Error: {type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

        # Final PNG sync to disk
        self.kernel.sync_png(PNG_DB_PATH, "commit")

    def ask(self, q):
        query_tags = self.index.extract_keywords(q)
        count = self.index.index_buffer[1]
        print(f"[*] Starting Gemtale process with total of {count} indexes.")
        sample_size = min(count, count)
        print(f"[*] Sample size is: {sample_size}.")

        #Wipe old logs for new tracking
        with open("gemtale_messenger_log.txt", "w", encoding="utf-8") as f:
            pass 

        #Error counts
        png_errors = 0
        ppm_errors = 0
        
        # Stochastic retrieval from RAM (PNG Buffer)
        indices = random.sample(range(2, count + 2), sample_size) if count > 0 else []
        context_snippets = ""
        for idx in indices:
            print(f"[*] Processing index: {idx}.")
            self.add_gemtale_messenger_log(f"[START OF ENTRY {idx}]\n\n")
            # We fetch from the hot PNG buffer for speed
            png_data = self.kernel.get_from_png(f"KEY_{self.cipher_table[idx-1]}", SECURE_PWD)
            png_data_sanitized = png_data.replace('g', '0').strip()
            if not all(c in "0123456789abcdef|" for c in png_data_sanitized.lower()):
                self.add_gemtale_messenger_log(f"[!] [ABNORMAL] {png_data}\n")
                print(f"[!] PNG Data corrupted at index of {idx}.")
                png_errors += 1
                continue
            else:
                self.add_gemtale_messenger_log(f"[+] [NORMAL] {png_data}\n")
            png_data_actual = bytes.fromhex(png_data_sanitized).decode('utf-8')
            keywords = png_data_actual.split('|')[0]
            print(f"[*] Keywords for entry: {keywords}.")
            # Normally, ppm_path parameter passed to rotating ppm vol
            ppm_data = self.kernel.get_from_ppm(f"KEY_{self.cipher_table[idx-1]}", SECURE_PWD)
            ppm_data_actual = ppm_data.replace("<sof>", "").split("<eof>")[0].strip()
            ppm_data_sanitized = ppm_data_actual.replace('g', '0').strip()
            if not all(c in "0123456789abcdef|" for c in ppm_data_sanitized.lower()):
                self.add_gemtale_messenger_log(f"[!] [ABNORMAL] {ppm_data}\n")
                print(f"[!] PPM Data corrupted at index of {idx}.")
                ppm_errors += 1
                continue
            else:
                self.add_gemtale_messenger_log(f"[+] [NORMAL] {ppm_data}\n")
            sanitized_ppm_data = bytes.fromhex(ppm_data_sanitized).decode('utf-8')
            print(f"[{idx-1}:{self.cipher_table[idx-1]}] Context is: {sanitized_ppm_data[:50]}...")
            tags = keywords.split(' ')
            q_tags = set(query_tags)
            p_tags = set(tags)
            matches = q_tags.intersection(p_tags)
            match_rate = len(matches) / len(q_tags) if q_tags else 0
            if match_rate >= 0.1:
                context_snippets = sanitized_ppm_data.split("Here is why this matters:")[0].strip()
                self.add_gemtale_messenger_log(f"[MATCH > 10%] [{sanitized_ppm_data}]\n\n")
            self.add_gemtale_messenger_log(f"[END OF ENTRY {idx}]\n\n")
        
        context = context_snippets.strip()
        if len(context) > 120000:
            context = context[:120000]
        prompt = f"Identify mutual or joint future research based on the stated research interest and the following research abstract: {context}\n\nResearch Interest: {q}\nFuture Research:"
        self.add_gemtale_messenger_log(f"Prompt is: \n\n{prompt}\n")
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=300)
        answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True).split("Future Research:")[-1].strip()
        self.add_gemtale_messenger_log(f"Answer is: \n\n{answer}\n")
        png_error_rate = (png_errors/count)*100
        ppm_error_rate = (ppm_errors/count)*100
        self.add_gemtale_messenger_log(f"[PNG ERRORS: {png_errors}/{count} or {png_error_rate}%] [PPM Errors: {ppm_errors} or {ppm_error_rate}%]")
        self.add_gemtale_messenger_log(f"[END OF GEMTALE INQUIRY]")
        return answer

    def extract_clean_text(self, url, raw_html):
        soup = BeautifulSoup(raw_html, 'html.parser')
        if "arxiv.org" in url:
            meta = soup.find("meta", attrs={"name": "citation_abstract"})
            if meta and meta.get("content"):
                return meta["content"]
                
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        return text[:6000]

    def load_cipher_table(self):
        try:
            with open(CIPHER_TABLE, "r") as f:
                cipher_table = [line.strip() for line in f if line.strip()]
                if len(cipher_table) < 10000:
                    print(f"[!] Warning: Cipher table only contains {len(cipher_table)} entries.")
                    sys.exit(0)
                return cipher_table
        except FileNotFoundError:
            print(f"[!] Error: {file_path} not found. Ensure the file is in the root directory.")
            return []

    def add_gemtale_log(self, log_entry):
        log_file = "gemtale_log.txt"
        if not os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as f:
                pass
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def add_gemtale_messenger_log(self, log_entry):
        log_file = "gemtale_messenger_log.txt"
        if not os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as f:
                pass
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{log_entry}\n\n")

# --- FASTAPI & UI ---
app = FastAPI()
node = None

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>Gemtale Messenger</title>
    <style>
        body { background: #0b0b0e; color: #d1d1d1; font-family: sans-serif; height: 100vh; margin: 0; display: flex; align-items: center; justify-content: center; }
        #chat-box { width: 550px; height: 750px; background: #14141a; border-radius: 20px; border: 1px solid #2a2a35; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
        #log { flex: 1; overflow-y: auto; padding: 25px; display: flex; flex-direction: column; gap: 20px; }
        .bubble { max-width: 85%; padding: 15px; border-radius: 18px; font-size: 15px; line-height: 1.5; }
        .user { align-self: flex-end; background: #2563eb; color: white; border-bottom-right-radius: 4px; }
        .ai { align-self: flex-start; background: #1f2937; color: #34d399; border-bottom-left-radius: 4px; border: 1px solid #374151; }
        #input-bar { padding: 25px; background: #1c1c24; display: flex; gap: 15px; border-top: 1px solid #2a2a35; }
        input { flex: 1; background: #0b0b0e; border: 1px solid #374151; color: white; padding: 12px; border-radius: 10px; outline: none; }
        button { background: #34d399; color: #064e3b; border: none; padding: 12px 20px; border-radius: 10px; font-weight: 700; cursor: pointer; }
    </style>
</head>
<body>
    <div id="chat-box">
        <div id="log"><div class="bubble ai">Gemtale connection active.</div></div>
        <div id="input-bar">
            <input type="text" id="q" placeholder="Type research interest..." onkeypress="if(event.key==='Enter')send()">
            <button onclick="send()">SEND</button>
        </div>
    </div>
    <script>
        async function send(){
            const i=document.getElementById('q'), l=document.getElementById('log');
            if(!i.value) return;
            const q=i.value; l.innerHTML+=`<div class="bubble user">${q}</div>`;
            i.value=''; l.scrollTop=l.scrollHeight;
            const res=await fetch(`/api?q=${encodeURIComponent(q)}`);
            const d=await res.json();
            l.innerHTML+=`<div class="bubble ai">${d.answer}</div>`;
            l.scrollTop=l.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home(): return HTML_UI

@app.get("/api")
async def api(q: str): return {"answer": node.ask(q)}

if __name__ == "__main__":
    print("\n--- GEMTALE LAUNCHER ---")
    print("[1] UPDATE: Create/Update Database (Process & Put)")
    print("[2] SERVER: Launch Messenger Only (Get)")
    mode = input("\nSelect Mode (1/2): ")

    node = GemtaleAI()
    if mode == "1":
        node.process_and_put()
    
    print("[+] Launching Gemtale Messenger on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)