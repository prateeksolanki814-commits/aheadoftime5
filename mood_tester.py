"""Mood Tester Module.

Embeds the AI Mood Tester (a fun face-scan mood detection demo) as a
self-contained HTML/CSS/JS component inside the app, rendered via
st.components.v1.html().

This is entirely front-end (runs in the visitor's browser): camera
access, the scan animation, mood simulation, meters, mini-dashboard,
and session history all happen client-side, with no server calls.
Note the history resets on page refresh (it is not saved to the
project's database) since it lives only in the embedded component's
browser memory.
"""

MOOD_TESTER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Mood Tester — Smart Face Scan</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<style>
  :root{
    --void:#0b0f1a;
    --panel:#131a2bcc;
    --panel-solid:#131a2b;
    --stroke:#2a3552;
    --scan-cyan:#4fe8d3;
    --text-primary:#eaf0ff;
    --text-muted:#8a93ac;
    --accent: var(--scan-cyan);
    --accent-soft: #4fe8d333;
    --radius-lg:24px;
    --radius-md:16px;
    --radius-sm:10px;
  }
  [data-theme="light"]{
    --void:#eef1fa;
    --panel:#ffffffcc;
    --panel-solid:#ffffff;
    --stroke:#d7deef;
    --text-primary:#141a2b;
    --text-muted:#5c6884;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  html{scroll-behavior:smooth;}
  body{
    font-family:'Inter', sans-serif;
    background:var(--void);
    color:var(--text-primary);
    min-height:100vh;
    overflow-x:hidden;
    transition:background .5s ease, color .5s ease;
    position:relative;
  }
  h1,h2,h3, .display{ font-family:'Space Grotesk', sans-serif; }
  .mono{ font-family:'JetBrains Mono', monospace; }

  /* ---------- Ambient aura background (the signature element) ---------- */
  #auraCanvas{
    position:fixed; inset:0; width:100%; height:100%;
    z-index:0; pointer-events:none;
  }
  .aura-glow{
    position:fixed; top:50%; left:50%;
    width:900px; height:900px;
    transform:translate(-50%,-50%);
    background:radial-gradient(circle, var(--accent-soft) 0%, transparent 70%);
    filter:blur(40px);
    z-index:0; pointer-events:none;
    transition:background 1.2s ease;
    animation:auraPulse 6s ease-in-out infinite;
  }
  @keyframes auraPulse{
    0%,100%{ opacity:.55; transform:translate(-50%,-50%) scale(1); }
    50%{ opacity:.85; transform:translate(-50%,-50%) scale(1.08); }
  }

  .wrap{ position:relative; z-index:1; max-width:1080px; margin:0 auto; padding:0 24px 80px; }

  /* ---------- Nav ---------- */
  nav{
    display:flex; align-items:center; justify-content:space-between;
    padding:22px 0;
  }
  .brand{ display:flex; align-items:center; gap:10px; font-size:19px; font-weight:700; letter-spacing:.3px;}
  .brand .dot{ width:10px; height:10px; border-radius:50%; background:var(--accent); box-shadow:0 0 12px var(--accent); transition:background .6s ease;}
  .nav-actions{ display:flex; gap:10px; }
  .icon-btn{
    width:40px; height:40px; border-radius:12px; border:1px solid var(--stroke);
    background:var(--panel); color:var(--text-primary); cursor:pointer;
    display:flex; align-items:center; justify-content:center; font-size:16px;
    transition:all .2s ease; backdrop-filter:blur(12px);
  }
  .icon-btn:hover{ border-color:var(--accent); transform:translateY(-2px); }

  /* ---------- Hero / Scanner ---------- */
  .hero{ text-align:center; padding:20px 0 10px; }
  .eyebrow{
    display:inline-block; font-family:'JetBrains Mono', monospace; font-size:12px;
    letter-spacing:2px; text-transform:uppercase; color:var(--accent);
    border:1px solid var(--stroke); padding:6px 14px; border-radius:99px;
    margin-bottom:18px; transition:color .6s ease;
  }
  .hero h1{ font-size:clamp(32px,5vw,52px); font-weight:700; line-height:1.05; margin-bottom:12px;}
  .hero p{ color:var(--text-muted); font-size:16px; max-width:480px; margin:0 auto 36px; }

  .scanner-frame{
    position:relative; width:min(360px, 84vw); aspect-ratio:1/1; margin:0 auto;
    border-radius:28px; overflow:hidden; background:#000;
    border:1px solid var(--stroke);
    box-shadow:0 0 0 1px #ffffff08, 0 20px 60px #00000055;
  }
  .scanner-frame video, .scanner-frame .placeholder{
    position:absolute; inset:0; width:100%; height:100%; object-fit:cover;
    transform:scaleX(-1);
  }
  .placeholder{
    display:flex; align-items:center; justify-content:center;
    color:var(--text-muted); font-size:13px; background:#0d1220;
    flex-direction:column; gap:10px; transform:none;
  }
  .placeholder .cam-icon{ font-size:34px; opacity:.6; }

  .corner{ position:absolute; width:34px; height:34px; border-color:var(--accent); transition:border-color .6s ease; opacity:.9;}
  .corner.tl{ top:14px; left:14px; border-top:3px solid; border-left:3px solid; border-radius:8px 0 0 0;}
  .corner.tr{ top:14px; right:14px; border-top:3px solid; border-right:3px solid; border-radius:0 8px 0 0;}
  .corner.bl{ bottom:14px; left:14px; border-bottom:3px solid; border-left:3px solid; border-radius:0 0 0 8px;}
  .corner.br{ bottom:14px; right:14px; border-bottom:3px solid; border-right:3px solid; border-radius:0 0 8px 0;}

  .scanline{
    position:absolute; left:8%; right:8%; height:2px;
    background:linear-gradient(90deg, transparent, var(--accent), transparent);
    box-shadow:0 0 12px var(--accent);
    top:0; opacity:0; transition:background .6s ease;
  }
  .scanline.active{ animation:sweep 1.8s ease-in-out infinite; opacity:1; }
  @keyframes sweep{
    0%{ top:8%; opacity:0; } 10%{ opacity:1;} 90%{ opacity:1;} 100%{ top:92%; opacity:0; }
  }

  .status-pill{
    margin-top:22px; display:inline-flex; align-items:center; gap:8px;
    font-family:'JetBrains Mono', monospace; font-size:12.5px; color:var(--text-muted);
    background:var(--panel); border:1px solid var(--stroke); padding:8px 16px; border-radius:99px;
    backdrop-filter:blur(12px);
  }
  .status-pill .blip{ width:7px; height:7px; border-radius:50%; background:var(--accent); transition:background .6s ease;}
  .status-pill.busy .blip{ animation:blink 1s ease-in-out infinite; }
  @keyframes blink{ 50%{ opacity:.2; } }

  .btn{
    font-family:'Inter', sans-serif; font-weight:600; font-size:15px;
    padding:15px 30px; border-radius:14px; border:none; cursor:pointer;
    background:linear-gradient(135deg, var(--accent), #7c5cff);
    color:#0b0f1a; margin-top:26px; transition:transform .15s ease, box-shadow .3s ease;
    box-shadow:0 10px 30px -8px var(--accent-soft);
  }
  .btn:hover{ transform:translateY(-2px); }
  .btn:active{ transform:translateY(0); }
  .btn.ghost{
    background:transparent; color:var(--text-primary); border:1px solid var(--stroke);
    box-shadow:none;
  }
  .btn-row{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; }
  .btn[disabled]{ opacity:.5; cursor:not-allowed; transform:none; }

  /* ---------- Sections ---------- */
  section{ margin-top:64px; }
  .section-head{ text-align:center; margin-bottom:28px; }
  .section-head .eyebrow{ margin-bottom:10px; }
  .section-head h2{ font-size:clamp(22px,3vw,30px); }

  .card{
    background:var(--panel); border:1px solid var(--stroke); border-radius:var(--radius-lg);
    backdrop-filter:blur(16px); padding:32px;
  }

  /* ---------- Result ---------- */
  #resultSection{ display:none; }
  .result-card{ text-align:center; position:relative; overflow:hidden; }
  .result-emoji{
    font-size:96px; display:inline-block; margin-bottom:6px;
    animation:floaty 3.5s ease-in-out infinite, popIn .6s cubic-bezier(.2,1.4,.4,1);
    filter:drop-shadow(0 0 24px var(--accent-soft));
  }
  @keyframes floaty{ 0%,100%{ transform:translateY(0);} 50%{ transform:translateY(-12px);} }
  @keyframes popIn{ from{ transform:scale(.4); opacity:0;} to{ transform:scale(1); opacity:1;} }
  .result-mood{ font-size:26px; font-weight:700; margin-top:4px; }
  .result-confidence{ font-family:'JetBrains Mono', monospace; color:var(--accent); font-size:15px; margin-top:6px; transition:color .6s ease;}
  .result-explanation{ color:var(--text-muted); max-width:440px; margin:16px auto 0; line-height:1.6; font-size:15px;}
  .result-message{
    margin:22px auto 0; max-width:440px; font-style:italic; font-size:15px;
    border-left:2px solid var(--accent); padding-left:14px; text-align:left; transition:border-color .6s ease;
  }

  .tips-row{ display:flex; gap:10px; flex-wrap:wrap; justify-content:center; margin-top:22px; }
  .tip-chip{
    font-size:13px; padding:8px 14px; border-radius:99px; border:1px solid var(--stroke);
    background:var(--panel); color:var(--text-primary);
  }

  /* ---------- Meters ---------- */
  .meters{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:20px; margin-top:32px; }
  .meter{ text-align:center; }
  .gauge{ position:relative; width:104px; height:104px; margin:0 auto 10px; }
  .gauge svg{ transform:rotate(-90deg); width:100%; height:100%; }
  .gauge circle{ fill:none; stroke-width:8; }
  .gauge .bg{ stroke:var(--stroke); }
  .gauge .fg{ stroke:var(--accent); stroke-linecap:round; transition:stroke-dashoffset 1.4s cubic-bezier(.2,.8,.2,1), stroke .6s ease; }
  .gauge-value{
    position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
    font-family:'JetBrains Mono', monospace; font-weight:700; font-size:18px;
  }
  .meter-label{ font-size:12.5px; color:var(--text-muted); text-transform:uppercase; letter-spacing:1px; }

  .result-actions{ display:flex; gap:10px; justify-content:center; flex-wrap:wrap; margin-top:30px; }
  .result-actions .btn{ margin-top:0; padding:11px 20px; font-size:13.5px; }

  /* ---------- Dashboard ---------- */
  .stat-grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:16px; margin-bottom:26px; }
  .stat-card{
    background:var(--panel); border:1px solid var(--stroke); border-radius:var(--radius-md);
    padding:20px; text-align:center; backdrop-filter:blur(16px);
  }
  .stat-card .num{ font-family:'JetBrains Mono', monospace; font-size:30px; font-weight:700; color:var(--accent); transition:color .6s ease;}
  .stat-card .lbl{ font-size:12px; color:var(--text-muted); text-transform:uppercase; letter-spacing:1px; margin-top:4px;}

  .chart-grid{ display:grid; grid-template-columns:1.1fr 1.4fr; gap:20px; }
  @media(max-width:760px){ .chart-grid{ grid-template-columns:1fr; } }
  .chart-card{ background:var(--panel); border:1px solid var(--stroke); border-radius:var(--radius-md); padding:22px; backdrop-filter:blur(16px);}
  .chart-card h3{ font-size:14px; margin-bottom:14px; color:var(--text-muted); font-weight:600; text-transform:uppercase; letter-spacing:1px;}
  .chart-card canvas{ max-height:220px; }

  /* ---------- History ---------- */
  .history-toolbar{ display:flex; gap:10px; justify-content:flex-end; margin-bottom:14px; flex-wrap:wrap; }
  .history-toolbar .btn{ margin-top:0; padding:9px 16px; font-size:13px; }
  table{ width:100%; border-collapse:collapse; }
  th, td{ text-align:left; padding:12px 10px; font-size:13.5px; border-bottom:1px solid var(--stroke); }
  th{ color:var(--text-muted); font-weight:600; text-transform:uppercase; font-size:11px; letter-spacing:1px; }
  .empty-state{ text-align:center; padding:40px 20px; color:var(--text-muted); font-size:14px; }

  footer{ text-align:center; margin-top:70px; color:var(--text-muted); font-size:12.5px; line-height:1.8; }
  footer .disclaimer{ max-width:480px; margin:0 auto 14px; }

  ::selection{ background:var(--accent); color:#0b0f1a; }

  @media(prefers-reduced-motion: reduce){
    *{ animation:none !important; transition:none !important; }
  }

  /* Toast */
  #toast{
    position:fixed; bottom:28px; left:50%; transform:translateX(-50%) translateY(20px);
    background:var(--panel-solid); border:1px solid var(--stroke); color:var(--text-primary);
    padding:13px 22px; border-radius:12px; font-size:13.5px; opacity:0; pointer-events:none;
    transition:all .3s ease; z-index:50;
  }
  #toast.show{ opacity:1; transform:translateX(-50%) translateY(0); }
</style>
</head>
<body>

<canvas id="auraCanvas"></canvas>
<div class="aura-glow" id="auraGlow"></div>

<div class="wrap">
  <nav>
    <div class="brand"><span class="dot" id="brandDot"></span> AI Mood Tester</div>
    <div class="nav-actions">
      <button class="icon-btn" id="themeToggle" title="Toggle theme">🌙</button>
      <button class="icon-btn" id="fullscreenToggle" title="Fullscreen">⛶</button>
      <button class="icon-btn" id="soundToggle" title="Toggle sound">🔊</button>
    </div>
  </nav>

  <!-- HERO / SCANNER -->
  <section class="hero">
    <span class="eyebrow" id="eyebrowTag">LIVE FACE SCAN · DEMO AI</span>
    <h1>What's your mood<br>right now?</h1>
    <p>Position your face in the frame and let the scanner do its thing. Just for fun — not a real diagnosis.</p>

    <div class="scanner-frame" id="scannerFrame">
      <video id="video" autoplay playsinline muted></video>
      <div class="placeholder" id="placeholder">
        <div class="cam-icon">📷</div>
        <div>Camera preview will appear here</div>
      </div>
      <div class="corner tl"></div><div class="corner tr"></div>
      <div class="corner bl"></div><div class="corner br"></div>
      <div class="scanline" id="scanline"></div>
    </div>

    <div class="status-pill" id="statusPill"><span class="blip"></span><span id="statusText">Idle — tap Start Mood Scan</span></div>

    <div class="btn-row">
      <button class="btn" id="scanBtn">Start Mood Scan</button>
      <button class="btn ghost" id="stopCamBtn" style="display:none;">Turn Off Camera</button>
    </div>
  </section>

  <!-- RESULT -->
  <section id="resultSection">
    <div class="card result-card">
      <div class="result-emoji" id="resultEmoji">😊</div>
      <div class="result-mood" id="resultMood">Happy</div>
      <div class="result-confidence mono" id="resultConfidence">Confidence: 92%</div>
      <div class="result-explanation" id="resultExplanation"></div>
      <div class="result-message" id="resultMessage"></div>

      <div class="tips-row" id="tipsRow"></div>

      <div class="meters" id="metersRow"></div>

      <div class="result-actions">
        <button class="btn ghost" id="scanAgainBtn">↻ Scan Again</button>
        <button class="btn ghost" id="downloadCardBtn">⬇ Download Result Card</button>
        <button class="btn ghost" id="shareBtn">↗ Share Result</button>
      </div>
    </div>
  </section>

  <!-- DASHBOARD -->
  <section id="dashboardSection">
    <div class="section-head">
      <span class="eyebrow">INSIGHTS</span>
      <h2>Your Mood Dashboard</h2>
    </div>

    <div class="stat-grid">
      <div class="stat-card"><div class="num" id="statTotal">0</div><div class="lbl">Total Scans</div></div>
      <div class="stat-card"><div class="num" id="statTopMood">—</div><div class="lbl">Most Common Mood</div></div>
      <div class="stat-card"><div class="num" id="statAvgConf">0%</div><div class="lbl">Avg Confidence</div></div>
      <div class="stat-card"><div class="num" id="statPositivity">0%</div><div class="lbl">Avg Positivity</div></div>
    </div>

    <div class="chart-grid">
      <div class="chart-card"><h3>Mood Distribution</h3><canvas id="pieChart"></canvas></div>
      <div class="chart-card"><h3>Mood Score — Last 7 Scans</h3><canvas id="lineChart"></canvas></div>
    </div>
  </section>

  <!-- HISTORY -->
  <section id="historySection">
    <div class="section-head">
      <span class="eyebrow">LOG</span>
      <h2>Scan History</h2>
    </div>
    <div class="card">
      <div class="history-toolbar">
        <button class="btn ghost" id="exportCsvBtn">⬇ Export CSV</button>
        <button class="btn ghost" id="exportPdfBtn">⬇ Download PDF</button>
        <button class="btn ghost" id="clearHistoryBtn">🗑 Clear History</button>
      </div>
      <div id="historyTableWrap">
        <div class="empty-state">No scans yet — your history will show up here after your first scan.</div>
      </div>
    </div>
  </section>

  <footer>
    <div class="disclaimer">AI Mood Tester is a fun demo built for exhibitions and learning. It does not use real emotion-recognition AI and is not a medical, psychological, or scientific assessment tool.</div>
    <div>Built with HTML, CSS &amp; JavaScript · No data leaves your browser</div>
  </footer>
</div>

<div id="toast"></div>

<script>
/* =========================================================
   AI MOOD TESTER — app logic
   All mood detection below is SIMULATED (weighted random +
   coherent meter math). No real facial emotion AI is used,
   by design — see the project brief.
   ========================================================= */

const MOODS = [
  { key:'happy', emoji:'😊', name:'Happy', color:'#ffc94d',
    explanation:'You appear cheerful, positive, and energetic today. Keep smiling and spread positivity!',
    message:'Your smile can brighten someone\u2019s day.',
    tips:['Keep smiling','Share positivity','Enjoy your day'],
    meters:{happiness:[85,98], energy:[70,90], stress:[5,20], positivity:[85,98]} },
  { key:'sad', emoji:'😢', name:'Sad', color:'#5b9dff',
    explanation:'You seem a little low today \u2014 that\u2019s completely okay, everyone has these moments.',
    message:'Every day is a new beginning. Better moments are ahead.',
    tips:['Listen to music','Talk to a friend','Take a short walk'],
    meters:{happiness:[10,30], energy:[20,40], stress:[50,70], positivity:[15,35]} },
  { key:'loving', emoji:'😍', name:'Loving', color:'#ff6fa5',
    explanation:'You\u2019re radiating warmth and affection right now.',
    message:'Love shared is love multiplied.',
    tips:['Tell someone you appreciate them','Write a kind note','Give a hug'],
    meters:{happiness:[80,95], energy:[60,80], stress:[10,25], positivity:[85,95]} },
  { key:'confident', emoji:'😎', name:'Confident', color:'#4fe8d3',
    explanation:'You look self-assured and ready to take on anything.',
    message:'Believe in yourself \u2014 you are capable of amazing things.',
    tips:['Set a bold goal today','Stand tall','Speak your mind'],
    meters:{happiness:[70,85], energy:[75,90], stress:[15,30], positivity:[80,92]} },
  { key:'sleepy', emoji:'😴', name:'Sleepy', color:'#8a93ac',
    explanation:'Looks like you could use some rest.',
    message:'Rest is productive too \u2014 recharge and come back stronger.',
    tips:['Take a short nap','Drink some water','Stretch a little'],
    meters:{happiness:[40,60], energy:[5,20], stress:[30,45], positivity:[40,60]} },
  { key:'excited', emoji:'🤩', name:'Excited', color:'#ff9f4d',
    explanation:'Your energy is through the roof right now!',
    message:'Ride this wave of excitement into something amazing.',
    tips:['Channel it into a project','Share your excitement','Dance it out'],
    meters:{happiness:[88,98], energy:[90,99], stress:[10,20], positivity:[88,98]} },
  { key:'relaxed', emoji:'😌', name:'Relaxed', color:'#56d9a0',
    explanation:'You look calm, centered, and at ease.',
    message:'Peace of mind is the best accessory you can wear.',
    tips:['Keep breathing deeply','Enjoy the quiet','Savor this calm'],
    meters:{happiness:[65,80], energy:[40,55], stress:[5,15], positivity:[70,85]} },
  { key:'thoughtful', emoji:'🤔', name:'Thoughtful', color:'#9b8cff',
    explanation:'You seem deep in thought about something important.',
    message:'Great ideas often start with a quiet moment of reflection.',
    tips:['Journal your thoughts','Take a walk to think','Talk it out with someone'],
    meters:{happiness:[50,65], energy:[45,60], stress:[25,40], positivity:[55,70]} },
  { key:'angry', emoji:'😠', name:'Angry', color:'#ff5a5a',
    explanation:'You seem a bit frustrated right now.',
    message:'Take a breath \u2014 this feeling will pass, and clarity will follow.',
    tips:['Take 5 deep breaths','Step away for a moment','Write down what\u2019s bothering you'],
    meters:{happiness:[15,30], energy:[60,80], stress:[70,90], positivity:[15,30]} },
  { key:'surprised', emoji:'😨', name:'Surprised', color:'#ffd84d',
    explanation:'Something caught you off guard!',
    message:'Unexpected moments often lead to the best stories.',
    tips:['Take a moment to process','Embrace the unexpected','Share the surprise'],
    meters:{happiness:[55,70], energy:[65,80], stress:[35,50], positivity:[55,70]} },
  { key:'peaceful', emoji:'😇', name:'Peaceful', color:'#7fe0d6',
    explanation:'You radiate calm and contentment.',
    message:'Inner peace is the greatest gift you can give yourself.',
    tips:['Practice gratitude','Meditate for a few minutes','Enjoy the stillness'],
    meters:{happiness:[75,88], energy:[35,50], stress:[5,15], positivity:[80,92]} },
  { key:'celebrating', emoji:'🥳', name:'Celebrating', color:'#ff7ad9',
    explanation:'You\u2019re in full celebration mode!',
    message:'Life\u2019s wins deserve to be celebrated \u2014 enjoy this moment!',
    tips:['Share the joy with others','Treat yourself','Capture the memory'],
    meters:{happiness:[92,99], energy:[85,98], stress:[5,15], positivity:[92,99]} },
  { key:'nervous', emoji:'😅', name:'Nervous', color:'#ffb37a',
    explanation:'You seem a little anxious about something.',
    message:'It\u2019s okay to feel nervous \u2014 it means you care about the outcome.',
    tips:['Take slow deep breaths','Prepare a little more','Talk to someone you trust'],
    meters:{happiness:[35,50], energy:[55,70], stress:[60,80], positivity:[35,50]} },
  { key:'motivated', emoji:'😤', name:'Motivated', color:'#ff6b4a',
    explanation:'You\u2019re locked in and ready to get things done.',
    message:'Motivation got you started \u2014 discipline will keep you going.',
    tips:['Write your top 3 priorities','Start with the hardest task','Celebrate small wins'],
    meters:{happiness:[65,80], energy:[80,95], stress:[30,45], positivity:[70,85]} },
  { key:'friendly', emoji:'🤗', name:'Friendly', color:'#ffcf4d',
    explanation:'You\u2019ve got warm, approachable energy today.',
    message:'A little kindness goes a long way \u2014 spread it around.',
    tips:['Say hello to someone new','Compliment a friend','Offer to help someone'],
    meters:{happiness:[75,88], energy:[60,75], stress:[10,25], positivity:[80,92]} },
];

let history = [];           // in-memory scan history (session only)
let pieChart, lineChart;
let soundOn = true;
let stream = null;

const $ = (id) => document.getElementById(id);

/* ---------- Ambient particle aura ---------- */
const auraCanvas = $('auraCanvas');
const ctx = auraCanvas.getContext('2d');
let particles = [];
function resizeCanvas(){ auraCanvas.width = innerWidth; auraCanvas.height = innerHeight; }
resizeCanvas();
addEventListener('resize', resizeCanvas);
function initParticles(){
  particles = Array.from({length:38}, () => ({
    x: Math.random()*innerWidth, y: Math.random()*innerHeight,
    r: Math.random()*2+0.6, vy: Math.random()*0.35+0.08, drift: Math.random()*0.4-0.2
  }));
}
initParticles();
function currentAccent(){ return getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#4fe8d3'; }
function animateParticles(){
  ctx.clearRect(0,0,auraCanvas.width,auraCanvas.height);
  ctx.fillStyle = currentAccent();
  particles.forEach(p=>{
    p.y -= p.vy; p.x += p.drift;
    if(p.y < -10){ p.y = innerHeight+10; p.x = Math.random()*innerWidth; }
    ctx.globalAlpha = 0.35;
    ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fill();
  });
  requestAnimationFrame(animateParticles);
}
animateParticles();

/* ---------- Theme toggle ---------- */
$('themeToggle').addEventListener('click', ()=>{
  const root = document.documentElement;
  const isLight = root.getAttribute('data-theme') === 'light';
  root.setAttribute('data-theme', isLight ? 'dark' : 'light');
  $('themeToggle').textContent = isLight ? '🌙' : '☀️';
});

/* ---------- Fullscreen ---------- */
$('fullscreenToggle').addEventListener('click', ()=>{
  if(!document.fullscreenElement){ document.documentElement.requestFullscreen().catch(()=>{}); }
  else{ document.exitFullscreen(); }
});

/* ---------- Sound (tiny synthesized beep, no audio files needed) ---------- */
$('soundToggle').addEventListener('click', ()=>{
  soundOn = !soundOn;
  $('soundToggle').textContent = soundOn ? '🔊' : '🔇';
});
function playBeep(freq=440, duration=0.08){
  if(!soundOn) return;
  try{
    const Actx = window.AudioContext || window.webkitAudioContext;
    const actx = new Actx();
    const osc = actx.createOscillator();
    const gain = actx.createGain();
    osc.type = 'sine'; osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.05, actx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, actx.currentTime + duration);
    osc.connect(gain).connect(actx.destination);
    osc.start(); osc.stop(actx.currentTime + duration);
  }catch(e){ /* audio not available -- silently skip */ }
}

/* ---------- Toast ---------- */
function toast(msg){
  const t = $('toast'); t.textContent = msg; t.classList.add('show');
  clearTimeout(toast._id);
  toast._id = setTimeout(()=> t.classList.remove('show'), 2600);
}

/* ---------- Camera ---------- */
async function startCamera(){
  try{
    stream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:'user' }, audio:false });
    $('video').srcObject = stream;
    $('placeholder').style.display = 'none';
    $('stopCamBtn').style.display = 'inline-block';
    return true;
  }catch(err){
    toast('Camera access denied or unavailable \u2014 running scan in demo mode.');
    return false;
  }
}
function stopCamera(){
  if(stream){ stream.getTracks().forEach(t=>t.stop()); stream=null; }
  $('video').srcObject = null;
  $('placeholder').style.display = 'flex';
  $('stopCamBtn').style.display = 'none';
}
$('stopCamBtn').addEventListener('click', stopCamera);

/* ---------- Native face detection (progressive enhancement) ----------
   Uses the browser's built-in Shape Detection API where available.
   Silently skipped (no error) on browsers that don't support it --
   the scan still works fully either way. */
async function tryDetectFace(videoEl){
  if(!('FaceDetector' in window)) return null;
  try{
    const fd = new FaceDetector({ fastMode:true });
    const faces = await fd.detect(videoEl);
    return faces.length > 0;
  }catch(e){ return null; }
}

/* ---------- Scan flow ---------- */
$('scanBtn').addEventListener('click', runScan);
async function runScan(){
  $('scanBtn').disabled = true;
  $('resultSection').style.display = 'none';

  const camOk = stream ? true : await startCamera();
  $('scanline').classList.add('active');
  $('statusPill').classList.add('busy');
  $('statusText').textContent = 'Scanning for a face...';
  playBeep(660,0.06);

  await wait(1400);

  if(camOk){
    const detected = await tryDetectFace($('video'));
    $('statusText').textContent = detected===false ? 'No face found \u2014 analyzing anyway...' : 'Face detected \u2014 analyzing mood...';
  } else {
    $('statusText').textContent = 'Analyzing mood (demo mode)...';
  }
  playBeep(880,0.06);
  await wait(1800);

  $('scanline').classList.remove('active');
  $('statusPill').classList.remove('busy');
  $('statusText').textContent = 'Scan complete ✓';
  playBeep(1040,0.12);

  const result = simulateMood();
  showResult(result);
  logScan(result);
  $('scanBtn').disabled = false;
  $('scanBtn').textContent = 'Scan Again';
  document.getElementById('resultSection').scrollIntoView({behavior:'smooth', block:'start'});
}
function wait(ms){ return new Promise(r=>setTimeout(r,ms)); }

function simulateMood(){
  const mood = MOODS[Math.floor(Math.random()*MOODS.length)];
  const confidence = Math.floor(Math.random()*(98-72+1)+72);
  const meters = {};
  Object.keys(mood.meters).forEach(k=>{
    const [lo,hi] = mood.meters[k];
    meters[k] = Math.floor(Math.random()*(hi-lo+1)+lo);
  });
  return { ...mood, confidence, meters, ts: new Date() };
}

/* ---------- Render result ---------- */
function setAccent(hex){
  document.documentElement.style.setProperty('--accent', hex);
  document.documentElement.style.setProperty('--accent-soft', hex + '33');
}

function showResult(r){
  setAccent(r.color);
  $('resultSection').style.display = 'block';
  $('resultEmoji').textContent = r.emoji;
  $('resultMood').textContent = r.name;
  $('resultConfidence').textContent = 'Confidence: ' + r.confidence + '%';
  $('resultExplanation').textContent = r.explanation;
  $('resultMessage').textContent = '\u201C' + r.message + '\u201D';

  $('tipsRow').innerHTML = r.tips.map(t=>`<span class="tip-chip">${t}</span>`).join('');

  const meterLabels = { happiness:'Happiness', energy:'Energy', stress:'Stress', positivity:'Positivity' };
  $('metersRow').innerHTML = Object.entries(r.meters).map(([key,val])=>{
    const R=42, C=2*Math.PI*R, offset = C - (val/100)*C;
    return `<div class="meter">
      <div class="gauge">
        <svg viewBox="0 0 100 100">
          <circle class="bg" cx="50" cy="50" r="${R}"></circle>
          <circle class="fg" cx="50" cy="50" r="${R}" stroke-dasharray="${C}" stroke-dashoffset="${C}" data-offset="${offset}"></circle>
        </svg>
        <div class="gauge-value">${val}</div>
      </div>
      <div class="meter-label">${meterLabels[key]}</div>
    </div>`;
  }).join('');

  // animate gauges in after paint
  requestAnimationFrame(()=>{
    document.querySelectorAll('.gauge .fg').forEach(el=>{
      el.style.strokeDashoffset = el.dataset.offset;
    });
  });
}

/* ---------- History + Dashboard ---------- */
function logScan(r){
  history.push(r);
  renderHistory();
  renderDashboard();
}

function renderHistory(){
  const wrap = $('historyTableWrap');
  if(history.length === 0){
    wrap.innerHTML = '<div class="empty-state">No scans yet \u2014 your history will show up here after your first scan.</div>';
    return;
  }
  const rows = [...history].reverse().map(r=>`
    <tr>
      <td>${r.ts.toLocaleDateString()}</td>
      <td class="mono">${r.ts.toLocaleTimeString()}</td>
      <td>${r.emoji} ${r.name}</td>
      <td class="mono">${r.confidence}%</td>
    </tr>`).join('');
  wrap.innerHTML = `<table>
    <thead><tr><th>Date</th><th>Time</th><th>Mood</th><th>Confidence</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderDashboard(){
  $('statTotal').textContent = history.length;
  const counts = {};
  history.forEach(r=> counts[r.name] = (counts[r.name]||0)+1 );
  const topMood = Object.entries(counts).sort((a,b)=>b[1]-a[1])[0];
  $('statTopMood').textContent = topMood ? topMood[0] : '\u2014';
  const avgConf = Math.round(history.reduce((s,r)=>s+r.confidence,0)/history.length);
  $('statAvgConf').textContent = avgConf + '%';
  const avgPos = Math.round(history.reduce((s,r)=>s+r.meters.positivity,0)/history.length);
  $('statPositivity').textContent = avgPos + '%';

  const labels = Object.keys(counts);
  const data = Object.values(counts);
  const colors = labels.map(l => MOODS.find(m=>m.name===l)?.color || '#4fe8d3');

  if(pieChart) pieChart.destroy();
  pieChart = new Chart($('pieChart'), {
    type:'doughnut',
    data:{ labels, datasets:[{ data, backgroundColor:colors, borderWidth:0 }] },
    options:{ plugins:{ legend:{ position:'bottom', labels:{ color:getComputedStyle(document.body).color, font:{size:11} } } } }
  });

  const last7 = history.slice(-7);
  if(lineChart) lineChart.destroy();
  lineChart = new Chart($('lineChart'), {
    type:'line',
    data:{
      labels: last7.map((r,i)=> 'Scan ' + (i+1)),
      datasets:[{
        label:'Mood Score', data: last7.map(r=> Math.round((r.meters.happiness + r.meters.positivity + (100-r.meters.stress))/3) ),
        borderColor:'#4fe8d3', backgroundColor:'#4fe8d333', fill:true, tension:.35, pointRadius:4
      }]
    },
    options:{
      scales:{ y:{ min:0, max:100, ticks:{ color:getComputedStyle(document.body).color } }, x:{ ticks:{ color:getComputedStyle(document.body).color } } },
      plugins:{ legend:{ display:false } }
    }
  });
}

/* ---------- History actions ---------- */
$('clearHistoryBtn').addEventListener('click', ()=>{
  if(history.length===0) return;
  history = [];
  renderHistory(); renderDashboard();
  if(pieChart) pieChart.destroy();
  if(lineChart) lineChart.destroy();
  toast('History cleared.');
});

$('exportCsvBtn').addEventListener('click', ()=>{
  if(history.length===0){ toast('No history to export yet.'); return; }
  let csv = 'Date,Time,Mood,Confidence\n';
  history.forEach(r=>{
    csv += `${r.ts.toLocaleDateString()},${r.ts.toLocaleTimeString()},${r.name},${r.confidence}%\n`;
  });
  downloadBlob(csv, 'mood_history.csv', 'text/csv');
  toast('CSV downloaded.');
});

$('exportPdfBtn').addEventListener('click', ()=>{
  if(history.length===0){ toast('No history to export yet.'); return; }
  try{
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    doc.setFontSize(16); doc.text('AI Mood Tester \u2014 Scan History', 14, 18);
    doc.setFontSize(10);
    let y = 30;
    history.forEach((r,i)=>{
      doc.text(`${i+1}. ${r.ts.toLocaleString()} \u2014 ${r.name} (${r.confidence}%)`, 14, y);
      y += 8;
      if(y > 280){ doc.addPage(); y = 20; }
    });
    doc.save('mood_history.pdf');
    toast('PDF downloaded.');
  }catch(e){ toast('PDF export unavailable right now.'); }
});

function downloadBlob(content, filename, type){
  const blob = new Blob([content], {type});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

/* ---------- Result actions ---------- */
$('scanAgainBtn').addEventListener('click', runScan);

$('downloadCardBtn').addEventListener('click', ()=>{
  const el = document.querySelector('.result-card');
  if(!window.html2canvas){ toast('Download unavailable right now.'); return; }
  html2canvas(el, { backgroundColor: getComputedStyle(document.body).backgroundColor, scale:2 }).then(canvas=>{
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = 'mood_result.png';
    a.click();
    toast('Result card downloaded.');
  }).catch(()=> toast('Download unavailable right now.'));
});

$('shareBtn').addEventListener('click', async ()=>{
  const mood = $('resultMood').textContent;
  const conf = $('resultConfidence').textContent;
  const text = `My AI Mood Tester result: ${mood} (${conf}) \u2014 just for fun! 🎭`;
  if(navigator.share){
    try{ await navigator.share({ text }); }catch(e){ /* user cancelled */ }
  } else {
    try{
      await navigator.clipboard.writeText(text);
      toast('Result copied to clipboard!');
    }catch(e){ toast(text); }
  }
});

/* ---------- Init ---------- */
renderDashboard();
</script>
</body>
</html>
"""


def get_mood_tester_html():
    """Returns the full HTML/CSS/JS for the AI Mood Tester component."""
    return MOOD_TESTER_HTML
