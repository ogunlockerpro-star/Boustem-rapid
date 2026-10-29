from flask import Flask, request, redirect, url_for, session, render_template_string, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, secrets, os, math
from functools import wraps
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "meru.db")
app = Flask(__name__)
app.secret_key = os.environ.get("BOUSTEM_SECRET_KEY") or os.environ.get("MERU_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
ADMIN_EMAIL = os.environ.get("BOUSTEM_ADMIN_EMAIL", "admin@localhost")
ADMIN_PASSWORD = os.environ.get("BOUSTEM_ADMIN_PASSWORD", "CHANGE_THIS_ADMIN_PASSWORD")
WITHDRAWAL_FEE = float(os.environ.get("BOUSTEM_WITHDRAWAL_FEE", "0.07"))
USD_HTG_RATE = float(os.environ.get("BOUSTEM_USD_HTG_RATE", "147"))
NATCASH_NUMBER = os.environ.get("BOUSTEM_NATCASH_NUMBER", "43455502")

CSS = """
:root{--bg:#f5f7fb;--surface:#fff;--ink:#14213d;--muted:#68758b;--blue:#3156d9;--blue2:#2444b5;--teal:#10a88a;--line:#e5eaf2;--shadow:0 16px 45px rgba(23,42,86,.08)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink);min-height:100vh}a{text-decoration:none;color:inherit}.container{width:min(1180px,92%);margin:auto}.nav{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}.navin{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{font-size:23px;font-weight:950;letter-spacing:-1px;color:var(--ink);white-space:nowrap}.brand span{color:var(--blue)}.links,.actions{display:flex;align-items:center;gap:12px}.links{color:#586780;font-size:14px;font-weight:700;gap:25px}.links a:hover{color:var(--blue)}.btn{border:0;border-radius:13px;padding:12px 17px;font-weight:800;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px;font-size:14px;transition:transform .18s,box-shadow .18s;background:#fff}.btn:hover{transform:translateY(-1px)}.primary{background:var(--blue);color:#fff;box-shadow:0 8px 20px #3156d925}.primary:hover{background:var(--blue2)}.dark{color:var(--ink);border:1px solid var(--line)}.danger{background:#fff0f1;color:#b42335;border:1px solid #ffd4d9}.hero{padding:70px 0 60px;background:radial-gradient(ellipse at 82% 4%,#dce6ff 0,transparent 36%),radial-gradient(ellipse at 4% 100%,#d9f8ef 0,transparent 30%),linear-gradient(180deg,#fff 0%,#f5f7fb 100%)}.hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:52px;align-items:center}.eyebrow{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;background:#edf1ff;border:1px solid #dce4ff;border-radius:999px;color:var(--blue);font-size:11px;font-weight:900;letter-spacing:1px}.hero h1{font-size:clamp(42px,6vw,72px);line-height:1.01;letter-spacing:-3px;margin:21px 0 18px;color:#14213d}.green{color:var(--blue)}.hero p{color:var(--muted);font-size:17px;line-height:1.8;max-width:580px}.hero-cta{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0 14px}.hero-card{position:relative;overflow:hidden;border-radius:28px;padding:28px;background:linear-gradient(145deg,#233fb2 0%,#3156d9 53%,#168b9c 100%);color:#fff;box-shadow:0 26px 60px #253f9c2e}.hero-card:before,.hero-card:after{content:"";position:absolute;border:1px solid #ffffff25;border-radius:50%;width:260px;height:260px;right:-90px;top:-120px}.hero-card:after{width:340px;height:340px;right:-130px;top:-160px}.hero-card>*{position:relative;z-index:1}.hero-card .muted{color:#dbe4ff}.wallet-head{display:flex;justify-content:space-between;align-items:center;gap:10px}.wallet-label{font-size:13px;font-weight:800;letter-spacing:.5px}.live-pill{font-size:11px;padding:7px 10px;border-radius:999px;background:#ffffff20;border:1px solid #ffffff38}.balance{font-size:39px;font-weight:950;margin:22px 0 6px;letter-spacing:-1px}.wallet-bottom{display:flex;justify-content:space-between;align-items:end;gap:10px;margin-top:28px}.mini-label{font-size:12px;color:#dbe4ff}.payrow{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:22px}.pay{background:#ffffff13;border:1px solid #ffffff28;padding:13px 8px;border-radius:14px;text-align:center;font-weight:800;font-size:12px}.trustline{display:flex;gap:18px;flex-wrap:wrap;color:#61718a;font-size:12px;font-weight:750;margin-top:22px}.section{padding:60px 0}.section h2{font-size:clamp(28px,4vw,40px);letter-spacing:-1.2px;margin:14px 0 10px}.section-lead{color:var(--muted);line-height:1.75;max-width:670px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:17px;margin-top:28px}.card,.panel{background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:23px;box-shadow:var(--shadow)}.service{min-height:188px;transition:.2s;display:flex;flex-direction:column;align-items:flex-start}.service:hover{transform:translateY(-4px);border-color:#c4d0ff;box-shadow:0 20px 40px #173f8312}.icon{font-size:25px;background:#edf1ff;width:54px;height:54px;border-radius:17px;display:grid;place-items:center}.service h3{margin:16px 0 7px;font-size:17px}.service p{color:var(--muted);line-height:1.65;font-size:13px;margin:0 0 16px}.service-link{font-size:13px;font-weight:850;color:var(--blue);margin-top:auto}.badge{font-size:10px;font-weight:850;letter-spacing:.5px;padding:5px 8px;border-radius:999px;background:#fff3d8;color:#865b00;margin-top:10px}.split{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:stretch}.feature-panel{border-radius:25px;padding:30px;background:#fff;border:1px solid var(--line);box-shadow:var(--shadow)}.feature-panel.blue{background:linear-gradient(135deg,#edf2ff,#fff)}.checklist{list-style:none;padding:0;margin:20px 0 0}.checklist li{padding:10px 0;border-bottom:1px solid var(--line);color:#4c5c73;font-size:14px}.checklist li:last-child{border-bottom:0}.notice,.fee{padding:14px 16px;border-radius:13px;background:#eef5ff;border:1px solid #d9e7ff;color:#284d86;margin:15px 0;line-height:1.7}.notice.success{background:#eafaf2;border-color:#c6f0d9;color:#17643d}.notice.danger{background:#fff0f1;border-color:#ffd4d9;color:#a51e30}.page{padding:36px 0 60px}.dash{display:grid;grid-template-columns:235px 1fr;gap:20px}.side{height:max-content;position:sticky;top:95px}.side h3{margin:3px 10px 15px}.side a{display:block;padding:13px 14px;border-radius:12px;color:#52637c;margin:4px 0;font-weight:750;font-size:14px}.side a:hover{background:#edf1ff;color:var(--blue)}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.stat{padding:20px;border-radius:18px;background:#fff;border:1px solid var(--line);box-shadow:0 6px 20px #18385d08}.stat b{display:block;font-size:25px;margin-top:8px;letter-spacing:-.6px}.muted{color:var(--muted)}.form{display:grid;gap:12px;max-width:620px}.input{width:100%;padding:14px 15px;border-radius:12px;border:1px solid #d7e0ed;background:#fff;color:var(--ink);outline:none;font:inherit}.input:focus{border-color:var(--blue);box-shadow:0 0 0 3px #3156d91a}label{font-size:13px;color:#52637c;font-weight:750}.tablewrap{overflow:auto}.table{width:100%;border-collapse:collapse;min-width:620px}.table th,.table td{text-align:left;padding:13px;border-bottom:1px solid var(--line);font-size:13px;vertical-align:top}.table th{color:#5e6e85;background:#f8faff}.footer{border-top:1px solid var(--line);padding:30px 0;color:var(--muted);margin-top:30px;font-size:13px;background:#fff}.footer-grid{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}.footer-links{display:flex;gap:16px;flex-wrap:wrap}.subtle{font-size:12px;color:var(--muted);line-height:1.65}
@media(max-width:850px){.links{display:none}.hero-grid,.dash,.split{grid-template-columns:1fr}.hero-grid{gap:32px}.grid{grid-template-columns:repeat(2,1fr)}.side{position:static;display:grid;grid-template-columns:repeat(2,1fr);gap:4px}.side h3{grid-column:1/-1}.hero{padding-top:48px}}
@media(max-width:560px){.container{width:91%}.grid,.stats{grid-template-columns:1fr}.hero h1{font-size:44px;letter-spacing:-2px}.hero p{font-size:15px}.payrow{grid-template-columns:repeat(2,1fr)}.btn{padding:11px 12px}.navin{min-height:66px}.brand{font-size:19px}.actions{gap:6px}.actions .btn{font-size:12px}.hero-card,.panel,.card,.feature-panel{padding:20px;border-radius:19px}.section{padding:44px 0}.page{padding-top:24px}.side{grid-template-columns:1fr 1fr}.balance{font-size:33px}}
"""
BASE = """<!doctype html><html lang="ht"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#07111f"><title>{{title}}</title><style>{{css|safe}}
.brand-logo{width:30px;height:30px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;background:#0f2941;border:1px solid #2a4c69;margin-right:8px;vertical-align:middle}
.brand-logo svg{width:19px;height:19px;display:block}
.brand-lockup{display:flex;align-items:center;font-weight:950}
.pay.brand-pay{display:flex;align-items:center;gap:9px;justify-content:flex-start}
.pay.brand-pay .brand-logo{margin:0;flex:0 0 30px}
.service .brand-logo{margin-bottom:10px}
</style></head><body><nav class="nav"><div class="container navin"><a class="brand" href="/">Boustem <span>Rapid</span></a><div class="links"><a href="/#services">Sèvis</a><a href="/#payments">Peman</a><a href="/#security">Sekirite</a></div><div class="actions">{% if session.get('user_id') %}<a class="btn dark" href="/dashboard">Dashboard</a><form method="post" action="/logout" style="display:inline"><input type="hidden" name="csrf" value="{{ csrf() }}"><button class="btn primary" type="submit">Dekonekte</button></form>{% else %}<a class="btn dark" href="/login">Konekte</a><a class="btn primary" href="/register">Kreye kont</a>{% endif %}</div></div></nav>{% with messages=get_flashed_messages(with_categories=true) %}{% for cat,msg in messages %}<div class="container"><div class="notice {{cat}}">{{msg}}</div></div>{% endfor %}{% endwith %}{{body|safe}}<footer class="footer"><div class="container footer-grid"><div><a class="brand" href="/">Boustem <span>Rapid</span></a><p class="subtle">Sèvis dijital nan yon sèl espas.<br>© 2026 Boustem Rapid.</p></div><div class="footer-links"><a href="/#services">Sèvis</a><a href="/#payments">Peman</a><a href="/#security">Sekirite</a><a href="/login">Konekte</a></div><div class="subtle">Gen kèk opsyon ki mande entegrasyon founisè<br>anvan yo kapab sèvi ak lajan reyèl.</div></div></footer></body></html>"""

def db():
    c=sqlite3.connect(DB, timeout=10); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def now(): return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
def init_db():
    c=db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,balance_htg REAL NOT NULL DEFAULT 0,balance_meru REAL NOT NULL DEFAULT 0,is_admin INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,kind TEXT NOT NULL,currency TEXT NOT NULL,amount REAL NOT NULL,status TEXT NOT NULL,reference TEXT,note TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS deposits(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,method TEXT NOT NULL,amount REAL NOT NULL,sender_name TEXT,sender_number TEXT,reference TEXT,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL,reviewed_at TEXT);
    CREATE TABLE IF NOT EXISTS withdrawals(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,method TEXT NOT NULL,amount REAL NOT NULL,fee REAL NOT NULL DEFAULT 0,net_amount REAL NOT NULL DEFAULT 0,receiver TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL,reviewed_at TEXT,transaction_id INTEGER);
    CREATE TABLE IF NOT EXISTS card_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,card_type TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL);
    """)
    cols={r["name"] for r in c.execute("PRAGMA table_info(withdrawals)")}
    if "fee" not in cols: c.execute("ALTER TABLE withdrawals ADD COLUMN fee REAL NOT NULL DEFAULT 0")
    if "net_amount" not in cols: c.execute("ALTER TABLE withdrawals ADD COLUMN net_amount REAL NOT NULL DEFAULT 0")
    if "transaction_id" not in cols: c.execute("ALTER TABLE withdrawals ADD COLUMN transaction_id INTEGER")
    if not c.execute("SELECT id FROM users WHERE email=?",(ADMIN_EMAIL,)).fetchone():
        c.execute("INSERT INTO users(name,email,password_hash,is_admin,created_at) VALUES(?,?,?,?,?)",("Boustem Rapid Admin",ADMIN_EMAIL,generate_password_hash(ADMIN_PASSWORD),1,now()))
    c.commit(); c.close()
def csrf():
    if "csrf" not in session: session["csrf"]=secrets.token_urlsafe(24)
    return session["csrf"]
def csrf_ok(): return secrets.compare_digest(request.form.get("csrf",""),session.get("csrf",""))
def current_user():
    uid=session.get("user_id")
    if not uid:return None
    c=db(); u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone(); c.close(); return u
def auth(f):
    @wraps(f)
    def inner(*a,**kw):
        if not session.get("user_id"): return redirect(url_for("login",next=request.path))
        return f(*a,**kw)
    return inner
def admin(f):
    @wraps(f)
    def inner(*a,**kw):
        u=current_user()
        if not u or not u["is_admin"]: abort(403)
        return f(*a,**kw)
    return inner
def page(body,title="Boustem Rapid"): return render_template_string(BASE,body=body,css=CSS,title=title,csrf=csrf)
def side(u):
    items=[("/dashboard","🏠 Dashboard"),("/deposit","💰 Depo"),("/withdraw","💸 Retrè"),("/exchange","🔄 Echanj"),("/cards","💳 Kat dijital"),("/transactions","📜 Tranzaksyon"),("/profile","👤 Pwofil")]
    if u["is_admin"]: items.append(("/admin","⚙️ Admin"))
    return '<aside class="panel side"><h3>Boustem Rapid</h3>'+''.join(f'<a href="{p}">{t}</a>' for p,t in items)+'</aside>'

@app.route("/")
def home():
    if session.get("user_id"): return redirect("/dashboard")
    body="""<main>
<section class="hero"><div class="container hero-grid"><div><span class="eyebrow">✦ PLATFÒM DIJITAL • AYITI</span><h1>Tout sèvis ou.<br><span class="green">Yon sèl espas.</span></h1><p>Boustem Rapid ede w jere demann peman, swiv tranzaksyon epi jwenn sèvis dijital yo nan yon eksperyans senp ki adapte ak telefòn ou.</p><div class="hero-cta"><a class="btn primary" href="/register">Kreye kont gratis <span>↗</span></a><a class="btn dark" href="/login">Mwen deja gen kont</a></div><div class="trustline"><span>✓ Eksperyans mobil</span><span>✓ Estati tranzaksyon</span><span>✓ Sipò itilizatè</span></div></div><div class="hero-card"><div class="wallet-head"><div class="wallet-label">BOUSTEM RAPID · ESPAS KLIYAN</div><span class="live-pill">● Kont dijital</span></div><div class="mini-label" style="margin-top:30px">Yon sèl kote pou òganize sèvis ou yo</div><div class="balance">Tout bagay anba kontwòl.</div><div class="muted">Depo · Retrè · Istwa · Sèvis dijital</div><div class="payrow">
<div class="pay brand-pay"><span class="brand-logo" aria-label="NatCash"><svg viewBox="0 0 24 24"><path fill="#52f0a0" d="M12 2 4 6v12l8 4 8-4V6l-8-4Zm0 4 4 2-4 2-4-2 4-2Zm-5 5 4 2v6l-4-2v-6Zm10 0v6l-4 2v-6l4-2Z"/></svg></span><span>NatCash</span></div>
<div class="pay brand-pay"><span class="brand-logo" aria-label="MonCash"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="#52f0a0" stroke-width="2"/><path fill="#52f0a0" d="M8 12h8v2H8z"/></svg></span><span>MonCash</span></div>
<div class="pay brand-pay"><span class="brand-logo" aria-label="PayPal"><svg viewBox="0 0 24 24"><path fill="#52f0a0" d="M7 4h6c4 0 6 2 5 5-1 3-3 4-7 4H9l-1 7H5L7 4Zm3 3-1 4h3c2 0 3-1 3-2 0-1-1-2-3-2h-2Z"/></svg></span><span>PayPal</span></div>
<div class="pay brand-pay"><span class="brand-logo" aria-label="USDT"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="#52f0a0" stroke-width="2"/><path fill="#52f0a0" d="M7 8h10v2h-4v7h-2v-7H7V8Z"/></svg></span><span>USDT</span></div>
<div class="pay brand-pay"><span class="brand-logo" aria-label="Digital Card"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2" fill="none" stroke="#52f0a0" stroke-width="2"/><path fill="#52f0a0" d="M3 9h18v2H3z"/></svg></span><span>Kat dijital</span></div>
<div class="pay brand-pay"><span class="brand-logo" aria-label="Security"><svg viewBox="0 0 24 24"><path fill="#52f0a0" d="M12 2 20 5v6c0 5-3.3 9-8 11-4.7-2-8-6-8-11V5l8-3Zm0 5-4 1.5V11c0 3.4 1.8 6.1 4 7.5 2.2-1.4 4-4.1 4-7.5V8.5L12 7Z"/></svg></span><span>Sekirite</span></div>
</div></div></div></section>
<section class="section" id="services"><div class="container"><span class="eyebrow">SÈVIS BOustem rapid</span><h2>Chwazi sa ou bezwen.</h2><p class="section-lead">Men opsyon prensipal yo. Sèvis ki poko konekte ak yon founisè ap make klèman kòm “Byento” pou pa konfonn yo ak sèvis ki deja aktif.</p><div class="grid">
<a class="card service" href="/deposit"><div class="icon">📥</div><h3>Depo / Rechaje</h3><p>Soumèt enfòmasyon peman MonCash epi swiv verifikasyon demann ou an.</p><span class="service-link">Kòmanse depo →</span></a>
<a class="card service" href="/withdraw"><div class="icon">📤</div><h3>Retrè</h3><p>Soumèt demann retrè, verifye frè ak montan nèt anvan ou konfime.</p><span class="service-link">Fè demann →</span></a>
<a class="card service" href="/exchange"><div class="icon">🔄</div><h3>Echanj</h3><p>Espas echanj demonstrasyon; pa sèvi ak montan sa yo kòm to mache reyèl.</p><span class="service-link">Gade echanj →</span></a>
<a class="card service" href="/cards"><div class="icon">💳</div><h3>Kat dijital</h3><p>Gade opsyon kat epi soumèt demann. Emisyon mande yon founisè otorize.</p><span class="service-link">Gade kat yo →</span></a>
<a class="card service" href="/transactions"><div class="icon">📜</div><h3>Istwa tranzaksyon</h3><p>Swiv depo, retrè, montan, dat ak estati demann ou yo.</p><span class="service-link">Louvri istwa →</span></a>
<a class="card service" href="/profile"><div class="icon">👤</div><h3>Pwofil kliyan</h3><p>Jere enfòmasyon kont ou epi konsève aksè ou an sekirite.</p><span class="service-link">Pwofil disponib apre koneksyon</span></a>
<div class="card service"><div class="icon">📱</div><h3>Rechaj telefòn & entènèt</h3><p>Opsyon pou achte minit oswa plan entènèt atravè founisè ki sipòte yo.</p><span class="badge">BYENTO · FOUNISÈ NESesè</span></div>
<div class="card service"><div class="icon">🎁</div><h3>KAT KADO</h3><p>Opsyon pou pwodwi dijital ak kat kado, lè entegrasyon founisè a pare.</p><span class="badge">BYENTO · FOUNISÈ NESesè</span></div>
<div class="card service"><div class="icon">↗️</div><h3>Transfè ant itilizatè</h3><p>Transfè ant kont kapab ajoute apre règ balans, sekirite ak kontwòl yo fin prepare.</p><span class="badge">BYENTO · PA AKTIF</span></div>
<div class="card service"><div class="icon">🛟</div><h3>Sipò kliyan</h3><p>Yon seksyon pou kestyon, pwoblèm tranzaksyon ak demann asistans.</p><span class="badge">BYENTO · KONTAK POU AJOUTE</span></div>
<div class="card service"><div class="icon">🔔</div><h3>Notifikasyon</h3><p>Alèt sou chanjman estati depo, retrè ak lòt demann kont ou.</p><span class="badge">BYENTO · KONFIGIRASYON NESesè</span></div>
<div class="card service"><div class="icon">🛡️</div><h3>Sekirite kont</h3><p>Bon pratik koneksyon, verifikasyon demann ak pwoteksyon done kliyan.</p><span class="service-link">Sekirite an premye</span></div>
</div></div></section>
<section class="section" id="payments"><div class="container split"><div class="feature-panel blue"><span class="eyebrow">RECHAJ MERU</span><h2>Peye an goud. Swiv demann ou an.</h2><p class="section-lead">To sèvis ou bay la se 1 USD = 147 HTG. Kliyan an dwe wè total la ak tout frè ki aplikab anvan li peye.</p><ul class="checklist"><li>📲 Metòd peman vize: MonCash</li><li>🧾 Referans tranzaksyon obligatwa</li><li>⏳ Demann rete an atant pandan verifikasyon</li><li>🔒 Pa bay kredi sou yon resi ki poko verifye</li></ul></div><div class="feature-panel"><span class="eyebrow">KONFYANS & TRANSPARANS</span><h2>Klè nan chak etap.</h2><p class="section-lead">Boustem Rapid ta dwe montre frè, limit, estati ak kondisyon anvan kliyan an konfime yon operasyon.</p><ul class="checklist"><li>✓ Montan ak frè vizib anvan konfimasyon</li><li>✓ Istwa ki montre dat ak referans</li><li>✓ Verifikasyon manyèl oswa otomatik anvan kredi</li><li>✓ Sipò pou pwoblèm ak peman ki an reta</li></ul><p class="subtle">Nòt: nan vèsyon sa a, kèk fonksyon se demonstrasyon. MonCash, kat, rechaj telefòn, kat kado ak transfè pa vin aktif otomatikman san entegrasyon founisè.</p></div></div></section>
<section class="section" id="security"><div class="container"><span class="eyebrow">ANVAN LANSE</span><h2>Yon bèl sit dwe mache san danje tou.</h2><p class="section-lead">Pou sèvi ak lajan reyèl, Boustem Rapid bezwen verifikasyon peman serye, aksè admin ki pwoteje, règleman sou frè ak kondisyon sèvis, ansanm ak bon pwoteksyon done. Pa mete kle API oswa modpas sekrè nan kòd piblik la.</p><div class="hero-cta"><a class="btn primary" href="/register">Kreye kont</a><a class="btn dark" href="/login">Konekte</a></div></div></section>
</main>"""
    return page(body,"Boustem Rapid — Wallet dijital")

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        if not csrf_ok(): flash("Sesyon ekspire. Eseye ankò.","danger"); return redirect("/register")
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        if len(name)<2 or "@" not in email or len(pw)<8: flash("Verifye non, imèl ak modpas (8 karaktè minimòm).","danger")
        else:
            c=db()
            try:
                c.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",(name,email,generate_password_hash(pw),now())); c.commit()
                flash("Kont kreye. Konekte kounye a.","success"); return redirect("/login")
            except sqlite3.IntegrityError: flash("Imèl sa deja gen yon kont.","danger")
            finally: c.close()
    body=f"""<div class="page"><div class="container"><div class="panel" style="max-width:520px;margin:auto"><span class="eyebrow">KREYE KONT</span><h2>Kreye kont ou</h2><form method="post" class="form"><input type="hidden" name="csrf" value="{csrf()}"><label>Non konplè</label><input class="input" name="name" required><label>Imèl</label><input class="input" type="email" name="email" required><label>Modpas (8 karaktè minimòm)</label><input class="input" type="password" name="password" minlength="8" required><button class="btn primary">Kreye kont →</button></form><p class="muted">Ou deja gen kont? <a href="/login">Konekte</a></p></div></div></div>"""
    return page(body,"Enskri — Boustem Rapid")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        if not csrf_ok(): flash("Sesyon ekspire. Eseye ankò.","danger"); return redirect("/login")
        email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        c=db(); u=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); c.close()
        if u and check_password_hash(u["password_hash"],pw):
            session.clear(); session["user_id"]=u["id"]; session["csrf"]=secrets.token_urlsafe(24); return redirect("/dashboard")
        flash("Imèl oswa modpas pa kòrèk.","danger")
    body=f"""<div class="page"><div class="container"><div class="panel" style="max-width:520px;margin:auto"><span class="eyebrow">WELCOME BACK</span><h2>Konekte ak Boustem Rapid</h2><form method="post" class="form"><input type="hidden" name="csrf" value="{csrf()}"><label>Imèl</label><input class="input" type="email" name="email" required><label>Modpas</label><input class="input" type="password" name="password" required><button class="btn primary">Konekte →</button></form><div class="notice">Firebase/Google login poko konekte nan vèsyon sa a.</div><p class="muted">Ou poko gen kont? <a href="/register">Enskri</a></p></div></div></div>"""
    return page(body,"Konekte — Boustem Rapid")
@app.post("/logout")
def logout():
    if not csrf_ok():
        flash("Sesyon ekspire. Eseye ankò.", "danger")
        return redirect("/")
    session.clear()
    return redirect("/")

@app.route("/dashboard")
@auth
def dashboard():
    u=current_user(); c=db()
    tx=c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 8",(u["id"],)).fetchall()
    pending=c.execute("SELECT (SELECT COUNT(*) FROM deposits WHERE user_id=? AND status='pending')+(SELECT COUNT(*) FROM withdrawals WHERE user_id=? AND status='pending') n",(u["id"],u["id"])).fetchone()["n"]; c.close()
    rows="".join(f"<tr><td>{x['kind']}</td><td>{x['amount']:,.2f} {x['currency']}</td><td>{x['status']}</td><td>{x['created_at']}</td></tr>" for x in tx) or '<tr><td colspan="4">Pa gen tranzaksyon toujou.</td></tr>'
    body=f"""<div class="page"><div class="container"><div class="dash">{side(u)}<main><h2>Bonjou, {u['name']}</h2><p class="muted">Men rezime aktivite kont ou.</p><div class="stats"><div class="stat"><span class="muted">Balans HTG</span><b>{u['balance_htg']:,.2f}</b></div><div class="stat"><span class="muted">Balans MERU</span><b>{u['balance_meru']:,.2f}</b></div><div class="stat"><span class="muted">Demann pending</span><b>{pending}</b></div></div><div class="actions" style="margin:16px 0;flex-wrap:wrap"><a class="btn primary" href="/deposit">+ Depo</a><a class="btn dark" href="/withdraw">Demann retrè</a><a class="btn dark" href="/exchange">Echanj</a></div><div class="panel"><h3>Dènye tranzaksyon</h3><div class="tablewrap"><table class="table"><tr><th>Kalite</th><th>Montan</th><th>Estati</th><th>Dat</th></tr>{rows}</table></div></div></main></div></div></div>"""
    return page(body,"Dashboard — Boustem Rapid")

@app.route("/deposit",methods=["GET","POST"])
@auth
def deposit():
    u=current_user()
    if request.method=="POST":
        if not csrf_ok(): flash("Sesyon ekspire.","danger"); return redirect("/deposit")
        method=request.form.get("method"); ref=request.form.get("reference","").strip(); name=request.form.get("sender_name","").strip(); num=request.form.get("sender_number","").strip()
        try: amount=float(request.form.get("amount","0"))
        except ValueError: amount=0
        if method not in {"NatCash","MonCash","PayPal","USDT","BSICards"} or not math.isfinite(amount) or amount<=0 or not ref: flash("Ranpli tout enfòmasyon obligatwa ak yon montan valab.","danger")
        else:
            c=db(); c.execute("INSERT INTO deposits(user_id,method,amount,sender_name,sender_number,reference,created_at) VALUES(?,?,?,?,?,?,?)",(u["id"],method,amount,name,num,ref,now())); c.commit(); c.close()
            flash("Demann depo a antre nan verifikasyon. Balans lan poko chanje.","success"); return redirect("/transactions")
    body=f"""<div class="page"><div class="container"><div class="dash">{side(u)}<main class="panel"><h2>Soumèt yon depo</h2><p class="muted">Demann lan rete pending jiskaske peman an verifye.</p><form method="post" class="form"><input type="hidden" name="csrf" value="{csrf()}"><label>Metòd</label><select class="input" name="method" id="method">
<option>NatCash</option><option>MonCash</option><option>PayPal</option><option>USDT</option><option>BSICards</option></select>
<div id="natcash-box" class="notice success"><b>NatCash — peman manyèl</b><br>Voye lajan sou <b>{NATCASH_NUMBER}</b>, epi mete referans tranzaksyon an anba a. Admin ap verifye peman an avan balans lan chanje.</div><label>Montan peman (HTG)</label><input class="input" type="number" min="1" step="0.01" name="amount" required><label>Non moun ki voye a</label><input class="input" name="sender_name"><label>Nimewo / wallet moun ki voye a</label><input class="input" name="sender_number"><label>Referans tranzaksyon</label><input class="input" name="reference" required><button class="btn primary">Soumèt demann</button></form><div class="notice">Admin dwe verifye peman an sou founisè a anvan apwobasyon.</div></main></div></div></div>"""
    return page(body,"Depo — Boustem Rapid")

@app.route("/withdraw",methods=["GET","POST"])
@auth
def withdraw():
    u=current_user()
    if request.method=="POST":
        if not csrf_ok(): flash("Sesyon ekspire.","danger"); return redirect("/withdraw")
        method=request.form.get("method"); receiver=request.form.get("receiver","").strip()
        try: amount=float(request.form.get("amount","0"))
        except ValueError: amount=0
        if method not in {"NatCash","MonCash","PayPal","USDT"} or not receiver or not math.isfinite(amount) or amount<=0:
            flash("Metòd, destinasyon oswa montan an pa valab.","danger")
        else:
            fee=round(amount*WITHDRAWAL_FEE,2); net=round(amount-fee,2); c=db(); c.execute("BEGIN IMMEDIATE")
            bal=c.execute("SELECT balance_htg FROM users WHERE id=?",(u["id"],)).fetchone()
            if not bal or amount>bal["balance_htg"]:
                c.rollback(); c.close(); flash("Balans HTG ou pa sifi.","danger")
            else:
                c.execute("UPDATE users SET balance_htg=balance_htg-? WHERE id=?",(amount,u["id"]))
                cur=c.execute("INSERT INTO withdrawals(user_id,method,amount,fee,net_amount,receiver,created_at) VALUES(?,?,?,?,?,?,?)",(u["id"],method,amount,fee,net,receiver,now()))
                withdrawal_id=cur.lastrowid
                txcur=c.execute("INSERT INTO transactions(user_id,kind,currency,amount,status,note,created_at) VALUES(?,?,?,?,?,?,?)",(u["id"],"Retrè","HTG",amount,"pending",f"Retrè #{withdrawal_id}; frè: {fee:.2f} HTG; nèt: {net:.2f} HTG",now()))
                c.execute("UPDATE withdrawals SET transaction_id=? WHERE id=?",(txcur.lastrowid,withdrawal_id))
                c.commit(); c.close(); flash(f"Demann lan anrejistre. Frè: {fee:.2f} HTG; montan nèt: {net:.2f} HTG. Lajan poko voye.","success"); return redirect("/transactions")
    body=f"""<div class="page"><div class="container"><div class="dash">{side(u)}<main class="panel"><h2>Demann retrè</h2><p class="muted">Balans disponib: <b>{u['balance_htg']:,.2f} HTG</b></p><div class="fee"><b>Frè retrè a se 7%.</b><br>Egzanp: 1,000 HTG retrè = 70 HTG frè; 930 HTG nèt pou resevwa.<br>Frè a soti nan montan total ou mande retire a.</div><form method="post" class="form"><input type="hidden" name="csrf" value="{csrf()}"><label>Metòd retrè</label><select class="input" name="method"><option>NatCash</option><option>MonCash</option><option>PayPal</option><option>USDT</option></select><label>Montan total pou retire (HTG)</label><input id="amount" class="input" type="number" min="1" step="0.01" name="amount" required><div class="fee">Frè 7%: <b id="fee">0.00 HTG</b><br>Montan nèt: <b id="net">0.00 HTG</b></div><label>Nimewo / kont destinasyon</label><input class="input" name="receiver" required><button class="btn primary">Konfime demann retrè</button></form><p class="muted" style="font-size:12px">Kalkil final la fèt sou sèvè a. Soumèt demann pa vle di peman an fèt.</p></main></div></div></div><script>const a=document.getElementById('amount'),f=document.getElementById('fee'),n=document.getElementById('net');function calc(){{let v=Math.max(0,Number(a.value)||0),fee=Math.round(v*.07*100)/100;f.textContent=fee.toFixed(2)+' HTG';n.textContent=(Math.round((v-fee)*100)/100).toFixed(2)+' HTG'}}a.addEventListener('input',calc);calc();</script>"""
    return page(body,"Retrè — Boustem Rapid")

@app.route("/exchange",methods=["GET","POST"])
@auth
def exchange():
    u=current_user()
    if request.method=="POST":
        if not csrf_ok(): flash("Sesyon ekspire.","danger"); return redirect("/exchange")
        direction=request.form.get("direction")
        try: amount=float(request.form.get("amount","0"))
        except ValueError: amount=0
        c=db(); c.execute("BEGIN IMMEDIATE"); bal=c.execute("SELECT * FROM users WHERE id=?",(u["id"],)).fetchone(); ok=False
        if math.isfinite(amount) and direction=="H2M" and 0<amount<=bal["balance_htg"]:
            m=amount/USD_HTG_RATE; c.execute("UPDATE users SET balance_htg=balance_htg-?,balance_meru=balance_meru+? WHERE id=?",(amount,m,u["id"]))
            c.execute("INSERT INTO transactions(user_id,kind,currency,amount,status,note,created_at) VALUES(?,?,?,?,?,?,?)",(u["id"],"Echanj","MERU",m,"completed",f"{amount:.2f} HTG; to demo",now())); ok=True
        elif math.isfinite(amount) and direction=="M2H" and 0<amount<=bal["balance_meru"]:
            h=amount*USD_HTG_RATE; c.execute("UPDATE users SET balance_meru=balance_meru-?,balance_htg=balance_htg+? WHERE id=?",(amount,h,u["id"]))
            c.execute("INSERT INTO transactions(user_id,kind,currency,amount,status,note,created_at) VALUES(?,?,?,?,?,?,?)",(u["id"],"Echanj","HTG",h,"completed",f"{amount:.2f} MERU; to demo",now())); ok=True
        if ok: c.commit(); c.close(); flash("Echanj fini.","success"); return redirect("/dashboard")
        c.rollback(); c.close(); flash("Montan pa valab oswa balans pa sifi.","danger")
    body=f"""<div class="page"><div class="container"><div class="dash">{side(u)}<main class="panel"><h2>Echanj</h2><div class="notice">To sèvis: 1 USD = {USD_HTG_RATE:g} HTG.</div><form method="post" class="form"><input type="hidden" name="csrf" value="{csrf()}"><label>Direksyon</label><select class="input" name="direction"><option value="H2M">HTG → MERU</option><option value="M2H">MERU → HTG</option></select><label>Montan</label><input class="input" type="number" min="0.01" step="0.01" name="amount" required><button class="btn primary">Echanje (demo)</button></form></main></div></div></div>"""
    return page(body,"Echanj — Boustem Rapid")

@app.route("/transactions")
@auth
def transactions():
    u=current_user(); c=db()
    tx=c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall()
    ds=c.execute("SELECT * FROM deposits WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall()
    ws=c.execute("SELECT * FROM withdrawals WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall(); c.close()
    t="".join(f"<tr><td>{x['kind']}</td><td>{x['amount']:,.2f} {x['currency']}</td><td>{x['status']}</td><td>{x['created_at']}</td><td>{x['note'] or ''}</td></tr>" for x in tx) or '<tr><td colspan="5">Pa gen tranzaksyon.</td></tr>'
    d="".join(f"<tr><td>{x['method']}</td><td>{x['amount']:,.2f} HTG</td><td>{x['reference']}</td><td>{x['status']}</td></tr>" for x in ds) or '<tr><td colspan="4">Pa gen depo.</td></tr>'
    w="".join(f"<tr><td>{x['method']}</td><td>{x['amount']:,.2f}</td><td>{x['fee']:,.2f}</td><td>{x['net_amount']:,.2f}</td><td>{x['receiver']}</td><td>{x['status']}</td></tr>" for x in ws) or '<tr><td colspan="6">Pa gen retrè.</td></tr>'
    body=f"""<div class="page"><div class="container"><div class="dash">{side(u)}<main class="panel"><h2>Istwa tranzaksyon</h2><h3>Ledger</h3><div class="tablewrap"><table class="table"><tr><th>Kalite</th><th>Montan</th><th>Estati</th><th>Dat</th><th>Nòt</th></tr>{t}</table></div><h3>Depo</h3><div class="tablewrap"><table class="table"><tr><th>Metòd</th><th>Montan</th><th>Referans</th><th>Estati</th></tr>{d}</table></div><h3>Retrè (frè 7%)</h3><div class="tablewrap"><table class="table"><tr><th>Metòd</th><th>Total</th><th>Frè</th><th>Nèt</th><th>Destinasyon</th><th>Estati</th></tr>{w}</table></div></main></div></div></div>"""
    return page(body,"Tranzaksyon — Boustem Rapid")

@app.route("/cards",methods=["GET","POST"])
@auth
def cards():
    u=current_user()
    if request.method=="POST":
        if not csrf_ok(): flash("Sesyon ekspire.","danger"); return redirect("/cards")
        typ=request.form.get("card_type","Digital USD Mastercard"); c=db()
        c.execute("INSERT INTO card_requests(user_id,card_type,created_at) VALUES(?,?,?)",(u["id"],typ,now())); c.commit(); c.close()
        flash("Demann kat la anrejistre. Sa pa emèt yon kat reyèl.","success"); return redirect("/cards")
    c=db(); rs=c.execute("SELECT * FROM card_requests WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall(); c.close()
    rows="".join(f"<tr><td>{x['card_type']}</td><td>{x['status']}</td><td>{x['created_at']}</td></tr>" for x in rs) or '<tr><td colspan="3">Pa gen demann kat.</td></tr>'
    body=f"""<div class="page"><div class="container"><div class="dash">{side(u)}<main class="panel"><h2>Kat dijital</h2><p class="muted">Demann kat sèlman; emisyon reyèl mande founisè ak verifikasyon.</p><form method="post" class="form"><input type="hidden" name="csrf" value="{csrf()}"><label>Kalite kat</label><select class="input" name="card_type"><option>Digital USD Mastercard</option><option>USD Visa</option><option>EURO Mastercard</option></select><button class="btn primary">Soumèt demann</button></form><h3>Demann mwen yo</h3><div class="tablewrap"><table class="table"><tr><th>Kalite</th><th>Estati</th><th>Dat</th></tr>{rows}</table></div></main></div></div></div>"""
    return page(body,"Kat — Boustem Rapid")

@app.route("/profile",methods=["GET","POST"])
@auth
def profile():
    u=current_user()
    if request.method=="POST":
        if not csrf_ok(): flash("Sesyon ekspire.","danger"); return redirect("/profile")
        name=request.form.get("name","").strip()
        if len(name)>=2:
            c=db(); c.execute("UPDATE users SET name=? WHERE id=?",(name,u["id"])); c.commit(); c.close(); flash("Pwofil mete ajou.","success"); return redirect("/profile")
        flash("Non pa valab.","danger")
    body=f"""<div class="page"><div class="container"><div class="dash">{side(u)}<main class="panel"><h2>Pwofil mwen</h2><form method="post" class="form"><input type="hidden" name="csrf" value="{csrf()}"><label>Non</label><input class="input" name="name" value="{u['name']}" required><label>Imèl</label><input class="input" value="{u['email']}" disabled><button class="btn primary">Sove chanjman</button></form></main></div></div></div>"""
    return page(body,"Pwofil — Boustem Rapid")

@app.route("/admin")
@admin
def admin_page():
    c=db()
    ds=c.execute("SELECT d.*,u.name,u.email FROM deposits d JOIN users u ON u.id=d.user_id WHERE d.status='pending' ORDER BY d.id DESC").fetchall()
    ws=c.execute("SELECT w.*,u.name,u.email FROM withdrawals w JOIN users u ON u.id=w.user_id WHERE w.status='pending' ORDER BY w.id DESC").fetchall()
    us=c.execute("SELECT * FROM users ORDER BY id DESC").fetchall(); c.close()
    dr="".join(f"""<tr><td>{d['name']}<br>{d['email']}</td><td>{d['method']}</td><td>{d['amount']:,.2f}</td><td>{d['reference']}</td><td><form method="post" action="/admin/deposit/{d['id']}/approve"><input type="hidden" name="csrf" value="{csrf()}"><button class="btn primary">Apwouve</button></form><form method="post" action="/admin/deposit/{d['id']}/reject"><input type="hidden" name="csrf" value="{csrf()}"><button class="btn danger">Refize</button></form></td></tr>""" for d in ds) or '<tr><td colspan="5">Pa gen depo pending.</td></tr>'
    wr="".join(f"""<tr><td>{w['name']}<br>{w['email']}</td><td>{w['method']}</td><td>{w['amount']:,.2f}</td><td>Frè: {w['fee']:,.2f}<br>Nèt: {w['net_amount']:,.2f}</td><td>{w['receiver']}</td><td><form method="post" action="/admin/withdrawal/{w['id']}/approve"><input type="hidden" name="csrf" value="{csrf()}"><button class="btn primary">Apwouve</button></form><form method="post" action="/admin/withdrawal/{w['id']}/reject"><input type="hidden" name="csrf" value="{csrf()}"><button class="btn danger">Refize</button></form></td></tr>""" for w in ws) or '<tr><td colspan="6">Pa gen retrè pending.</td></tr>'
    ur="".join(f"<tr><td>{u['id']}</td><td>{u['name']}</td><td>{u['email']}</td><td>{u['balance_htg']:,.2f}</td><td>{u['balance_meru']:,.2f}</td></tr>" for u in us)
    body=f"""<div class="page"><div class="container"><div class="dash">{side(current_user())}<main class="panel"><h2>Admin Console</h2><div class="notice">Verifye peman an ak founisè a anvan apwobasyon. Apwouve retrè lokalman pa voye lajan otomatikman.</div><h3>Depo pending</h3><div class="tablewrap"><table class="table"><tr><th>Itilizatè</th><th>Metòd</th><th>Montan</th><th>Referans</th><th>Aksyon</th></tr>{dr}</table></div><h3>Retrè pending</h3><div class="tablewrap"><table class="table"><tr><th>Itilizatè</th><th>Metòd</th><th>Total</th><th>Frè / nèt</th><th>Destinasyon</th><th>Aksyon</th></tr>{wr}</table></div><h3>Itilizatè yo</h3><div class="tablewrap"><table class="table"><tr><th>ID</th><th>Non</th><th>Imèl</th><th>HTG</th><th>MERU</th></tr>{ur}</table></div></main></div></div></div>"""
    return page(body,"Admin — Boustem Rapid")

@app.post("/admin/deposit/<int:did>/<action>")
@admin
def review_deposit(did,action):
    if action not in {"approve","reject"}: abort(404)
    if not csrf_ok(): flash("CSRF error.","danger"); return redirect("/admin")
    c=db(); c.execute("BEGIN IMMEDIATE"); d=c.execute("SELECT * FROM deposits WHERE id=?",(did,)).fetchone()
    if not d or d["status"]!="pending": c.rollback(); c.close(); flash("Demann deja trete.","danger"); return redirect("/admin")
    if action=="approve":
        c.execute("UPDATE deposits SET status='approved',reviewed_at=? WHERE id=? AND status='pending'",(now(),did))
        c.execute("UPDATE users SET balance_htg=balance_htg+? WHERE id=?",(d["amount"],d["user_id"]))
        c.execute("INSERT INTO transactions(user_id,kind,currency,amount,status,reference,note,created_at) VALUES(?,?,?,?,?,?,?,?)",(d["user_id"],"Depo","HTG",d["amount"],"completed",d["reference"],d["method"],now()))
        flash("Depo apwouve lokalman. Verifye peman an premye.","success")
    else:
        c.execute("UPDATE deposits SET status='rejected',reviewed_at=? WHERE id=? AND status='pending'",(now(),did)); flash("Depo refize.","success")
    c.commit(); c.close(); return redirect("/admin")

@app.post("/admin/withdrawal/<int:wid>/<action>")
@admin
def review_withdrawal(wid,action):
    if action not in {"approve","reject"}: abort(404)
    if not csrf_ok(): flash("CSRF error.","danger"); return redirect("/admin")
    c=db(); c.execute("BEGIN IMMEDIATE"); w=c.execute("SELECT * FROM withdrawals WHERE id=?",(wid,)).fetchone()
    if not w or w["status"]!="pending": c.rollback(); c.close(); flash("Demann deja trete.","danger"); return redirect("/admin")
    if action=="approve":
        c.execute("UPDATE withdrawals SET status='approved',reviewed_at=? WHERE id=? AND status='pending'",(now(),wid))
        if w["transaction_id"]:
            c.execute("UPDATE transactions SET status='completed' WHERE id=? AND user_id=? AND kind='Retrè' AND status='pending'",(w["transaction_id"],w["user_id"]))
        flash("Retrè make apwouve lokalman; voye montan nèt la manyèlman epi verifye payout la.","success")
    else:
        c.execute("UPDATE withdrawals SET status='rejected',reviewed_at=? WHERE id=? AND status='pending'",(now(),wid))
        c.execute("UPDATE users SET balance_htg=balance_htg+? WHERE id=?",(w["amount"],w["user_id"]))
        if w["transaction_id"]:
            c.execute("UPDATE transactions SET status='rejected' WHERE id=? AND user_id=? AND kind='Retrè' AND status='pending'",(w["transaction_id"],w["user_id"]))
        flash("Retrè refize; montan rezève a retounen nan balans lan.","success")
    c.commit(); c.close(); return redirect("/admin")

@app.errorhandler(403)
def forbidden(_):
    return page('<div class="page"><div class="container panel"><h2>Aksè refize</h2><a class="btn primary" href="/dashboard">Retounen</a></div></div>',"Aksè refize"),403

if __name__=="__main__":
    if not os.environ.get("BOUSTEM_SECRET_KEY") and not os.environ.get("MERU_SECRET_KEY"):
        print("WARNING: set BOUSTEM_SECRET_KEY to a persistent random secret before deployment.")
    if ADMIN_PASSWORD == "CHANGE_THIS_ADMIN_PASSWORD":
        print("WARNING: set BOUSTEM_ADMIN_PASSWORD before deployment; change the default admin password.")
    init_db()
    print("Boustem Rapid server starting on port 5000")
    app.run(host="0.0.0.0",port=5000,debug=False)
