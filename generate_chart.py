"""
NBA Wins Above .500 Chart Generator
====================================
1. Go to https://www.basketball-reference.com/leagues/NBA_2026_standings_by_date_eastern_conference.html
2. Press Ctrl+S, save as "bbref_east.html" in this folder
3. Run: python generate_chart.py
4. Open index.html in your browser

For West: save western conference page as bbref_west.html and re-run.
"""

from bs4 import BeautifulSoup, Comment
import json, re, os, sys
from datetime import datetime

def parse_bbref(filename):
    if not os.path.exists(filename):
        return []
    print(f"  Parsing {filename}...")
    with open(filename, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "standings_by_date"})
    if not table:
        comments = soup.find_all(string=lambda t: isinstance(t, Comment))
        for c in comments:
            if "standings_by_date" in str(c):
                inner = BeautifulSoup(str(c), "html.parser")
                table = inner.find("table", {"id": "standings_by_date"})
                if table:
                    break
    if not table:
        print(f"  WARNING: Could not find standings table in {filename}")
        return []

    tbody = table.find("tbody")
    teams = {}
    for row in tbody.find_all("tr"):
        if "thead" in row.get("class", []):
            continue
        date_th = row.find("th", {"data-stat": "date"})
        if not date_th:
            continue
        date_str = date_th.text.strip()
        if not date_str:
            continue
        for td in row.find_all("td"):
            small = td.find("small")
            if not small:
                continue
            record_text = small.text.strip("()")
            classes = td.get("class", [])
            abbr = None
            for c in classes:
                if c not in ("left","right","center","iz") and 2 <= len(c) <= 3 and c.isupper():
                    abbr = c
                    break
            if not abbr:
                txt = td.text.strip()
                m = re.match(r'\s*([A-Z]{2,3})\s', txt)
                if m:
                    abbr = m.group(1)
            if not abbr:
                continue
            try:
                w, l = record_text.split("-")
                wa500 = int(w) - int(l)
                if abbr not in teams:
                    teams[abbr] = {"abbr": abbr, "dates": [], "wa500": []}
                teams[abbr]["dates"].append(date_str)
                teams[abbr]["wa500"].append(wa500)
            except:
                continue
    result = [v for v in teams.values() if len(v["dates"]) > 0]
    print(f"  Found {len(result)} teams, {len(result[0]['dates']) if result else 0} dates")
    return result

def generate_html(east_teams, west_teams, generated_at):
    all_teams = []
    for t in east_teams:
        all_teams.append({**t, "conf": "east"})
    for t in west_teams:
        all_teams.append({**t, "conf": "west"})

    team_colors = {
        # East
        "BOS":"#007a33","NYK":"#006bb6","PHI":"#0076b6","BRK":"#555",
        "TOR":"#ce1141","MIA":"#98002e","ORL":"#0077c0","ATL":"#e03a3e",
        "CLE":"#860038","DET":"#c8102e","MIL":"#00471b","CHI":"#ce1141",
        "CHO":"#1d1160","IND":"#002d62","WAS":"#002b5c",
        # West
        "OKC":"#007ac1","SAS":"#c4ced4","LAL":"#552583","DEN":"#0e2240",
        "MIN":"#236192","HOU":"#ce1141","GSW":"#1d428a","PHX":"#1d1160",
        "LAC":"#c8102e","POR":"#e03a3e","UTA":"#002b5c","MEM":"#5d76a9",
        "DAL":"#00538c","NOP":"#0c2340","SAC":"#5a2d81",
    }

    data_json = json.dumps(all_teams)
    colors_json = json.dumps(team_colors)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NBA Wins Above .500 — {generated_at}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #fff; color: #222; padding: 24px; }}
  h1 {{ font-size: 20px; font-weight: 500; margin-bottom: 4px; }}
  .subtitle {{ font-size: 13px; color: #888; margin-bottom: 16px; }}
  .controls {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }}
  button {{ font-size: 12px; padding: 5px 12px; border-radius: 6px; border: 1px solid #ddd; background: #fff; color: #333; cursor: pointer; }}
  button.active {{ background: #222; color: #fff; border-color: #222; }}
  .chart-wrap {{ display: flex; gap: 20px; align-items: flex-start; }}
  .canvas-wrap {{ position: relative; flex: 1; height: 500px; }}
  #legend {{ width: 140px; font-size: 11px; padding-top: 4px; max-height: 500px; overflow-y: auto; }}
  .leg-row {{ display: flex; align-items: center; gap: 5px; padding: 2px 0; cursor: pointer; white-space: nowrap; }}
  .leg-row:hover {{ opacity: 0.8; }}
  .leg-swatch {{ width: 14px; height: 2.5px; border-radius: 2px; flex-shrink: 0; }}
  .leg-val {{ min-width: 30px; text-align: right; font-variant-numeric: tabular-nums; color: #666; }}
  .leg-name {{ color: #222; }}
  #tooltip {{ display:none; position:absolute; pointer-events:none; background:#fff; border:1px solid #ddd; border-radius:6px; padding:7px 10px; font-size:12px; min-width:120px; z-index:10; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .generated {{ font-size: 11px; color: #aaa; margin-top: 12px; }}
</style>
</head>
<body>
<h1>NBA wins above .500</h1>
<p class="subtitle">Source: Basketball Reference &nbsp;·&nbsp; Generated {generated_at} &nbsp;·&nbsp; Click legend to highlight</p>

<div class="controls">
  <button id="btn-all" class="active" onclick="filterConf('all')">All teams</button>
  <button id="btn-east" onclick="filterConf('east')">East</button>
  <button id="btn-west" onclick="filterConf('west')">West</button>
</div>

<div class="chart-wrap">
  <div class="canvas-wrap">
    <canvas id="chart"></canvas>
    <div id="tooltip"></div>
  </div>
  <div id="legend"></div>
</div>

<script>
const RAW = {data_json};
const COLORS = {colors_json};

// Build global date spine from all teams
const dateSet = new Set();
RAW.forEach(t => t.dates.forEach(d => dateSet.add(d)));
const allDates = Array.from(dateSet).sort((a,b) => new Date(a) - new Date(b));
const dateIndex = {{}};
allDates.forEach((d,i) => dateIndex[d] = i);

function buildDatasets(teams) {{
  return teams.map(t => {{
    const color = COLORS[t.abbr] || '#888';
    const data = t.dates.map((d,i) => ({{ x: dateIndex[d], y: t.wa500[i] }}));
    return {{
      label: t.abbr,
      data,
      conf: t.conf,
      borderColor: color,
      backgroundColor: color,
      borderWidth: 1.8,
      pointRadius: 0,
      tension: 0.2,
      parsing: false,
    }};
  }});
}}

// Month label positions (approximate game indices)
function getMonthTicks() {{
  const months = {{}};
  allDates.forEach((d,i) => {{
    const month = new Date(d).toLocaleString('default', {{ month: 'short' }});
    if (!months[month]) months[month] = i;
  }});
  return months;
}}
const monthTicks = getMonthTicks();

let chart = null;
let currentConf = 'all';
let currentHighlight = null;

function buildChart(conf) {{
  const filtered = conf === 'all' ? RAW : RAW.filter(t => t.conf === conf);
  const datasets = buildDatasets(filtered);
  if (chart) chart.destroy();
  const ctx = document.getElementById('chart').getContext('2d');
  chart = new Chart(ctx, {{
    type: 'line',
    data: {{ datasets }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      animation: {{ duration: 200 }},
      plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: false }} }},
      interaction: {{ mode: 'nearest', axis: 'x', intersect: false }},
      scales: {{
        x: {{
          type: 'linear',
          min: 0,
          max: allDates.length - 1,
          ticks: {{
            color: '#999',
            font: {{ size: 11 }},
            callback: (val) => {{
              for (const [m, idx] of Object.entries(monthTicks)) {{
                if (val === idx) return m;
              }}
              return '';
            }},
            maxRotation: 0,
            autoSkip: false,
          }},
          grid: {{ color: 'rgba(0,0,0,0.06)' }},
        }},
        y: {{
          ticks: {{ color: '#999', font: {{ size: 11 }} }},
          grid: {{ color: 'rgba(0,0,0,0.06)' }},
          title: {{ display: true, text: 'W − L', color: '#999', font: {{ size: 11 }} }},
        }}
      }},
      onHover: () => {{}}
    }}
  }});
  buildLegend(filtered, currentHighlight);
}}

function setHighlight(abbr) {{
  currentHighlight = abbr;
  if (!chart) return;
  chart.data.datasets.forEach(ds => {{
    if (abbr === null) {{
      ds.borderWidth = 1.8;
      ds.borderColor = COLORS[ds.label] || '#888';
    }} else if (ds.label === abbr) {{
      ds.borderWidth = 3.5;
      ds.borderColor = COLORS[ds.label] || '#888';
    }} else {{
      ds.borderWidth = 1;
      ds.borderColor = 'rgba(130,130,130,0.55)';
    }}
  }});
  chart.update('none');
  const filtered = currentConf === 'all' ? RAW : RAW.filter(t => t.conf === currentConf);
  buildLegend(filtered, abbr);
}}

function buildLegend(teams, highlighted) {{
  const sorted = [...teams].sort((a,b) => b.wa500[b.wa500.length-1] - a.wa500[a.wa500.length-1]);
  document.getElementById('legend').innerHTML = sorted.map(t => {{
    const val = t.wa500[t.wa500.length - 1];
    const color = COLORS[t.abbr] || '#888';
    const isHl = highlighted === t.abbr;
    const fade = highlighted && !isHl ? 'opacity:0.3;' : '';
    return `<div class="leg-row" style="${{fade}}" onclick="toggle('${{t.abbr}}')">
      <span class="leg-swatch" style="background:${{color}};height:${{isHl ? '3px' : '2px'}};"></span>
      <span class="leg-val">${{val >= 0 ? '+' : ''}}${{val}}</span>
      <span class="leg-name" style="font-weight:${{isHl ? 600 : 400}}">${{t.abbr}}</span>
    </div>`;
  }}).join('');
}}

function toggle(abbr) {{
  currentHighlight = currentHighlight === abbr ? null : abbr;
  setHighlight(currentHighlight);
}}

function filterConf(conf) {{
  currentConf = conf;
  currentHighlight = null;
  ['all','east','west'].forEach(c => {{
    document.getElementById('btn-' + c).className = c === conf ? 'active' : '';
  }});
  buildChart(conf);
}}

buildChart('all');

// Tooltip via direct mouse tracking — much more reliable than onHover
const canvas = document.getElementById('chart');
const tip = document.getElementById('tooltip');

canvas.addEventListener('mousemove', (e) => {{
  if (!chart) return;
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  const xAxis = chart.scales.x;
  const yAxis = chart.scales.y;
  const xVal = xAxis.getValueForPixel(mouseX);

  let bestDs = null, bestPtIdx = null, bestDist = Infinity;

  chart.data.datasets.forEach((ds) => {{
    // Find closest x index
    let lo = 0, hi = ds.data.length - 1, idx = 0;
    while (lo <= hi) {{
      const mid = (lo + hi) >> 1;
      if (ds.data[mid].x < xVal) {{ lo = mid + 1; idx = mid; }}
      else {{ hi = mid - 1; }}
    }}
    // Check idx and idx+1
    [idx, idx+1].forEach(i => {{
      if (i < 0 || i >= ds.data.length) return;
      const px = xAxis.getPixelForValue(ds.data[i].x);
      const py = yAxis.getPixelForValue(ds.data[i].y);
      const dist = Math.hypot(px - mouseX, py - mouseY);
      if (dist < bestDist) {{ bestDist = dist; bestDs = ds; bestPtIdx = i; }}
    }});
  }});

  if (!bestDs || bestDist > 20) {{
    tip.style.display = 'none';
    return;
  }}

  const val = bestDs.data[bestPtIdx].y;
  const team = RAW.find(t => t.abbr === bestDs.label);
  const dateStr = team ? (team.dates[bestPtIdx] || '') : '';
  const px = xAxis.getPixelForValue(bestDs.data[bestPtIdx].x);
  const py = yAxis.getPixelForValue(val);

  tip.style.display = 'block';
  tip.style.left = (px + 14) + 'px';
  tip.style.top = (py - 12) + 'px';
  tip.innerHTML = `<span style="font-weight:600;color:${{bestDs.borderColor}}">${{bestDs.label}}</span><br>
    <span style="color:#999;font-size:11px;">${{dateStr}}</span><br>
    <span style="font-size:14px;">${{val >= 0 ? '+' : ''}}${{val}}</span>`;
}});

canvas.addEventListener('mouseleave', () => {{
  tip.style.display = 'none';
}});
</script>
</body>
</html>"""
    return html

# ── Main ──────────────────────────────────────────────────────────────────────
print("NBA Wins Above .500 — Chart Generator")
print("=" * 40)

east_teams = parse_bbref("bbref_east.html")
west_teams = parse_bbref("bbref_west.html")

if not east_teams and not west_teams:
    print("\nERROR: No data found.")
    print("Save the BBRef pages as bbref_east.html and/or bbref_west.html")
    print("then run this script again.")
    sys.exit(1)

generated_at = datetime.now().strftime("%b %d, %Y")
html = generate_html(east_teams, west_teams, generated_at)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

total = len(east_teams) + len(west_teams)
print(f"\nDone! {total} teams written to index.html")
print("Open index.html in your browser to view the chart.")
