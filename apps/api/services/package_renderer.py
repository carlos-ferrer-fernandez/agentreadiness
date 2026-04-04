"""
Package Renderer Service

Renders individual pages within a documentation package with shared navigation chrome.
Each page type has its own renderer. The agents page reuses render_agent_page_html.
"""

import datetime
from typing import List, Optional

from services.agent_page_generator import render_agent_page_html, _esc


# ---------------------------------------------------------------------------
# Shared CSS + Navigation
# ---------------------------------------------------------------------------

SHARED_CSS = """\
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#FAFAF8;--surface:#FFFFFF;--border:#E5E5E0;--text:#1A1A1A;
  --light:#6B6B6B;--accent:#1A7A4C;--green:#16A34A;--red:#DC2626;
  --amber:#D97706;--radius:10px;
}
body{
  font-family:'Plus Jakarta Sans',system-ui,-apple-system,sans-serif;
  background:var(--bg);color:var(--text);margin:0;line-height:1.5;
  font-size:14px;
}
.layout{display:flex;min-height:100vh}

/* Sidebar */
.sidebar{
  width:260px;background:var(--surface);border-right:1px solid var(--border);
  padding:1.25rem 0;position:fixed;top:0;left:0;bottom:0;overflow-y:auto;
  z-index:100;
}
.sidebar-brand{
  padding:0 1.25rem 1rem;border-bottom:1px solid var(--border);margin-bottom:0.75rem;
}
.sidebar-brand h2{
  font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:1.15rem;
  color:var(--text);margin:0;
}
.sidebar-brand p{font-size:0.72rem;color:var(--light);margin-top:0.15rem}
.sidebar-nav{list-style:none;padding:0;margin:0}
.sidebar-nav li{margin:0}
.sidebar-nav a{
  display:flex;align-items:center;gap:0.5rem;padding:0.5rem 1.25rem;
  text-decoration:none;color:var(--text);font-size:0.82rem;font-weight:500;
  border-left:3px solid transparent;transition:all 0.15s;
}
.sidebar-nav a:hover{background:rgba(26,122,76,0.04);color:var(--accent)}
.sidebar-nav a.active{
  background:rgba(26,122,76,0.06);color:var(--accent);
  border-left-color:var(--accent);font-weight:700;
}
.sidebar-nav .locked{opacity:0.5}
.sidebar-nav .lock-icon{font-size:0.7rem;margin-left:auto;color:var(--light)}
.sidebar-nav .page-icon{font-size:0.9rem;width:1.1rem;text-align:center}

/* Main content */
.main{margin-left:260px;flex:1;min-width:0}
.page-content{max-width:820px;margin:0 auto;padding:2rem 2.5rem 3rem}

/* Common page elements */
h1{font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:2rem;margin-bottom:0.5rem}
h2{font-size:1.1rem;font-weight:700;color:var(--text);margin:1.75rem 0 0.75rem;padding-bottom:0.4rem;border-bottom:1px solid var(--border)}
h3{font-size:0.9rem;font-weight:700;margin:1rem 0 0.5rem}
h4{font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:var(--light);margin:0.75rem 0 0.35rem}
p{margin:0.5rem 0;color:var(--text);font-size:0.88rem;line-height:1.6}
ul,ol{padding-left:1.25rem;margin:0.4rem 0}
li{margin-bottom:0.25rem;font-size:0.85rem;line-height:1.5}
code{
  font-family:'JetBrains Mono',monospace;font-size:0.8rem;
  background:rgba(0,0,0,0.04);padding:0.1rem 0.35rem;border-radius:4px;
}
pre{
  background:#1A1A1A;color:#E5E5E0;padding:1rem;border-radius:8px;
  overflow-x:auto;margin:0.75rem 0;font-size:0.78rem;line-height:1.5;
}
pre code{background:none;padding:0;color:inherit}
a{color:var(--accent);text-decoration:none;font-weight:600}
a:hover{text-decoration:underline}

/* Cards */
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1.25rem 1.5rem;margin-bottom:1rem}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.75rem}
.mini-card{background:var(--bg);border-radius:8px;padding:0.85rem 1rem}
.mini-card h4{margin:0 0 0.3rem;font-size:0.82rem;color:var(--accent);text-transform:none;letter-spacing:0}
.mini-card p{font-size:0.78rem;margin:0;color:var(--light)}

/* Badge */
.badge{
  display:inline-block;padding:0.15rem 0.5rem;border-radius:100px;
  font-size:0.65rem;font-weight:700;letter-spacing:0.04em;
}

/* Table */
table{width:100%;border-collapse:collapse;font-size:0.82rem;margin:0.75rem 0}
th{text-align:left;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:var(--light);padding:0.5rem 0.6rem;border-bottom:2px solid var(--border)}
td{padding:0.5rem 0.6rem;border-bottom:1px solid var(--border);vertical-align:top}

/* Lock overlay */
.page-locked{position:relative;min-height:300px}
.page-locked .page-content-inner{filter:blur(6px);opacity:0.25;pointer-events:none;user-select:none}
.lock-overlay{
  position:absolute;top:0;left:0;right:0;bottom:0;
  display:flex;align-items:center;justify-content:center;z-index:10;
  background:linear-gradient(180deg,rgba(250,250,248,0) 0%,rgba(250,250,248,0.95) 50%);
}
.lock-cta{
  text-align:center;padding:1.5rem 2rem;background:var(--surface);
  border:1px solid var(--border);border-radius:var(--radius);
  box-shadow:0 8px 32px rgba(0,0,0,0.08);
}
.lock-cta svg{color:var(--accent);margin-bottom:0.5rem}
.lock-cta p{font-weight:700;color:var(--text);margin-bottom:0.75rem;font-size:1rem}
.unlock-btn{
  display:inline-block;padding:0.6rem 2rem;background:var(--accent);color:#fff;
  border-radius:100px;font-weight:700;text-decoration:none;font-size:0.88rem;
  transition:background 0.15s;
}
.unlock-btn:hover{background:#15603B}

.empty{color:#C0BDB8;font-style:italic}

/* Footer */
footer{text-align:center;padding:1.5rem 0;color:var(--light);font-size:0.72rem;border-top:1px solid var(--border);margin-top:2rem}

/* Responsive */
@media(max-width:768px){
  .sidebar{display:none}
  .main{margin-left:0}
  .page-content{padding:1.5rem 1rem}
  .card-grid{grid-template-columns:1fr}
}
"""

PAGE_ICONS = {
    "overview": "&#128218;",      # book
    "agents": "&#129302;",        # robot
    "getting-started": "&#128640;", # rocket
    "authentication": "&#128274;", # lock
    "core-concepts": "&#128161;", # lightbulb
    "rules": "&#128220;",        # scroll
    "troubleshooting": "&#128295;", # wrench
    "faq": "&#10067;",           # question mark
    "resources": "&#128279;",    # link
    "workflow": "&#9881;",       # gear
}


def _get_page_icon(page_type: str) -> str:
    if page_type.startswith("workflow"):
        return PAGE_ICONS["workflow"]
    return PAGE_ICONS.get(page_type, "&#128196;")


def _render_sidebar(product_name: str, package_slug: str, page_map: list, current_page_slug: str, is_paid: bool) -> str:
    """Render the sidebar navigation."""
    nav_items = ""
    for entry in page_map:
        slug = entry["slug"]
        title = entry["title"]
        page_type = entry.get("page_type", "")
        tier = entry.get("tier", "full")
        icon = _get_page_icon(page_type)

        active = "active" if slug == current_page_slug else ""
        locked = not is_paid and tier == "full"
        locked_cls = " locked" if locked else ""
        lock_icon = '<span class="lock-icon">&#128274;</span>' if locked else ""

        href = f"/packages/{_esc(package_slug)}/{_esc(slug)}"
        nav_items += (
            f'<li><a href="{href}" class="{active}{locked_cls}">'
            f'<span class="page-icon">{icon}</span>'
            f'{_esc(title)}'
            f'{lock_icon}'
            f'</a></li>'
        )

    return f"""\
    <nav class="sidebar">
      <div class="sidebar-brand">
        <h2>{_esc(product_name)}</h2>
        <p>AI-Ready Documentation</p>
      </div>
      <ul class="sidebar-nav">
        {nav_items}
      </ul>
    </nav>"""


def _render_lock_overlay(package_slug: str) -> str:
    return (
        '<div class="lock-overlay">'
        '<div class="lock-cta">'
        '<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
        '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>'
        '<p>Unlock Full Documentation Package &mdash; $99</p>'
        f'<a href="/packages/{_esc(package_slug)}" class="unlock-btn">Unlock Now</a>'
        '</div></div>'
    )


# ---------------------------------------------------------------------------
# Per-page-type renderers
# ---------------------------------------------------------------------------

def _render_overview_content(data: dict) -> str:
    """Render overview page content."""
    tagline = data.get("tagline", "")
    what_it_does = data.get("what_it_does", [])
    key_concepts = data.get("key_concepts", [])
    capabilities = data.get("capabilities", [])
    integrations = data.get("integrations", [])
    when_to_use = data.get("when_to_use", [])
    when_not = data.get("when_not_to_use", [])
    links = data.get("links", [])

    tagline_html = f'<p style="font-size:1rem;color:var(--light);margin-bottom:1.5rem">{_esc(tagline)}</p>' if tagline else ""

    # What it does
    what_html = ""
    if what_it_does:
        bullets = "".join(f"<li>{_esc(str(w))}</li>" for w in what_it_does)
        what_html = f'<section class="card"><h2>What It Does</h2><ul>{bullets}</ul></section>'

    # Key concepts
    concepts_html = ""
    if key_concepts:
        cards = ""
        for c in key_concepts:
            if isinstance(c, dict):
                cards += f'<div class="mini-card"><h4>{_esc(c.get("term", ""))}</h4><p>{_esc(c.get("definition", ""))}</p></div>'
            else:
                cards += f'<div class="mini-card"><p>{_esc(str(c))}</p></div>'
        concepts_html = f'<section class="card"><h2>Key Concepts</h2><div class="card-grid">{cards}</div></section>'

    # Capabilities
    cap_html = ""
    if capabilities:
        cards = ""
        for c in capabilities:
            if isinstance(c, dict):
                cards += f'<div class="mini-card"><h4>{_esc(c.get("name", ""))}</h4><p>{_esc(c.get("description", ""))}</p></div>'
            else:
                cards += f'<div class="mini-card"><p>{_esc(str(c))}</p></div>'
        cap_html = f'<section class="card"><h2>Capabilities</h2><div class="card-grid">{cards}</div></section>'

    # Integrations
    integ_html = ""
    if integrations:
        pills = "".join(f'<span class="badge" style="background:#DBEAFE;color:#1E40AF;margin:0.15rem">{_esc(str(i))}</span>' for i in integrations)
        integ_html = f'<section class="card"><h2>Integrations</h2><div>{pills}</div></section>'

    # When to use / not
    use_html = ""
    if when_to_use or when_not:
        use_bullets = "".join(f"<li>{_esc(str(w))}</li>" for w in when_to_use)
        not_bullets = "".join(f"<li>{_esc(str(w))}</li>" for w in when_not)
        use_section = f'<div><h3 style="color:var(--green)">When to use</h3><ul>{use_bullets}</ul></div>' if use_bullets else ""
        not_section = f'<div><h3 style="color:var(--red)">When not to use</h3><ul>{not_bullets}</ul></div>' if not_bullets else ""
        use_html = f'<section class="card">{use_section}{not_section}</section>'

    # Links
    links_html = ""
    if links:
        items = ""
        for l in links:
            if isinstance(l, dict):
                items += f'<li><a href="{_esc(l.get("url", "#"))}" target="_blank">{_esc(l.get("label", "Link"))}</a></li>'
        if items:
            links_html = f'<section class="card"><h2>Key Links</h2><ul style="list-style:none;padding:0">{items}</ul></section>'

    return f"{tagline_html}{what_html}{concepts_html}{cap_html}{integ_html}{use_html}{links_html}"


def _render_getting_started_content(data: dict) -> str:
    """Render getting-started page content."""
    prereqs = data.get("prerequisites", [])
    steps = data.get("install_steps", [])
    first_call = data.get("first_api_call", {})
    auth = data.get("auth_setup", {})
    next_steps = data.get("common_next_steps", [])
    gotchas = data.get("gotchas", [])

    # Prerequisites
    prereq_html = ""
    if prereqs:
        bullets = "".join(f"<li>{_esc(str(p))}</li>" for p in prereqs)
        prereq_html = f'<section class="card"><h2>Prerequisites</h2><ul>{bullets}</ul></section>'

    # Install steps
    steps_html = ""
    if steps:
        items = ""
        for s in steps:
            if isinstance(s, dict):
                instruction = s.get("instruction", "")
                code = s.get("code_snippet", "")
                items += f"<li><p>{_esc(instruction)}</p>"
                if code:
                    items += f"<pre><code>{_esc(code)}</code></pre>"
                items += "</li>"
            else:
                items += f"<li>{_esc(str(s))}</li>"
        steps_html = f'<section class="card"><h2>Installation</h2><ol>{items}</ol></section>'

    # First API call
    call_html = ""
    if first_call and isinstance(first_call, dict):
        desc = first_call.get("description", "")
        code = first_call.get("code_snippet", "")
        resp = first_call.get("expected_response", "")
        inner = f"<p>{_esc(desc)}</p>" if desc else ""
        if code:
            inner += f"<pre><code>{_esc(code)}</code></pre>"
        if resp:
            inner += f'<h4>Expected Response</h4><pre><code>{_esc(resp)}</code></pre>'
        call_html = f'<section class="card"><h2>First API Call</h2>{inner}</section>'

    # Auth setup
    auth_html = ""
    if auth and isinstance(auth, dict):
        method = auth.get("method", "")
        auth_steps = auth.get("steps", [])
        inner = f'<p><strong>Method:</strong> {_esc(method)}</p>' if method else ""
        if auth_steps:
            bullets = "".join(f"<li>{_esc(str(s))}</li>" for s in auth_steps)
            inner += f"<ol>{bullets}</ol>"
        auth_html = f'<section class="card"><h2>Authentication Setup</h2>{inner}</section>'

    # Next steps
    next_html = ""
    if next_steps:
        cards = ""
        for n in next_steps:
            if isinstance(n, dict):
                cards += f'<div class="mini-card"><h4>{_esc(n.get("action", ""))}</h4><p>{_esc(n.get("description", ""))}</p></div>'
            else:
                cards += f'<div class="mini-card"><p>{_esc(str(n))}</p></div>'
        next_html = f'<section class="card"><h2>What Next?</h2><div class="card-grid">{cards}</div></section>'

    # Gotchas
    gotcha_html = ""
    if gotchas:
        bullets = "".join(f"<li>{_esc(str(g))}</li>" for g in gotchas)
        gotcha_html = f'<section class="card"><h2>Common Gotchas</h2><ul>{bullets}</ul></section>'

    return f"{prereq_html}{steps_html}{call_html}{auth_html}{next_html}{gotcha_html}"


def _render_auth_content(data: dict) -> str:
    """Render authentication page content."""
    methods = data.get("auth_methods", [])
    tokens = data.get("token_management", {})
    scopes = data.get("scopes_and_permissions", [])
    rules = data.get("security_rules", [])
    errors = data.get("common_errors", [])

    methods_html = ""
    if methods:
        cards = ""
        for m in methods:
            if isinstance(m, dict):
                cards += (
                    f'<div class="mini-card">'
                    f'<h4>{_esc(m.get("method", ""))}</h4>'
                    f'<p>{_esc(m.get("description", ""))}</p>'
                    f'<p style="font-size:0.72rem;color:var(--accent)">Use when: {_esc(m.get("when_to_use", ""))}</p>'
                    f'</div>'
                )
        methods_html = f'<section class="card"><h2>Authentication Methods</h2><div class="card-grid">{cards}</div></section>'

    tokens_html = ""
    if tokens and isinstance(tokens, dict):
        items = ""
        for key in ["how_to_get", "how_to_refresh", "expiration", "storage_recommendations"]:
            val = tokens.get(key, "")
            if val:
                label = key.replace("_", " ").title()
                items += f"<li><strong>{label}:</strong> {_esc(str(val))}</li>"
        if items:
            tokens_html = f'<section class="card"><h2>Token Management</h2><ul style="list-style:none;padding:0">{items}</ul></section>'

    scopes_html = ""
    if scopes:
        rows = ""
        for s in scopes:
            if isinstance(s, dict):
                rows += (
                    f'<tr><td><code>{_esc(s.get("scope", ""))}</code></td>'
                    f'<td>{_esc(s.get("description", ""))}</td>'
                    f'<td>{_esc(s.get("required_for", ""))}</td></tr>'
                )
        if rows:
            scopes_html = f'<section class="card"><h2>Scopes & Permissions</h2><table><thead><tr><th>Scope</th><th>Description</th><th>Required For</th></tr></thead><tbody>{rows}</tbody></table></section>'

    rules_html = ""
    if rules:
        bullets = "".join(f"<li>{_esc(str(r))}</li>" for r in rules)
        rules_html = f'<section class="card"><h2>Security Rules</h2><ul>{bullets}</ul></section>'

    errors_html = _render_error_table(errors, "Common Auth Errors")

    return f"{methods_html}{tokens_html}{scopes_html}{rules_html}{errors_html}"


def _render_concepts_content(data: dict) -> str:
    """Render core concepts page."""
    domain = data.get("domain_model", [])
    abstractions = data.get("key_abstractions", [])
    data_flow = data.get("data_flow", "")
    terminology = data.get("terminology", [])
    mental_model = data.get("mental_model", "")

    domain_html = ""
    if domain:
        cards = ""
        for d in domain:
            if isinstance(d, dict):
                rels = d.get("relationships", "")
                rel_html = f'<p style="font-size:0.72rem;color:var(--light)">Relates to: {_esc(str(rels))}</p>' if rels else ""
                cards += f'<div class="mini-card"><h4>{_esc(d.get("entity", ""))}</h4><p>{_esc(d.get("description", ""))}</p>{rel_html}</div>'
        domain_html = f'<section class="card"><h2>Domain Model</h2><div class="card-grid">{cards}</div></section>'

    abs_html = ""
    if abstractions:
        cards = ""
        for a in abstractions:
            if isinstance(a, dict):
                cards += (
                    f'<div class="mini-card"><h4>{_esc(a.get("name", ""))}</h4>'
                    f'<p>{_esc(a.get("what_it_is", ""))}</p>'
                    f'<p style="font-size:0.72rem;color:var(--accent)">{_esc(a.get("why_it_matters", ""))}</p></div>'
                )
        abs_html = f'<section class="card"><h2>Key Abstractions</h2><div class="card-grid">{cards}</div></section>'

    flow_html = ""
    if data_flow:
        flow_html = f'<section class="card"><h2>Data Flow</h2><p>{_esc(str(data_flow))}</p></section>'

    term_html = ""
    if terminology:
        rows = ""
        for t in terminology:
            if isinstance(t, dict):
                rows += f'<tr><td><strong>{_esc(t.get("term", ""))}</strong></td><td>{_esc(t.get("definition", ""))}</td></tr>'
        if rows:
            term_html = f'<section class="card"><h2>Terminology</h2><table><thead><tr><th>Term</th><th>Definition</th></tr></thead><tbody>{rows}</tbody></table></section>'

    mm_html = ""
    if mental_model:
        mm_html = f'<section class="card"><h2>Mental Model</h2><p style="font-style:italic;color:var(--light)">{_esc(str(mental_model))}</p></section>'

    return f"{domain_html}{abs_html}{flow_html}{term_html}{mm_html}"


def _render_rules_content(data: dict) -> str:
    """Render rules & constraints page."""
    rate_limits = data.get("rate_limits", [])
    quotas = data.get("quotas", [])
    size_limits = data.get("size_limits", [])
    naming = data.get("naming_rules", [])
    ordering = data.get("ordering_rules", [])
    edges = data.get("edge_cases", [])

    rl_html = ""
    if rate_limits:
        rows = ""
        for r in rate_limits:
            if isinstance(r, dict):
                rows += (
                    f'<tr><td>{_esc(r.get("endpoint_or_resource", ""))}</td>'
                    f'<td>{_esc(str(r.get("limit", "")))}</td>'
                    f'<td>{_esc(str(r.get("window", "")))}</td>'
                    f'<td>{_esc(r.get("what_happens_when_exceeded", ""))}</td></tr>'
                )
        if rows:
            rl_html = f'<section class="card"><h2>Rate Limits</h2><table><thead><tr><th>Resource</th><th>Limit</th><th>Window</th><th>When Exceeded</th></tr></thead><tbody>{rows}</tbody></table></section>'

    quotas_html = ""
    if quotas:
        rows = ""
        for q in quotas:
            if isinstance(q, dict):
                rows += f'<tr><td>{_esc(q.get("resource", ""))}</td><td>{_esc(str(q.get("limit", "")))}</td><td>{_esc(q.get("how_to_check", ""))}</td></tr>'
        if rows:
            quotas_html = f'<section class="card"><h2>Quotas</h2><table><thead><tr><th>Resource</th><th>Limit</th><th>How to Check</th></tr></thead><tbody>{rows}</tbody></table></section>'

    size_html = ""
    if size_limits:
        rows = ""
        for s in size_limits:
            if isinstance(s, dict):
                rows += f'<tr><td>{_esc(s.get("what", ""))}</td><td>{_esc(str(s.get("max_size", "")))}</td></tr>'
        if rows:
            size_html = f'<section class="card"><h2>Size Limits</h2><table><thead><tr><th>What</th><th>Max Size</th></tr></thead><tbody>{rows}</tbody></table></section>'

    naming_html = ""
    if naming:
        bullets = "".join(f"<li>{_esc(str(n))}</li>" for n in naming)
        naming_html = f'<section class="card"><h2>Naming Rules</h2><ul>{bullets}</ul></section>'

    ordering_html = ""
    if ordering:
        bullets = "".join(f"<li>{_esc(str(o))}</li>" for o in ordering)
        ordering_html = f'<section class="card"><h2>Ordering Rules</h2><ul>{bullets}</ul></section>'

    edge_html = ""
    if edges:
        rows = ""
        for e in edges:
            if isinstance(e, dict):
                rows += (
                    f'<tr><td>{_esc(e.get("scenario", ""))}</td>'
                    f'<td>{_esc(e.get("behavior", ""))}</td>'
                    f'<td>{_esc(e.get("recommendation", ""))}</td></tr>'
                )
        if rows:
            edge_html = f'<section class="card"><h2>Edge Cases</h2><table><thead><tr><th>Scenario</th><th>Behavior</th><th>Recommendation</th></tr></thead><tbody>{rows}</tbody></table></section>'

    return f"{rl_html}{quotas_html}{size_html}{naming_html}{ordering_html}{edge_html}"


def _render_troubleshooting_content(data: dict) -> str:
    """Render troubleshooting page."""
    errors = data.get("common_errors", [])
    diagnostics = data.get("diagnostic_steps", [])
    health = data.get("health_checks", [])
    known = data.get("known_issues", [])

    errors_html = _render_error_table(errors, "Common Errors")

    diag_html = ""
    if diagnostics:
        cards = ""
        for d in diagnostics:
            if isinstance(d, dict):
                cards += (
                    f'<div class="mini-card">'
                    f'<h4>{_esc(d.get("symptom", ""))}</h4>'
                    f'<p><strong>Check first:</strong> {_esc(d.get("check_first", ""))}</p>'
                    f'<p><strong>Then:</strong> {_esc(d.get("then_check", ""))}</p>'
                    f'</div>'
                )
        diag_html = f'<section class="card"><h2>Diagnostic Steps</h2><div class="card-grid">{cards}</div></section>'

    health_html = ""
    if health:
        rows = ""
        for h in health:
            if isinstance(h, dict):
                rows += (
                    f'<tr><td>{_esc(h.get("what_to_check", ""))}</td>'
                    f'<td><code>{_esc(h.get("how", ""))}</code></td>'
                    f'<td>{_esc(h.get("healthy_response", ""))}</td></tr>'
                )
        if rows:
            health_html = f'<section class="card"><h2>Health Checks</h2><table><thead><tr><th>Check</th><th>How</th><th>Healthy Response</th></tr></thead><tbody>{rows}</tbody></table></section>'

    known_html = ""
    if known:
        rows = ""
        for k in known:
            if isinstance(k, dict):
                rows += (
                    f'<tr><td>{_esc(k.get("issue", ""))}</td>'
                    f'<td>{_esc(k.get("workaround", ""))}</td>'
                    f'<td>{_esc(k.get("status", ""))}</td></tr>'
                )
        if rows:
            known_html = f'<section class="card"><h2>Known Issues</h2><table><thead><tr><th>Issue</th><th>Workaround</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></section>'

    return f"{errors_html}{diag_html}{health_html}{known_html}"


def _render_faq_content(data: dict) -> str:
    """Render FAQ page."""
    questions = data.get("questions", [])
    if not questions:
        return '<p class="empty">No FAQ available.</p>'

    # Group by category
    categories: dict = {}
    for q in questions:
        if isinstance(q, dict):
            cat = q.get("category", "general").title()
            categories.setdefault(cat, []).append(q)

    html = ""
    for cat, items in categories.items():
        inner = ""
        for q in items:
            inner += (
                f'<div style="margin-bottom:1rem">'
                f'<p style="font-weight:700;margin-bottom:0.25rem">{_esc(q.get("question", ""))}</p>'
                f'<p style="color:var(--light)">{_esc(q.get("answer", ""))}</p>'
                f'</div>'
            )
        html += f'<section class="card"><h2>{_esc(cat)}</h2>{inner}</section>'

    return html


def _render_resources_content(data: dict) -> str:
    """Render resources page."""
    sdks = data.get("sdks", [])
    apis = data.get("api_references", [])
    changelog = data.get("changelogs", data.get("changelog", {}))
    community = data.get("community", [])
    status = data.get("status_page", {})
    support = data.get("support", {})

    sdk_html = ""
    if sdks:
        cards = ""
        for s in sdks:
            if isinstance(s, dict):
                install = s.get("install_command", "")
                install_html = f'<pre><code>{_esc(install)}</code></pre>' if install else ""
                url = s.get("url", "")
                link_html = f' <a href="{_esc(url)}" target="_blank">docs</a>' if url else ""
                cards += (
                    f'<div class="mini-card">'
                    f'<h4>{_esc(s.get("language", ""))}{link_html}</h4>'
                    f'<p><code>{_esc(s.get("package_name", ""))}</code></p>'
                    f'{install_html}'
                    f'</div>'
                )
        sdk_html = f'<section class="card"><h2>SDKs & Libraries</h2><div class="card-grid">{cards}</div></section>'

    api_html = ""
    if apis:
        items = ""
        for a in apis:
            if isinstance(a, dict):
                items += f'<li><a href="{_esc(a.get("url", "#"))}" target="_blank">{_esc(a.get("name", ""))}</a> &mdash; {_esc(a.get("description", ""))}</li>'
        if items:
            api_html = f'<section class="card"><h2>API References</h2><ul style="list-style:none;padding:0">{items}</ul></section>'

    misc_html = ""
    misc_items = ""
    if changelog and isinstance(changelog, dict) and changelog.get("url"):
        misc_items += f'<li><a href="{_esc(changelog["url"])}" target="_blank">Changelog</a></li>'
    if status and isinstance(status, dict) and status.get("url"):
        misc_items += f'<li><a href="{_esc(status["url"])}" target="_blank">Status Page</a></li>'
    if community:
        for c in community:
            if isinstance(c, dict):
                misc_items += f'<li><a href="{_esc(c.get("url", "#"))}" target="_blank">{_esc(c.get("platform", "Community"))}</a></li>'
    if support and isinstance(support, dict):
        contact = support.get("how_to_contact", "")
        if contact:
            misc_items += f'<li><strong>Support:</strong> {_esc(contact)}</li>'
    if misc_items:
        misc_html = f'<section class="card"><h2>Links & Community</h2><ul style="list-style:none;padding:0">{misc_items}</ul></section>'

    return f"{sdk_html}{api_html}{misc_html}"


def _render_workflow_content(data: dict) -> str:
    """Render a workflow page."""
    goal = data.get("goal", "")
    prereqs = data.get("prerequisites", [])
    steps = data.get("steps", [])
    verify = data.get("verify", "")
    variations = data.get("common_variations", [])
    errors = data.get("error_handling", [])
    related = data.get("related_workflows", [])

    goal_html = f'<p style="font-size:1rem;color:var(--light);margin-bottom:1rem">{_esc(goal)}</p>' if goal else ""

    prereq_html = ""
    if prereqs:
        bullets = "".join(f"<li>{_esc(str(p))}</li>" for p in prereqs)
        prereq_html = f'<section class="card"><h2>Prerequisites</h2><ul>{bullets}</ul></section>'

    steps_html = ""
    if steps:
        items = ""
        for s in steps:
            if isinstance(s, dict):
                action = s.get("action", "")
                details = s.get("details", "")
                code = s.get("code_snippet", "")
                gotcha = s.get("gotcha", "")
                items += f"<li><strong>{_esc(action)}</strong>"
                if details:
                    items += f"<br><span style='color:var(--light)'>{_esc(details)}</span>"
                if code:
                    items += f"<pre><code>{_esc(code)}</code></pre>"
                if gotcha:
                    items += f"<br><span style='color:var(--amber);font-size:0.78rem'>&#9888; {_esc(gotcha)}</span>"
                items += "</li>"
            else:
                items += f"<li>{_esc(str(s))}</li>"
        steps_html = f'<section class="card"><h2>Steps</h2><ol>{items}</ol></section>'

    verify_html = ""
    if verify:
        verify_html = f'<section class="card"><h2>Verify Success</h2><p>{_esc(str(verify))}</p></section>'

    var_html = ""
    if variations:
        cards = ""
        for v in variations:
            if isinstance(v, dict):
                cards += f'<div class="mini-card"><h4>{_esc(v.get("variation", ""))}</h4><p>{_esc(v.get("how_it_differs", ""))}</p></div>'
        var_html = f'<section class="card"><h2>Variations</h2><div class="card-grid">{cards}</div></section>'

    errors_html = _render_error_table(errors, "Error Handling")

    related_html = ""
    if related:
        bullets = "".join(f"<li>{_esc(str(r))}</li>" for r in related)
        related_html = f'<section class="card"><h2>Related Workflows</h2><ul>{bullets}</ul></section>'

    return f"{goal_html}{prereq_html}{steps_html}{verify_html}{var_html}{errors_html}{related_html}"


def _render_error_table(errors: list, title: str) -> str:
    """Shared helper for error tables."""
    if not errors:
        return ""
    rows = ""
    for e in errors:
        if isinstance(e, dict):
            error_key = e.get("error_code_or_message", e.get("error", ""))
            rows += (
                f'<tr><td><code>{_esc(str(error_key))}</code></td>'
                f'<td>{_esc(e.get("likely_cause", e.get("cause", "")))}</td>'
                f'<td>{_esc(e.get("fix", ""))}</td>'
                f'<td>{_esc(e.get("escalate_if", ""))}</td></tr>'
            )
    if not rows:
        return ""
    return (
        f'<section class="card"><h2>{_esc(title)}</h2>'
        f'<table><thead><tr><th>Error</th><th>Cause</th><th>Fix</th><th>Escalate If</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></section>'
    )


# ---------------------------------------------------------------------------
# Page type dispatcher
# ---------------------------------------------------------------------------

PAGE_RENDERERS = {
    "overview": _render_overview_content,
    "getting-started": _render_getting_started_content,
    "authentication": _render_auth_content,
    "core-concepts": _render_concepts_content,
    "rules": _render_rules_content,
    "troubleshooting": _render_troubleshooting_content,
    "faq": _render_faq_content,
    "resources": _render_resources_content,
}


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_package_page(
    content_json: dict,
    page_type: str,
    page_title: str,
    product_name: str,
    package_slug: str,
    page_map: list,
    current_page_slug: str,
    is_paid: bool = False,
) -> str:
    """Render a full HTML page with sidebar navigation and page content."""
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Special case: agents page uses the existing renderer (embedded in the package chrome)
    if page_type == "agents":
        # Render the agent page content without the full HTML wrapper
        # We'll extract just the body content
        agent_html = render_agent_page_html(
            content_json=content_json,
            product_name=product_name,
            slug=package_slug,
            mode="full",
        )
        # Extract body content from the full HTML
        body_start = agent_html.find('<div class="container">')
        body_end = agent_html.rfind('</div>\n</body>')
        if body_start >= 0 and body_end >= 0:
            page_content = agent_html[body_start:body_end + 6]
        else:
            page_content = agent_html
    else:
        # Determine which renderer to use
        if page_type.startswith("workflow"):
            renderer = _render_workflow_content
        else:
            renderer = PAGE_RENDERERS.get(page_type)

        if renderer:
            page_content = renderer(content_json)
        else:
            page_content = f'<p class="empty">Unknown page type: {_esc(page_type)}</p>'

    # Check if this page should be locked
    page_entry = next((p for p in page_map if p["slug"] == current_page_slug), None)
    is_locked = page_entry and page_entry.get("tier") == "full" and not is_paid

    sidebar = _render_sidebar(product_name, package_slug, page_map, current_page_slug, is_paid)

    if is_locked:
        body_content = (
            f'<div class="page-locked">'
            f'<div class="page-content-inner">'
            f'<h1>{_esc(page_title)}</h1>'
            f'{page_content}'
            f'</div>'
            f'{_render_lock_overlay(package_slug)}'
            f'</div>'
        )
    else:
        body_content = f'<h1>{_esc(page_title)}</h1>\n{page_content}'

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(page_title)} &mdash; {_esc(product_name)} | GrounDocs</title>
<meta name="description" content="{_esc(page_title)} for {_esc(product_name)}. AI-ready documentation by GrounDocs.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{SHARED_CSS}</style>
</head>
<body>
<div class="layout">
  {sidebar}
  <main class="main">
    <div class="page-content">
      {body_content}
      <footer>
        <p>Generated by <a href="https://groundocs.com" target="_blank">GrounDocs</a></p>
        <p style="margin-top:0.2rem;font-size:0.68rem;color:#C0BDB8">{timestamp}</p>
      </footer>
    </div>
  </main>
</div>
</body>
</html>
"""


def render_generating_package_html(product_name: str, slug: str) -> str:
    """Return a generating page with auto-refresh for packages."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="5">
<title>{_esc(product_name)} &mdash; Generating... | GrounDocs</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{
  font-family:'Plus Jakarta Sans',system-ui,sans-serif;
  background:#FAFAF8;color:#1A1A1A;display:flex;align-items:center;justify-content:center;
  min-height:100vh;margin:0;
}}
.card{{
  text-align:center;background:#fff;border:1px solid #E5E5E0;border-radius:10px;
  padding:2.5rem 2rem;max-width:440px;box-shadow:0 4px 24px rgba(0,0,0,0.04);
}}
h1{{font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:1.5rem;margin-bottom:0.5rem}}
p{{color:#6B6B6B;margin-bottom:0.75rem;font-size:0.9rem}}
.spinner{{
  width:32px;height:32px;border:3px solid #E5E5E0;border-top-color:#1A7A4C;
  border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 1rem;
}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.hint{{font-size:0.75rem;color:#C0BDB8}}
</style>
</head>
<body>
<div class="card">
  <div class="spinner"></div>
  <h1>Building your documentation package</h1>
  <p>Crawling <strong>{_esc(product_name)}</strong> docs and generating your AI-ready pages.</p>
  <p class="hint">This page refreshes automatically.</p>
</div>
</body>
</html>
"""
