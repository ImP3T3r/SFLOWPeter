import threading
import os
import json
from flask import Flask, jsonify, render_template_string, send_from_directory, request
from db.database import TranscriptionDB
from config import DB_PATH

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.json")
GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-2.0-pro",
]

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Howl - Transcripciones</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        body { font-family: 'Inter', system-ui, sans-serif; background: #0a0a0a; color: #e5e5e5; }
        .glass { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); }
        .row-hover:hover { background: rgba(255,255,255,0.05); }
        .text-preview { max-height: 2.6em; overflow: hidden; transition: max-height 0.3s ease; }
        .text-preview.expanded { max-height: 500px; }
        .copied { animation: flash 0.5s ease; }
        @keyframes flash { 0%,100% { background: transparent; } 50% { background: rgba(255,255,255,0.1); } }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
        .model-card { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.06); }
        .model-card:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.12); }
        .model-card.active { background: rgba(251,146,60,0.08); border-color: rgba(251,146,60,0.4); }
        .model-card.active .model-name { color: rgb(251,146,60); }
    </style>
</head>
<body class="min-h-screen p-6">
    <div class="max-w-4xl mx-auto">
        <!-- Header -->
        <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-3">
                <div class="text-2xl font-semibold flex items-center gap-2">
                    <img src="/logo_small.png" alt="Howl Logo" class="w-8 h-8 rounded-full bg-white/10 p-1">
                    <span>Howl</span>
                </div>
                <span class="text-xs text-white/30 bg-white/5 px-2 py-1 rounded-full" id="count-badge">-</span>
                <span class="text-xs text-white/25 bg-white/5 px-2 py-1 rounded-full" id="tokens-badge">- tokens</span>
            </div>
            <div class="flex items-center gap-3">
                <input type="text" id="search" placeholder="Buscar..."
                    class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white/80
                    placeholder-white/30 focus:outline-none focus:border-white/20 w-48">
                <button onclick="loadData()" class="text-white/40 hover:text-white/70 text-sm">Actualizar</button>
            </div>
        </div>

        <!-- Model Selector -->
        <div class="glass rounded-xl px-4 py-4 mb-4">
            <div class="flex items-center justify-between mb-3">
                <span class="text-white/40 text-xs uppercase tracking-wider">Modelo Gemini para refinar</span>
                <span id="model-status" class="text-orange-400/70 text-xs transition-all duration-300"></span>
            </div>
            <div class="grid grid-cols-2 gap-2" id="model-cards">
                <div class="model-card rounded-lg px-3 py-2.5 cursor-pointer border transition-all duration-150"
                    data-model="gemini-1.5-flash" onclick="selectModel(this)">
                    <div class="flex items-center justify-between">
                        <div class="text-sm font-medium model-name">gemini-1.5-flash</div>
                        <div class="text-xs text-white/20 font-mono">$0.075/M</div>
                    </div>
                    <div class="text-xs text-white/30 mt-0.5">Rápido &middot; más económico</div>
                </div>
                <div class="model-card rounded-lg px-3 py-2.5 cursor-pointer border transition-all duration-150"
                    data-model="gemini-2.0-flash" onclick="selectModel(this)">
                    <div class="flex items-center justify-between">
                        <div class="text-sm font-medium model-name">gemini-2.0-flash</div>
                        <div class="text-xs text-white/20 font-mono">$0.10/M</div>
                    </div>
                    <div class="text-xs text-white/30 mt-0.5">Rápido &middot; más reciente</div>
                </div>
                <div class="model-card rounded-lg px-3 py-2.5 cursor-pointer border transition-all duration-150"
                    data-model="gemini-1.5-pro" onclick="selectModel(this)">
                    <div class="flex items-center justify-between">
                        <div class="text-sm font-medium model-name">gemini-1.5-pro</div>
                        <div class="text-xs text-white/20 font-mono">$1.25/M</div>
                    </div>
                    <div class="text-xs text-white/30 mt-0.5">Potente &middot; más preciso</div>
                </div>
                <div class="model-card rounded-lg px-3 py-2.5 cursor-pointer border transition-all duration-150"
                    data-model="gemini-2.0-pro" onclick="selectModel(this)">
                    <div class="flex items-center justify-between">
                        <div class="text-sm font-medium model-name">gemini-2.0-pro</div>
                        <div class="text-xs text-white/20 font-mono">$2.00/M</div>
                    </div>
                    <div class="text-xs text-white/30 mt-0.5">Máxima calidad &middot; experimental</div>
                </div>
            </div>
        </div>

        <!-- Table -->
        <div class="glass rounded-xl overflow-hidden">
            <table class="w-full">
                <thead>
                    <tr class="text-white/40 text-xs uppercase tracking-wider border-b border-white/5">
                        <th class="py-3 px-4 text-left w-36">Hora</th>
                        <th class="py-3 px-4 text-left">Transcripcion</th>
                        <th class="py-3 px-4 text-right w-20">Dur.</th>
                        <th class="py-3 px-4 text-right w-20">Tokens</th>
                        <th class="py-3 px-4 text-center w-16"></th>
                    </tr>
                </thead>
                <tbody id="tbody"></tbody>
            </table>
            <div id="empty" class="hidden text-center py-12 text-white/20 text-sm">
                No hay transcripciones aun
            </div>
        </div>

        <!-- Footer -->
        <div class="mt-4 text-center text-white/15 text-xs">
            Howl &middot; Ctrl+Shift para grabar &middot; Groq Whisper
        </div>
    </div>

    <script>
        let allData = [];

        async function loadData() {
            const res = await fetch('/api/transcriptions');
            allData = await res.json();
            renderTable(allData);
        }

        function renderTable(data) {
            const tbody = document.getElementById('tbody');
            const empty = document.getElementById('empty');
            const badge = document.getElementById('count-badge');
            badge.textContent = data.length + ' total';

            if (data.length === 0) {
                tbody.innerHTML = '';
                empty.classList.remove('hidden');
                return;
            }
            empty.classList.add('hidden');

            tbody.innerHTML = data.map((t, i) => {
                const date = new Date(t.created_at + 'Z');
                const time = date.toLocaleString('es-MX', {
                    month: 'short', day: 'numeric',
                    hour: '2-digit', minute: '2-digit', second: '2-digit'
                });
                const dur = t.duration_seconds ? t.duration_seconds.toFixed(1) + 's' : '-';
                const tok = t.tokens ? t.tokens.toLocaleString() : '-';
                return `
                <tr class="row-hover border-b border-white/[0.03] cursor-pointer" onclick="toggleExpand(this)">
                    <td class="py-3 px-4 text-white/30 text-xs whitespace-nowrap align-top">${time}</td>
                    <td class="py-3 px-4 text-white/80 text-sm align-top">
                        <div class="text-preview" id="text-${i}">${escapeHtml(t.text)}</div>
                    </td>
                    <td class="py-3 px-4 text-white/20 text-xs text-right align-top">${dur}</td>
                    <td class="py-3 px-4 text-white/20 text-xs text-right align-top font-mono">${tok}</td>
                    <td class="py-3 px-4 text-center align-top">
                        <button onclick="event.stopPropagation(); copyText(${i}, this)"
                            class="text-white/20 hover:text-white/60 text-xs px-2 py-1 rounded hover:bg-white/5">
                            Copiar
                        </button>
                    </td>
                </tr>`;
            }).join('');
        }

        function toggleExpand(row) {
            const preview = row.querySelector('.text-preview');
            preview.classList.toggle('expanded');
        }

        function copyText(index, btn) {
            navigator.clipboard.writeText(allData[index].text);
            const row = btn.closest('tr');
            row.classList.add('copied');
            btn.textContent = 'OK';
            setTimeout(() => { btn.textContent = 'Copiar'; row.classList.remove('copied'); }, 1000);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Search
        document.getElementById('search').addEventListener('input', (e) => {
            const q = e.target.value.toLowerCase();
            if (!q) { renderTable(allData); return; }
            renderTable(allData.filter(t => t.text.toLowerCase().includes(q)));
        });

        function setActiveCard(modelValue) {
            document.querySelectorAll('.model-card').forEach(c => {
                c.classList.toggle('active', c.dataset.model === modelValue);
            });
        }

        async function loadSettings() {
            const res = await fetch('/api/settings');
            const data = await res.json();
            if (data.gemini_model) setActiveCard(data.gemini_model);
        }

        async function selectModel(card) {
            const model = card.dataset.model;
            setActiveCard(model);
            await fetch('/api/settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({gemini_model: model})
            });
            const st = document.getElementById('model-status');
            st.textContent = 'Guardado ✓';
            setTimeout(() => st.textContent = '', 2000);
        }

        async function loadStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('tokens-badge').textContent =
                data.total_tokens.toLocaleString() + ' tokens';
        }

        // Auto-refresh every 5 seconds
        loadData();
        loadSettings();
        loadStats();
        setInterval(() => { loadData(); loadStats(); }, 5000);
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/transcriptions")
def get_transcriptions():
    db = TranscriptionDB()
    return jsonify(db.get_recent(limit=200))

@app.route("/api/stats")
def get_stats():
    db = TranscriptionDB()
    return jsonify({"total_tokens": db.get_total_tokens(), "total_count": db.count()})

@app.route("/api/settings", methods=["GET"])
def get_settings():
    import config
    return jsonify({"gemini_model": config.GEMINI_MODEL})


@app.route("/api/settings", methods=["POST"])
def save_settings():
    import config
    data = request.get_json() or {}
    model = data.get("gemini_model", "gemini-1.5-flash")
    if model not in GEMINI_MODELS:
        return jsonify({"error": "Modelo no válido"}), 400
    config.GEMINI_MODEL = model
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump({"gemini_model": model}, f)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True, "gemini_model": model})


@app.route("/logo_small.png")
def logo():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    return send_from_directory(root_dir, "logo_small.png")


def start_web_server(port: int = 5000):
    """Start Flask in a daemon thread so it doesn't block the Qt event loop."""
    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
    return port
