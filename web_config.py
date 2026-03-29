#!/usr/bin/env python3
"""
Rafthercal web configuration interface.
Serves a minimal UI to edit config.py and RML templates.

Usage:
    python3 web_config.py [--config-dir /path/to/working/dir] [--host 0.0.0.0] [--port 5000]

  --config-dir  Directory containing config.py and local templates/ overrides.
                Defaults to the current working directory.

Basic auth can be enabled by setting environment variables:
    WEB_USERNAME=admin WEB_PASSWORD=secret python3 web_config.py
"""

import os
import sys
import functools
import subprocess
import pathlib
import argparse

from flask import Flask, request, redirect, url_for, render_template_string, flash, Response

# Source tree (where this script and the package live)
BASE_DIR = pathlib.Path(__file__).parent.resolve()

# Working directory: where config.py and local template overrides live.
# Set by --config-dir; defaults to cwd. Resolved after arg parsing below.
CONFIG_DIR: pathlib.Path = None  # filled in by parse_args() at startup

# Files that may be edited, keyed by a URL-safe identifier.
# Values are the WRITE path (always in CONFIG_DIR). Reads fall back to the
# package template when the CONFIG_DIR copy doesn't exist yet.
def get_editable_files():
    files = {}

    files["config.py"] = CONFIG_DIR / "config.py"

    pkg_dir = BASE_DIR / "src" / "rafthercal" / "templates"
    local_dir = CONFIG_DIR / "templates"

    seen = set()
    for d in [local_dir, pkg_dir]:
        if not d.is_dir():
            continue
        for rml in sorted(d.glob("*.rml")):
            if rml.name not in seen:
                seen.add(rml.name)
                files[f"templates/{rml.name}"] = local_dir / rml.name

    return files


def read_template(file_id, write_path):
    """Return content for a template, falling back to the package copy."""
    if write_path.exists():
        return write_path.read_text(encoding="utf-8")
    pkg = BASE_DIR / "src" / "rafthercal" / "templates" / write_path.name
    return pkg.read_text(encoding="utf-8") if pkg.exists() else ""


def customised_templates():
    """Set of template filenames that have a local override in CONFIG_DIR."""
    local_dir = CONFIG_DIR / "templates"
    if not local_dir.is_dir():
        return set()
    return {f.name for f in local_dir.glob("*.rml")}


app = Flask(__name__)
app.secret_key = os.urandom(24)

WEB_USERNAME = os.environ.get("WEB_USERNAME", "")
WEB_PASSWORD = os.environ.get("WEB_PASSWORD", "")


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not WEB_USERNAME or not WEB_PASSWORD:
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or auth.username != WEB_USERNAME or auth.password != WEB_PASSWORD:
            return Response(
                "Authentication required.",
                401,
                {"WWW-Authenticate": 'Basic realm="Rafthercal Config"'},
            )
        return f(*args, **kwargs)
    return decorated


HTML_BASE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rafthercal Config</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: monospace; margin: 0; background: #1a1a1a; color: #e0e0e0; }
  header { background: #111; padding: 12px 20px; display: flex; align-items: center; gap: 20px; border-bottom: 1px solid #333; }
  header h1 { margin: 0; font-size: 1.1rem; color: #ccc; }
  header a { color: #6af; text-decoration: none; font-size: 0.9rem; }
  header a:hover { text-decoration: underline; }
  .container { display: flex; height: calc(100vh - 49px); }
  nav { width: 220px; min-width: 180px; background: #141414; border-right: 1px solid #333; overflow-y: auto; padding: 10px 0; flex-shrink: 0; }
  nav .section { font-size: 0.7rem; color: #666; padding: 8px 14px 4px; text-transform: uppercase; letter-spacing: 0.05em; }
  nav a { display: flex; justify-content: space-between; align-items: center; padding: 6px 14px; color: #aaa; text-decoration: none; font-size: 0.85rem; gap: 6px; }
  nav a span.name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  nav a span.pattern { color: #555; font-size: 0.75rem; white-space: nowrap; flex-shrink: 0; }
  nav a span.custom { color: #6a8; font-size: 0.75rem; flex-shrink: 0; }
  nav a:hover { background: #222; color: #ddd; }
  nav a.active { background: #1e3a5f; color: #6af; }
  main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  .editor-header { padding: 10px 16px; background: #181818; border-bottom: 1px solid #333; display: flex; align-items: center; gap: 12px; }
  .editor-header h2 { margin: 0; font-size: 0.95rem; color: #bbb; flex: 1; }
  textarea { flex: 1; width: 100%; background: #0d0d0d; color: #d4d4d4; border: none; outline: none; padding: 16px; font-family: monospace; font-size: 0.88rem; line-height: 1.5; resize: none; tab-size: 4; }
  .form-full { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
  button { background: #1e4d8c; color: #e0e0e0; border: none; padding: 7px 16px; cursor: pointer; font-family: monospace; font-size: 0.85rem; border-radius: 3px; }
  button:hover { background: #2a62b0; }
  button.danger { background: #6b2020; }
  button.danger:hover { background: #8b2a2a; }
  .flash { padding: 8px 16px; font-size: 0.85rem; }
  .flash.ok { background: #1a3a1a; color: #6d6; border-bottom: 1px solid #2a4a2a; }
  .flash.err { background: #3a1a1a; color: #d66; border-bottom: 1px solid #4a2a2a; }
  .index-page { padding: 30px; }
  .index-page p { color: #888; line-height: 1.6; }
  .actions { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
  .log-page { padding: 20px; display: flex; flex-direction: column; height: 100%; }
  .log-page h2 { margin: 0 0 12px; font-size: 0.95rem; color: #bbb; }
  pre#log { flex: 1; background: #0d0d0d; color: #d4d4d4; padding: 14px; overflow-y: auto; font-size: 0.82rem; line-height: 1.5; margin: 0; border: 1px solid #333; border-radius: 3px; white-space: pre-wrap; }
  .run-label { color: #aaa; font-size: 0.85rem; display: flex; align-items: center; gap: 6px; }
  .output-panel { display: none; flex-direction: column; border-top: 1px solid #333; flex: 0 0 40%; min-height: 0; }
  .output-panel.visible { display: flex; }
  .output-panel pre { flex: 1; margin: 0; padding: 14px; background: #0d0d0d; color: #d4d4d4; font-size: 0.82rem; line-height: 1.5; overflow-y: auto; white-space: pre; font-family: monospace; }
  .output-panel pre.error { color: #d66; }
  .output-header { padding: 6px 14px; background: #181818; border-bottom: 1px solid #333; font-size: 0.8rem; color: #666; display: flex; justify-content: space-between; }
  .output-header button { background: none; border: none; color: #555; cursor: pointer; padding: 0; font-size: 0.8rem; }
  .output-header button:hover { color: #aaa; background: none; }
</style>
</head>
<body>
<header>
  <h1>rafthercal</h1>
</header>
<div class="container">
<nav>
  <div class="section">Admin</div>
  <a href="{{ url_for('index') }}"
     class="{{ 'active' if active_file == '__index__' else '' }}"><span class="name">admin</span></a>
  <div class="section">Config</div>
  <a href="{{ url_for('edit_file', file_id='config.py') }}"
     class="{{ 'active' if active_file == 'config.py' else '' }}"><span class="name">config.py</span></a>
  {% if configured_templates %}
  <div class="section">Main templates</div>
  {% for filename, pattern in configured_templates %}
  {% set key = 'templates/' + filename %}
  <a href="{{ url_for('edit_file', file_id=key) }}"
     class="{{ 'active' if active_file == key else '' }}"><span class="name">{{ filename }}</span><span class="pattern">[{{ pattern }}]</span>{% if filename in customised %}<span class="custom">·</span>{% endif %}</a>
  {% endfor %}
  {% endif %}
  {% if template_files %}
  <div class="section">Templates</div>
  {% for key in template_files %}
  {% set fname = key.split('/')[-1] %}
  <a href="{{ url_for('edit_file', file_id=key) }}"
     class="{{ 'active' if active_file == key else '' }}"><span class="name">{{ fname }}</span>{% if fname in customised %}<span class="custom">·</span>{% endif %}</a>
  {% endfor %}
  {% endif %}
</nav>
<main>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
  <div class="flash {{ cat }}">{{ msg }}</div>
  {% endfor %}
{% endwith %}
{% block content %}{% endblock %}
</main>
</div>
</body>
</html>"""

INDEX_TMPL = HTML_BASE.replace(
    "{% block content %}{% endblock %}",
    """<div class="index-page">
  <p>Select a file from the sidebar to edit it.</p>
  <p>Editing a template saves it to your config directory, overriding the shipped version.<br>
     Customised templates are marked with <span style="color:#6a8">·</span> in the sidebar.</p>
  <div class="actions">
    <form method="post" action="{{ url_for('restart') }}">
      <button class="danger" type="submit">Restart service</button>
    </form>
    <form method="post" action="{{ url_for('update') }}">
      <button class="danger" type="submit">Update app</button>
    </form>
  </div>
</div>""",
)

UPDATE_TMPL = HTML_BASE.replace(
    "{% block content %}{% endblock %}",
    """<div class="log-page">
  <h2>Updating&hellip;</h2>
  <pre id="log"></pre>
</div>
<script>
const pre = document.getElementById('log');
const es = new EventSource('{{ url_for("update_stream") }}');
es.onmessage = e => {
  pre.textContent += e.data + '\\n';
  pre.scrollTop = pre.scrollHeight;
};
es.addEventListener('done', e => {
  es.close();
  const status = e.data === '0' ? ' — done' : ' — failed (exit ' + e.data + ')';
  document.querySelector('h2').textContent = 'Update' + status;
});
es.onerror = () => es.close();
</script>""",
)

EDITOR_TMPL = HTML_BASE.replace(
    "{% block content %}{% endblock %}",
    """<form class="form-full" method="post" id="editor-form">
  <div class="editor-header">
    <h2>{{ active_file }}</h2>
    {% if is_main %}
    <label class="run-label"><input type="radio" name="run_mode" value="rml" checked> Raw</label>
    <label class="run-label"><input type="radio" name="run_mode" value="simulate"> Simulated</label>
    <button type="button" id="btn-run">Run</button>
    <button type="button" id="btn-print">Print</button>
    {% endif %}
    <button type="submit">Save</button>
  </div>
  <textarea name="content" spellcheck="false" autocorrect="off" autocapitalize="off">{{ content }}</textarea>
  {% if is_main %}
  <div class="output-panel" id="output-panel">
    <div class="output-header">
      <span id="output-label">Output</span>
      <button type="button" onclick="closeOutput()">✕</button>
    </div>
    <pre id="output-pre"></pre>
  </div>
  <script>
  const template = {{ template_name | tojson }};
  function closeOutput() {
    document.getElementById('output-panel').classList.remove('visible');
  }
  function streamRun(url) {
    const panel = document.getElementById('output-panel');
    const pre = document.getElementById('output-pre');
    const label = document.getElementById('output-label');
    pre.textContent = '';
    pre.className = '';
    panel.classList.add('visible');
    label.textContent = 'Running…';
    const es = new EventSource(url);
    es.onmessage = e => { pre.textContent += e.data + '\\n'; pre.scrollTop = pre.scrollHeight; };
    es.addEventListener('done', e => {
      es.close();
      label.textContent = e.data === '0' ? 'Output' : 'Output (error)';
      if (e.data !== '0') pre.className = 'error';
    });
    es.onerror = () => { es.close(); label.textContent = 'Output (connection error)'; };
  }
  document.getElementById('btn-run').addEventListener('click', () => {
    const mode = document.querySelector('input[name=run_mode]:checked').value;
    streamRun('/run/' + encodeURIComponent(template) + '?mode=' + mode);
  });
  document.getElementById('btn-print').addEventListener('click', () => {
    const label = document.getElementById('output-label');
    const panel = document.getElementById('output-panel');
    panel.classList.add('visible');
    streamRun('/run/' + encodeURIComponent(template) + '?mode=print');
  });
  </script>
  {% endif %}
</form>""",
)


def nav_context():
    files = get_editable_files()
    configured = get_configured_templates()
    configured_names = {fn for fn, _ in configured}
    template_files = [k for k in files if k.startswith("templates/") and k[len("templates/"):] not in configured_names]
    customised = customised_templates()
    return files, configured, template_files, customised


@app.route("/")
@require_auth
def index():
    files, configured_templates, template_files, customised = nav_context()
    return render_template_string(
        INDEX_TMPL,
        active_file="__index__",
        template_files=template_files,
        customised=customised,
        configured_templates=configured_templates,
        all_files=files,
    )


@app.route("/edit/<path:file_id>", methods=["GET", "POST"])
@require_auth
def edit_file(file_id):
    files, configured_templates, template_files, customised = nav_context()

    # Security: only allow whitelisted identifiers
    if file_id not in files:
        return "Not found", 404

    path = files[file_id]

    if request.method == "POST":
        content = request.form.get("content", "").replace("\r\n", "\n").replace("\r", "\n")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            flash("Saved.", "ok")
        except OSError as e:
            flash(f"Error saving: {e}", "err")
        return redirect(url_for("edit_file", file_id=file_id))

    if file_id == "config.py":
        if path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            sample = BASE_DIR / "src" / "rafthercal" / "config.py.sample"
            content = sample.read_text(encoding="utf-8") if sample.exists() else ""
    else:
        content = read_template(file_id, path)

    fname = file_id.split("/")[-1]
    is_main = fname in {fn for fn, _ in configured_templates}
    return render_template_string(
        EDITOR_TMPL,
        active_file=file_id,
        template_files=template_files,
        customised=customised,
        configured_templates=configured_templates,
        all_files=files,
        content=content,
        is_main=is_main,
        template_name=fname,
    )


@app.route("/restart", methods=["POST"])
@require_auth
def restart():
    script = BASE_DIR / "scripts" / "restart-rafthercal"
    try:
        result = subprocess.run(
            [str(script)], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            flash("Service restarted.", "ok")
        else:
            flash(f"Restart failed: {result.stderr.strip()}", "err")
    except FileNotFoundError:
        flash("restart-rafthercal script not found.", "err")
    except subprocess.TimeoutExpired:
        flash("Restart timed out.", "err")
    return redirect(url_for("index"))


@app.route("/update", methods=["POST"])
@require_auth
def update():
    files, configured_templates, template_files, customised = nav_context()
    return render_template_string(
        UPDATE_TMPL,
        active_file=None,
        template_files=template_files,
        customised=customised,
        configured_templates=configured_templates,
        all_files=files,
    )


@app.route("/update/stream")
@require_auth
def update_stream():
    script = BASE_DIR / "scripts" / "update-rafthercal"

    def generate():
        try:
            proc = subprocess.Popen(
                [str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in proc.stdout:
                yield f"data: {line.rstrip()}\n\n"
            proc.wait()
            yield f"event: done\ndata: {proc.returncode}\n\n"
        except FileNotFoundError:
            yield "data: update-rafthercal script not found.\n\n"
            yield "event: done\ndata: 1\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


RENDER_SCRIPT = """\
import sys, os
sys.path.insert(0, {src!r})
os.chdir({config_dir!r})
from rafthercal.rafthercal import load_context, load_template
context = load_context()
tmpl = load_template({template!r})
rml_str = tmpl.render(context)
"""

RENDER_SCRIPT_RML = RENDER_SCRIPT + "print(rml_str)\n"

RENDER_SCRIPT_SIMULATE = RENDER_SCRIPT + """\
from io import BytesIO
from rml.rml import print_from_str
from rml.simulate import simulate_print
buf = BytesIO()
print_from_str(rml_str, buf)
simulate_print(buf)
"""


def get_template_names():
    """All .rml filenames available for rendering, local overrides first."""
    seen = set()
    names = []
    for d in [CONFIG_DIR / "templates", BASE_DIR / "src" / "rafthercal" / "templates"]:
        if d.is_dir():
            for f in sorted(d.glob("*.rml")):
                if f.name not in seen:
                    seen.add(f.name)
                    names.append(f.name)
    return names


def get_configured_templates():
    """Return RAFTHERCAL_TEMPLATES from config.py (falling back to config.py.sample)
    as a list of (filename, pattern_label)."""
    import importlib.util
    candidates = [
        CONFIG_DIR / "config.py",
        BASE_DIR / "src" / "rafthercal" / "config.py.sample",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location("_rafthercal_config", path)
            cfg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfg)
            entries = getattr(cfg, "RAFTHERCAL_TEMPLATES", [])
            if entries:
                return [
                    (e["filename"], e["pattern"] if e.get("pattern") is not None else "default")
                    for e in entries
                ]
        except Exception:
            continue
    return []


RENDER_SCRIPT_PRINT = RENDER_SCRIPT + """\
import config as _config
from rml.rml import print_from_str
out_file = _config.RAFTHERCAL_SERIAL_DEVICE
print_from_str(rml_str, out_file)
print("Sent to printer.")
"""


@app.route("/run/<template_name>")
@require_auth
def run_template(template_name):
    # Validate: only allow known template filenames
    known = get_template_names()
    if template_name not in known:
        return "Not found", 404

    mode = request.args.get("mode", "rml")
    script_tmpl = {"rml": RENDER_SCRIPT_RML, "simulate": RENDER_SCRIPT_SIMULATE, "print": RENDER_SCRIPT_PRINT}.get(mode, RENDER_SCRIPT_RML)
    script = script_tmpl.format(
        src=str(BASE_DIR / "src"),
        config_dir=str(CONFIG_DIR),
        template=template_name,
    )

    def generate():
        try:
            proc = subprocess.Popen(
                [str(BASE_DIR / "venv" / "bin" / "python3"), "-c", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(CONFIG_DIR),
            )
            for line in proc.stdout:
                yield f"data: {line.rstrip()}\n\n"
            proc.wait()
            yield f"event: done\ndata: {proc.returncode}\n\n"
        except Exception as e:
            yield f"data: {e}\n\n"
            yield "event: done\ndata: 1\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rafthercal web config UI")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port (default: 5000)")
    parser.add_argument("--config-dir", default=None,
                        help="Directory containing config.py and local templates/. "
                             "Overrides RAFTHERCAL_CONFIG_DIR env var. Defaults to cwd.")
    args = parser.parse_args()

    config_dir_str = args.config_dir or os.environ.get("RAFTHERCAL_CONFIG_DIR") or str(pathlib.Path.cwd())
    CONFIG_DIR = pathlib.Path(config_dir_str).resolve()
    print(f"Config directory: {CONFIG_DIR}")

    if WEB_USERNAME and WEB_PASSWORD:
        print(f"Basic auth enabled for user '{WEB_USERNAME}'")
    else:
        print("WARNING: No auth configured. Set WEB_USERNAME and WEB_PASSWORD env vars to enable.")

    app.run(host=args.host, port=args.port, debug=False)
