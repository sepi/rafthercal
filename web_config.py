#!/usr/bin/env python3
"""
Rafthercal web configuration interface.
Serves a minimal UI to edit config.py and RML templates.

Usage:
    python3 web_config.py [--host 0.0.0.0] [--port 5000]

Basic auth can be enabled by setting environment variables:
    WEB_USERNAME=admin WEB_PASSWORD=secret python3 web_config.py
"""

import os
import functools
import subprocess
import pathlib
import argparse

from flask import Flask, request, redirect, url_for, render_template_string, flash, Response

BASE_DIR = pathlib.Path(__file__).parent.resolve()

# Files that may be edited, keyed by a URL-safe identifier
def get_editable_files():
    files = {}

    config_file = BASE_DIR / "config.py"
    if config_file.exists():
        files["config.py"] = config_file
    else:
        # Still allow editing even if it doesn't exist yet (create from sample)
        files["config.py"] = config_file

    templates_dir = BASE_DIR / "src" / "rafthercal" / "templates"
    if templates_dir.is_dir():
        for rml in sorted(templates_dir.glob("*.rml")):
            files[f"templates/{rml.name}"] = rml

    # Local override templates directory
    local_templates = BASE_DIR / "templates"
    if local_templates.is_dir():
        for rml in sorted(local_templates.glob("*.rml")):
            key = f"local/{rml.name}"
            if key not in files:
                files[key] = rml

    return files


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
  nav a { display: block; padding: 6px 14px; color: #aaa; text-decoration: none; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
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
</style>
</head>
<body>
<header>
  <h1>rafthercal config</h1>
  <a href="{{ url_for('index') }}">home</a>
</header>
<div class="container">
<nav>
  <div class="section">Config</div>
  <a href="{{ url_for('edit_file', file_id='config.py') }}"
     class="{{ 'active' if active_file == 'config.py' else '' }}">config.py</a>
  <div class="section">Templates</div>
  {% for key in template_files %}
  <a href="{{ url_for('edit_file', file_id=key) }}"
     class="{{ 'active' if active_file == key else '' }}">{{ key.split('/')[-1] }}</a>
  {% endfor %}
  {% if local_files %}
  <div class="section">Local overrides</div>
  {% for key in local_files %}
  <a href="{{ url_for('edit_file', file_id=key) }}"
     class="{{ 'active' if active_file == key else '' }}">{{ key.split('/')[-1] }}</a>
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
  <p>Templates in <code>src/rafthercal/templates/</code> are the active package templates.<br>
     Files in <code>templates/</code> (local overrides) take precedence when present.</p>
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
    """<form class="form-full" method="post">
  <div class="editor-header">
    <h2>{{ active_file }}</h2>
    <button type="submit">Save</button>
  </div>
  <textarea name="content" spellcheck="false" autocorrect="off" autocapitalize="off">{{ content }}</textarea>
</form>""",
)


def nav_context():
    files = get_editable_files()
    template_files = [k for k in files if k.startswith("templates/")]
    local_files = [k for k in files if k.startswith("local/")]
    return files, template_files, local_files


@app.route("/")
@require_auth
def index():
    files, template_files, local_files = nav_context()
    return render_template_string(
        INDEX_TMPL,
        active_file=None,
        template_files=template_files,
        local_files=local_files,
    )


@app.route("/edit/<path:file_id>", methods=["GET", "POST"])
@require_auth
def edit_file(file_id):
    files, template_files, local_files = nav_context()

    # Security: only allow whitelisted identifiers
    if file_id not in files:
        return "Not found", 404

    path = files[file_id]

    if request.method == "POST":
        content = request.form.get("content", "")
        try:
            path.write_text(content, encoding="utf-8")
            flash("Saved.", "ok")
        except OSError as e:
            flash(f"Error saving: {e}", "err")
        return redirect(url_for("edit_file", file_id=file_id))

    if path.exists():
        content = path.read_text(encoding="utf-8")
    else:
        # Offer the sample as a starting point for config.py
        sample = BASE_DIR / "src" / "rafthercal" / "config.py.sample"
        content = sample.read_text(encoding="utf-8") if sample.exists() else ""

    return render_template_string(
        EDITOR_TMPL,
        active_file=file_id,
        template_files=template_files,
        local_files=local_files,
        content=content,
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
    files, template_files, local_files = nav_context()
    return render_template_string(
        UPDATE_TMPL,
        active_file=None,
        template_files=template_files,
        local_files=local_files,
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rafthercal web config UI")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port (default: 5000)")
    args = parser.parse_args()

    if WEB_USERNAME and WEB_PASSWORD:
        print(f"Basic auth enabled for user '{WEB_USERNAME}'")
    else:
        print("WARNING: No auth configured. Set WEB_USERNAME and WEB_PASSWORD env vars to enable.")

    app.run(host=args.host, port=args.port, debug=False)
