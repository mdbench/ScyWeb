import os
import sys
import subprocess

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
        'beautifulsoup4': 'bs4'
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

import re
import time
import random
import io
import torch
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

    def update_index(self, keywords, ppm_path, key_id):
        idx_count = self.index_buffer[1]
        if idx_count < self.max_keys:
            new_idx = idx_count + 2 
            self.index_buffer[new_idx] = {
                "tags": keywords,
                "path": ppm_path,
                "key": key_id
            }
            self.index_buffer[1] += 1

# --- THE GEMTALE AI ENGINE ---
class GemtaleAI:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        # Initialize ScyKernel for PPM and PNG operations
        self.kernel = ScyKernel(password=SECURE_PWD, file_path=f"{PPM_PATH_BASE}1.ppm")
        self.index = GemtaleIndex()
        
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
            snapshot_download(repo_id="google/gemma-2b-it", local_dir=MODEL_PATH)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH, torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            low_cpu_mem_usage=True).to(self.device)

    def process_and_put(self):
        crawler = EthicalCrawler()
        if not os.path.exists(URL_FILE): return
        
        with open(URL_FILE, "r") as f:
            seeds = [l.strip() for l in f if l.strip() and not l.startswith("#")]

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

        for url in list(set(queue))[:2000]:
            if not crawler.is_allowed(url): continue
            time.sleep(random.uniform(5, 15))
            try:
                raw = requests.get(url, headers=HEADERS, timeout=15).text
                text = re.sub('<[^<]+?>', '', raw)[:6000]
                prompt = f"""
                    [SYSTEM: ACADEMIC ARCHIVIST PERSONA]
                    Distill the following text into a technical summary. 
                    1. Use advanced nomenclature (e.g., decoherence, Hilbert space, non-linear mapping).
                    2. Focus on structural data points that can be indexed via keywords.
                    3. Maintain a College-Level ARI score (>12).
                    4. Do not use conversational filler.

                    TEXT TO PROCESS:
                    {text}
                """
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
                outputs = self.model.generate(**inputs, max_new_tokens=450)
                summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

                # Put to PPM (Physical Volume)
                ppm_vol_path = f"{PPM_PATH_BASE}{self.index.current_volume}.ppm"
                if not os.path.exists(ppm_vol_path):
                    self.kernel.create_ppm_db(ppm_vol_path)
                
                # Logic to update internal index and put into database
                key_id = f"KEY_{self.index.index_buffer[1] + 1}"
                self.kernel.put_to_ppm(key_id, summary, SECURE_PWD)
                
                # Put to PNG Index (RAM Buffer)
                keywords = self.index.extract_keywords(summary)
                self.index.update_index(keywords, ppm_vol_path, key_id)
                self.kernel.put_to_png(key_id, f"{' '.join(keywords)}|{summary}", SECURE_PWD)
                
                # Update Key 1 Counter
                new_count = self.index.index_buffer[1]
                self.kernel.put_to_png("INDEX_COUNT", str(new_count), SECURE_PWD)
                
                print(f"[+] Data put successfully: {url}")
            except Exception as e: print(f"[!] Error: {e}")

        # Final PNG sync to disk
        self.kernel.sync_png(PNG_DB_PATH, "commit")

    def ask(self, q):
        query_tags = self.index.extract_keywords(q)
        count = self.index.index_buffer[1]
        sample_size = min(300, count)
        
        # Stochastic retrieval from RAM (PNG Buffer)
        indices = random.sample(range(2, count + 2), sample_size) if count > 0 else []
        context_snippets = []
        for idx in indices:
            # We fetch from the hot PNG buffer for speed
            entry_data = self.kernel.get_from_png(f"KEY_{idx-1}", SECURE_PWD)
            if "|" in entry_data:
                tags, content = entry_data.split("|", 1)
                if any(t in tags for t in query_tags):
                    context_snippets.append(content)
        
        context = " ".join(context_snippets[:5])
        prompt = f"Context: {context}\n\nQuestion: {q}\nAnswer:"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=300)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).split("Answer:")[-1].strip()

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
            <input type="text" id="q" placeholder="Type quantum mechanics inquiry..." onkeypress="if(event.key==='Enter')send()">
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
    
    print("[+] Launching Quantum Messenger on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)