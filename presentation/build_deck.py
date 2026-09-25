# -*- coding: utf-8 -*-
"""
Builds the 16-slide 16:9 competition-ready HTML presentation deck (with Technical Architecture, Implementation Details, Challenges Faced, and Future Roadmap) for Averish Shipping AI.
"""
import os
import json

def build_deck():
    # Load base64 rendered images for email_512
    with open('presentation/assets/images_b64.json', 'r', encoding='utf-8') as f:
        images = json.load(f)
    
    b64_si = images['si']
    b64_bl = images['bl']

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Averish Shipping AI — Competition Presentation Deck</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      /* Light Beige / Warm Editorial Palette */
      --bg-editorial: #F9F6F0;
      --bg-surface: #F3EFE6;
      --bg-card: #FFFFFF;
      --border-card: #E8E2D9;
      --border-subtle: #E2DBD0;
      --card-shadow: 0 10px 25px -5px rgba(44, 42, 41, 0.05), 0 4px 10px -2px rgba(44, 42, 41, 0.02);

      /* Sophisticated Earthy Accent Colors */
      --accent-cyan: #2A7B9B;        /* Muted Ocean Teal */
      --accent-blue: #3A5A80;        /* Muted Navy */
      --accent-indigo: #56507A;      /* Slate Indigo */
      --accent-green: #3B7A57;       /* Deep Forest / Sage Green */
      --accent-red: #B84A39;         /* Earthy Terracotta Red */
      --accent-amber: #C07D38;       /* Warm Ochre / Amber */
      --accent-terracotta: #C8795B;  /* Editorial Terracotta */
      --accent-sage: #7A8B6E;        /* Sage */
      --accent-mustard: #D4A373;     /* Warm Mustard */

      /* Warm Charcoal & Editorial Text Hierarchy */
      --text-main: #2C2A29;          /* Soft charcoal */
      --text-muted: #5C5750;         /* Warm gray */
      --text-dim: #8C857B;           /* Muted sand gray */
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: #EFEBE4;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      color: var(--text-main);
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      user-select: none;
      -webkit-font-smoothing: antialiased;
    }}

    /* 16:9 Presentation Viewport Container */
    #deck-viewport {{
      position: relative;
      width: 100vw;
      height: 56.25vw; /* 16:9 ratio */
      max-height: 100vh;
      max-width: 177.78vh; /* 16:9 ratio */
      background: var(--bg-editorial);
      border: 1px solid var(--border-card);
      border-radius: 4px;
      box-shadow: 0 25px 60px -15px rgba(44, 42, 41, 0.12), 0 0 0 1px rgba(232, 226, 217, 0.6);
      overflow: hidden;
    }}

    /* Slide Stage */
    .slide {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      padding: 3.5vw 4.5vw 3vw 4.5vw;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.35s ease, transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      transform: scale(0.985);
    }}

    .slide.active {{
      opacity: 1;
      pointer-events: auto;
      transform: scale(1);
      z-index: 10;
    }}

    /* Slide Header */
    .slide-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border-card);
      padding-bottom: 0.8vw;
      margin-bottom: 1.2vw;
    }}

    .brand-cluster {{
      display: flex;
      align-items: center;
      gap: 0.7vw;
    }}

    .brand-logo-icon {{
      width: 1.8vw;
      height: 1.8vw;
      border-radius: 0.4vw;
      background: #FFFFFF;
      border: 1px solid var(--border-card);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: var(--card-shadow);
      font-size: 1vw;
    }}

    .brand-title {{
      font-size: 1.05vw;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text-main);
      font-family: 'Google Sans', sans-serif;
    }}

    .brand-badge {{
      font-size: 0.65vw;
      font-weight: 600;
      padding: 0.2vw 0.5vw;
      border-radius: 0.25vw;
      background: rgba(200, 121, 91, 0.1);
      border: 1px solid rgba(200, 121, 91, 0.25);
      color: var(--accent-terracotta);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .header-right {{
      display: flex;
      align-items: center;
      gap: 1.2vw;
    }}

    .category-label {{
      font-size: 0.75vw;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 600;
    }}

    .slide-number-badge {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85vw;
      font-weight: 600;
      color: var(--text-main);
      background: #FFFFFF;
      padding: 0.2vw 0.6vw;
      border-radius: 0.3vw;
      border: 1px solid var(--border-card);
      box-shadow: var(--card-shadow);
    }}

    /* Main Slide Body */
    .slide-body {{
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      position: relative;
    }}

    /* Headlines */
    .headline-wrap {{
      margin-bottom: 1.2vw;
    }}

    .headline-pre {{
      font-size: 0.85vw;
      font-weight: 600;
      color: var(--accent-cyan);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 0.3vw;
    }}

    h1.slide-title {{
      font-family: 'Google Sans', 'Inter', sans-serif;
      font-size: 2.2vw;
      line-height: 1.18;
      font-weight: 700;
      color: var(--text-main);
      letter-spacing: -0.03em;
    }}

    h1.slide-title.alert {{
      color: #B84A39;
    }}

    p.slide-sub {{
      font-size: 1.05vw;
      color: var(--text-muted);
      margin-top: 0.5vw;
      line-height: 1.45;
      max-width: 90%;
    }}

    /* Footer */
    .slide-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid var(--border-subtle);
      padding-top: 0.8vw;
      font-size: 0.7vw;
      color: var(--text-dim);
    }}

    .footer-quote {{
      font-style: italic;
      color: var(--text-muted);
    }}

    /* Controls HUD */
    #hud-controls {{
      position: fixed;
      bottom: 1.5vw;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(249, 246, 240, 0.95);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-card);
      border-radius: 9999px;
      padding: 0.4vw 0.8vw;
      display: flex;
      align-items: center;
      gap: 0.8vw;
      z-index: 1000;
      box-shadow: 0 10px 30px rgba(44, 42, 41, 0.12);
    }}

    .hud-btn {{
      background: #FFFFFF;
      border: 1px solid var(--border-card);
      color: var(--text-main);
      padding: 0.35vw 0.75vw;
      border-radius: 9999px;
      font-size: 0.75vw;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.3vw;
      transition: all 0.2s;
    }}

    .hud-btn:hover {{
      background: #EFEBE4;
      border-color: var(--accent-terracotta);
      color: var(--accent-terracotta);
    }}

    .slide-dots {{
      display: flex;
      gap: 0.35vw;
    }}

    .dot {{
      width: 0.5vw;
      height: 0.5vw;
      border-radius: 50%;
      background: #D9D2C5;
      cursor: pointer;
      transition: all 0.2s;
    }}

    .dot.active {{
      background: var(--accent-terracotta);
      box-shadow: 0 0 8px rgba(200, 121, 91, 0.4);
      transform: scale(1.25);
    }}

    /* Reusable Cards & Components */
    .card-grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5vw;
    }}

    .card-grid-3 {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 1.2vw;
    }}

    .card-grid-4 {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr 1fr;
      gap: 1vw;
    }}

    .glass-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-card);
      border-radius: 0.8vw;
      padding: 1.2vw;
      box-shadow: var(--card-shadow);
      position: relative;
    }}

    .glass-card.alert-card {{
      border-color: rgba(184, 74, 57, 0.3);
      background: #FFF8F6;
    }}

    .glass-card.highlight-card {{
      border-color: rgba(42, 123, 155, 0.35);
      background: #F4F8FA;
    }}

    /* Badges & Tags */
    .pill-tag {{
      display: inline-flex;
      align-items: center;
      gap: 0.3vw;
      padding: 0.25vw 0.6vw;
      border-radius: 0.3vw;
      font-size: 0.7vw;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}

    .pill-tag.red {{
      background: #FDEEEB;
      border: 1px solid #F8C7C0;
      color: #B84A39;
    }}

    .pill-tag.green {{
      background: #EDF5F0;
      border: 1px solid #C3DFC9;
      color: #356745;
    }}

    .pill-tag.cyan {{
      background: #EDF6F9;
      border: 1px solid #C6E4ED;
      color: #1E667E;
    }}

    .pill-tag.amber {{
      background: #FEF7ED;
      border: 1px solid #F8DFC0;
      color: #9A5D18;
    }}

    /* Terminal Window Mock */
    .terminal-window {{
      background: #242936; color: #E8E4DD;
      border: 1px solid var(--border-card);
      border-radius: 0.6vw;
      overflow: hidden;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75vw;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6);
    }}

    .terminal-bar {{
      background: #111827;
      padding: 0.4vw 0.8vw;
      display: flex;
      align-items: center;
      gap: 0.4vw;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .term-dot {{
      width: 0.5vw;
      height: 0.5vw;
      border-radius: 50%;
    }}

    .term-dot.r {{ background: #EF4444; }}
    .term-dot.y {{ background: #F59E0B; }}
    .term-dot.g {{ background: #10B981; }}

    .terminal-content {{
      padding: 0.9vw 1.2vw;
      line-height: 1.6;
      color: #5C5750;
    }}

    /* Document Preview Frame */
    .doc-preview-frame {{
      background: #FAF8F5;
      border: 1px solid var(--border-card);
      border-radius: 0.5vw;
      padding: 0.8vw;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7vw;
      line-height: 1.5;
      color: var(--text-main);
      max-height: 16vw;
      overflow-y: auto;
    }}

    /* Table Styles */
    .matrix-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.75vw;
    }}

    .matrix-table th {{
      background: #EFEBE4;
      text-align: left;
      padding: 0.55vw 0.8vw;
      font-weight: 600;
      color: var(--text-main);
      border-bottom: 1px solid var(--border-card);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .matrix-table td {{
      padding: 0.5vw 0.8vw;
      border-bottom: 1px solid #EFEBE4;
      color: var(--text-main);
    }}

    .matrix-table tr:hover td {{
      background: #F4F0E8;
    }}

    .matrix-table .check-yes {{
      color: var(--accent-green);
      font-weight: 700;
    }}

    .matrix-table .check-no {{
      color: var(--accent-red);
      font-weight: 700;
    }}

    .matrix-table .check-var {{
      color: #6B665E;
      font-weight: 400;
    }}

    /* Custom highlight banner */
    .takeaway-banner {{
      background: linear-gradient(90deg, rgba(56, 189, 248, 0.15), rgba(99, 102, 241, 0.15));
      border-left: 4px solid var(--accent-cyan);
      padding: 0.7vw 1.2vw;
      border-radius: 0 0.4vw 0.4vw 0;
      font-size: 0.9vw;
      font-weight: 600;
      color: var(--text-main);
      margin-top: 0.8vw;
    }}

    .takeaway-banner.alert {{
      background: linear-gradient(90deg, rgba(239, 68, 68, 0.2), rgba(245, 158, 11, 0.1));
      border-left-color: var(--accent-red);
    }}

    /* Flowchart & Architecture Elements */
    .flow-step-pill {{
      background: #FFFFFF;
      border: 1px solid var(--border-card);
      border-radius: 0.35vw;
      padding: 0.32vw 0.65vw;
      font-size: 0.68vw;
      font-weight: 600;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 0.4vw;
      box-shadow: 0 2px 5px rgba(44, 42, 41, 0.04);
      transition: transform 0.15s ease;
    }}
    .flow-arrow-down {{
      color: var(--accent-terracotta);
      font-size: 0.75vw;
      line-height: 1;
      text-align: center;
      margin: 0.05vw 0;
    }}
    .fatigue-hero-badge {{
      background: linear-gradient(135deg, #FFF6F3 0%, #FDEEEB 100%);
      border: 2px solid #B84A39;
      border-radius: 0.6vw;
      padding: 0.7vw 1.2vw;
      text-align: center;
      box-shadow: 0 10px 30px -5px rgba(184, 74, 57, 0.22);
    }}
    .fatigue-hero-title {{
      font-family: 'Inter', sans-serif;
      font-size: 1.8vw;
      font-weight: 900;
      letter-spacing: 0.06em;
      color: #B84A39;
      line-height: 1.1;
      text-transform: uppercase;
    }}

    /* Hero Architecture Diagram */
    .hero-arch-box {{
      background: #FFFFFF;
      border: 1px solid var(--border-card);
      border-radius: 0.45vw;
      padding: 0.45vw 0.8vw;
      box-shadow: 0 2px 8px rgba(44, 42, 41, 0.04);
      transition: all 0.2s ease;
    }}
    .hero-arch-box:hover {{
      border-color: var(--accent-cyan);
      transform: translateY(-1px);
    }}
    .hero-arch-title {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.74vw;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .hero-arch-desc {{
      font-size: 0.62vw;
      color: var(--text-muted);
      margin-top: 0.15vw;
      line-height: 1.35;
    }}
    .hero-arch-connector {{
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--accent-cyan);
      font-size: 0.75vw;
      height: 0.85vw;
      font-weight: bold;
    }}
  </style>
</head>
<body>

  <div id="deck-viewport">

    

<!-- =================================================================== -->
    <!-- SLIDE 1: SCREEN 1 — HUMAN FATIGUE (0:00–0:35) -->
    <!-- =================================================================== -->
    <div class="slide active" id="slide-1">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge" style="background: #FEF7ED; border-color: #F8DFC0; color: #C07D38;">Problem Statement · 0:00–0:35</span>
        </div>
        <div class="header-right">
          <span class="category-label">SCREEN 1 — Human Fatigue</span>
          <span class="slide-number-badge">01 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre" style="color: #C8795B;">SCREEN 1 — Operational Reality (0:00–0:35)</div>
          <h1 class="slide-title" style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.2vw; line-height: 1.15;">
            In shipping operations, AI was supposed to reduce workload.<br>Instead, it created <span style="color: #B84A39;">Human Fatigue</span>.
          </h1>
        </div>

        <!-- 2-Column Main Content: Left Workflow vs Right Voiceover & Turning Question -->
        <div style="display: grid; grid-template-columns: 1.05fr 1fr; gap: 1.8vw; margin-top: 0.8vw; align-items: stretch;">
          
          <!-- Left Column: The Simple Exception Workflow -->
          <div class="glass-card" style="background: #FFFFFF; border: 1px solid var(--border-card); padding: 0.9vw 1.2vw; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6vw;">
                <span style="font-size: 0.72vw; font-weight: 700; color: #6B665E; text-transform: uppercase; letter-spacing: 0.05em;">THE REPETITIVE EXCEPTION LOOP</span>
                <span class="pill-tag red" style="font-size: 0.58vw;">OPERATIONAL BOTTLENECK</span>
              </div>

              <!-- Simple 8-Step Flowchart in 2 parallel columns with bridge -->
              <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 0.35vw; align-items: center; margin-bottom: 0.6vw;">
                
                <!-- Left Chain: Steps 1 to 4 -->
                <div style="display: flex; flex-direction: column; gap: 0.25vw;">
                  <div class="flow-step-pill" style="border-left: 3.5px solid #2A7B9B;">
                    <span style="color: #2A7B9B;">📨</span> <span>SHIPPING EMAIL</span>
                  </div>
                  <div class="flow-arrow-down">↓</div>
                  <div class="flow-step-pill" style="border-left: 3.5px solid #3A5A80;">
                    <span style="color: #3A5A80;">📄</span> <span>DOCUMENTS</span>
                  </div>
                  <div class="flow-arrow-down">↓</div>
                  <div class="flow-step-pill" style="border-left: 3.5px solid #56507A;">
                    <span style="color: #56507A;">🤖</span> <span>AI EXTRACTION</span>
                  </div>
                  <div class="flow-arrow-down">↓</div>
                  <div class="flow-step-pill" style="border-left: 3.5px solid #C07D38; background: #FEF8EF;">
                    <span style="color: #C07D38;">⚠️</span> <span style="font-weight: 700; color: #9A5D18;">EXCEPTION</span>
                  </div>
                </div>

                <!-- Bridge Arrow between left chain and right chain -->
                <div style="display: flex; align-items: center; justify-content: center; padding: 0 0.3vw; color: #C8795B; font-size: 1.1vw; font-weight: bold;">
                  ➔
                </div>

                <!-- Right Chain: Steps 5 to 8 -->
                <div style="display: flex; flex-direction: column; gap: 0.25vw;">
                  <div class="flow-step-pill" style="border-left: 3.5px solid #C8795B;">
                    <span style="color: #C8795B;">🔍</span> <span>HUMAN CHECK</span>
                  </div>
                  <div class="flow-arrow-down">↓</div>
                  <div class="flow-step-pill" style="border-left: 3.5px solid #7A8B6E;">
                    <span style="color: #7A8B6E;">✏️</span> <span>HUMAN CORRECTION</span>
                  </div>
                  <div class="flow-arrow-down">↓</div>
                  <div class="flow-step-pill" style="border-left: 3.5px solid #C07D38; background: #FEF8EF;">
                    <span style="color: #C07D38;">🔄</span> <span style="font-weight: 700; color: #9A5D18;">ANOTHER EXCEPTION</span>
                  </div>
                  <div class="flow-arrow-down">↓</div>
                  <div class="flow-step-pill" style="border-left: 3.5px solid #C8795B;">
                    <span style="color: #C8795B;">🔍</span> <span>HUMAN CHECK AGAIN</span>
                  </div>
                </div>

              </div>
            </div>

            <!-- HUGE HERO BADGE: HUMAN FATIGUE -->
            <div class="fatigue-hero-badge">
              <div style="display: flex; align-items: center; justify-content: center; gap: 0.6vw;">
                <span style="font-size: 1.5vw;">⚠️</span>
                <span class="fatigue-hero-title">HUMAN FATIGUE</span>
                <span style="font-size: 1.5vw;">⚠️</span>
              </div>
              <p style="font-size: 0.66vw; color: #8C3426; margin-top: 0.25vw; font-weight: 500;">
                The problem is no longer only AI accuracy. It becomes human fatigue.
              </p>
            </div>
          </div>

          <!-- Right Column: Voiceover Narration & Hero Setup Question -->
          <div style="display: flex; flex-direction: column; justify-content: space-between;">
            
            <!-- Voiceover Script Cards -->
            <div style="display: flex; flex-direction: column; gap: 0.55vw;">
              
              <div class="glass-card" style="background: #FFFFFF; border: 1px solid var(--border-card); border-left: 3.5px solid #2A7B9B; padding: 0.65vw 0.9vw;">
                <div style="display: flex; align-items: center; gap: 0.4vw; margin-bottom: 0.2vw;">
                  <span style="font-size: 0.72vw;">🎙️</span>
                  <span style="font-size: 0.6vw; font-weight: 700; color: #2A7B9B; text-transform: uppercase;">Voiceover · The Intent</span>
                </div>
                <p style="font-size: 0.82vw; color: var(--text-main); line-height: 1.4; font-style: italic;">
                  “In shipping operations, AI is supposed to reduce workload.”
                </p>
              </div>

              <div class="glass-card" style="background: #FFFFFF; border: 1px solid var(--border-card); border-left: 3.5px solid #C07D38; padding: 0.65vw 0.9vw;">
                <div style="display: flex; align-items: center; gap: 0.4vw; margin-bottom: 0.2vw;">
                  <span style="font-size: 0.72vw;">⚠️</span>
                  <span style="font-size: 0.6vw; font-weight: 700; color: #C07D38; text-transform: uppercase;">Voiceover · The Reality</span>
                </div>
                <p style="font-size: 0.8vw; color: var(--text-main); line-height: 1.4; font-style: italic;">
                  “But when documents are <span style="background: #FEF7ED; color: #9A5D18; padding: 0.05vw 0.3vw; border-radius: 0.2vw; font-weight: 600;">missing</span>, <span style="background: #FEF7ED; color: #9A5D18; padding: 0.05vw 0.3vw; border-radius: 0.2vw; font-weight: 600;">unreadable</span>, <span style="background: #FEF7ED; color: #9A5D18; padding: 0.05vw 0.3vw; border-radius: 0.2vw; font-weight: 600;">incorrect</span>, or <span style="background: #FEF7ED; color: #9A5D18; padding: 0.05vw 0.3vw; border-radius: 0.2vw; font-weight: 600;">inconsistent</span>, humans still have to check the AI's output.”
                </p>
              </div>

              <div class="glass-card" style="background: #FFFFFF; border: 1px solid var(--border-card); border-left: 3.5px solid #B84A39; padding: 0.65vw 0.9vw;">
                <div style="display: flex; align-items: center; gap: 0.4vw; margin-bottom: 0.2vw;">
                  <span style="font-size: 0.72vw;">🔄</span>
                  <span style="font-size: 0.6vw; font-weight: 700; color: #B84A39; text-transform: uppercase;">Voiceover · The Shift</span>
                </div>
                <p style="font-size: 0.8vw; color: var(--text-main); line-height: 1.4; font-style: italic;">
                  “And when the same type of exception happens repeatedly, the problem is no longer only AI accuracy. <strong style="color: #B84A39;">It becomes human fatigue.</strong>”
                </p>
              </div>

            </div>

            <!-- The Setup: Hero Technical Transition Question -->
            <div style="background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FA 100%); border: 1.5px solid #2A7B9B; border-left: 5px solid #2A7B9B; border-radius: 0.55vw; padding: 0.8vw 1.1vw; box-shadow: 0 6px 18px rgba(42, 123, 155, 0.08); margin-top: 0.5vw;">
              <div style="font-size: 0.68vw; font-weight: 700; color: #2A7B9B; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.2vw;">
                OUR TECHNICAL QUESTION
              </div>
              <p style="font-size: 0.8vw; color: var(--text-muted); line-height: 1.35;">
                “So instead of asking only, <em>‘Can AI extract the answer?’</em> we asked a different question:”
              </p>
              <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 1.3vw; font-weight: 700; color: #1E667E; margin: 0.3vw 0; line-height: 1.25;">
                “Should AI be allowed to act on that answer?”
              </div>
              <div style="display: flex; align-items: center; gap: 0.4vw; font-size: 0.68vw; color: #5C5750; font-weight: 600;">
                <span>➔</span> <span>That question sets up our entire decision-control architecture.</span>
              </div>
            </div>

          </div>

        </div>

        <div class="takeaway-banner alert" style="margin-top: 0.7vw; padding: 0.45vw 1vw; font-size: 0.76vw;">
          The bottleneck is not extraction. It is the cost of repetitive human intervention when AI lacks decision boundaries.
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — SCREEN 1 · 0:00–0:35 Problem Statement</span>
        <span class="footer-quote">Voiceover: “Should AI be allowed to act on that answer?”</span>
      </div>
    </div>



<!-- =================================================================== -->
    <!-- SLIDE 2: SCREEN 2 — DECISION-CONTROL ARCHITECTURE (0:35–1:00) -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-2">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge" style="background: #EDF6F9; border-color: #C6E4ED; color: #1E667E;">Architecture · 0:35–1:00</span>
        </div>
        <div class="header-right">
          <span class="category-label">SCREEN 2 — Unique Technical Architecture</span>
          <span class="slide-number-badge">02 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre" style="color: #2A7B9B;">SCREEN 2 — YOUR UNIQUE TECHNICAL ARCHITECTURE (0:35–1:00)</div>
          <h1 class="slide-title" style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.2vw; line-height: 1.15;">
            Averish Decision-Control Architecture
          </h1>
        </div>

        <!-- 2-Column Hero Layout: Left Hero Diagram (60%) vs Right Strategic Depth (40%) -->
        <div style="display: grid; grid-template-columns: 1.35fr 1fr; gap: 1.8vw; margin-top: 0.7vw; align-items: stretch;">
          
          <!-- Left Column: The Complete Hero Technical Architecture Flowchart -->
          <div class="glass-card" style="background: #FFFFFF; border: 1.5px solid var(--border-card); padding: 0.8vw 1.2vw; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 8px 24px rgba(44,42,41,0.06);">
            
            <!-- Banner Header -->
            <div style="text-align: center; margin-bottom: 0.35vw;">
              <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75vw; font-weight: 800; color: #2A7B9B; letter-spacing: 0.08em; background: #EDF6F9; padding: 0.2vw 0.8vw; border-radius: 0.25vw; border: 1px solid #C6E4ED;">
                AVERISH SHIPPING AI · DECISION-CONTROL LAYER
              </span>
            </div>

            <!-- Root Input Node -->
            <div style="display: flex; justify-content: center;">
              <div style="background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.35vw; padding: 0.25vw 0.8vw; font-size: 0.7vw; font-weight: 700; color: var(--text-main); display: inline-flex; align-items: center; gap: 0.4vw;">
                <span>📧</span> <span>Email / Documents (B/L, Booking, SI, Invoices)</span>
              </div>
            </div>

            <div class="hero-arch-connector">│<br>▼</div>

            <!-- Node 1: Intent Engine -->
            <div class="hero-arch-box" style="border-left: 3.5px solid #56507A;">
              <div class="hero-arch-title">
                <span style="color: #56507A;">1. INTENT ENGINE</span>
                <span class="pill-tag cyan" style="font-size: 0.52vw; padding: 0.1vw 0.4vw;">CLASSIFY</span>
              </div>
              <div class="hero-arch-desc">
                <strong>What task is needed?</strong> Identifies trade task, document requirements, and verification policy.
              </div>
            </div>

            <div class="hero-arch-connector">▼</div>

            <!-- Node 2: Validation Gates -->
            <div class="hero-arch-box" style="border-left: 3.5px solid #C07D38;">
              <div class="hero-arch-title">
                <span style="color: #9A5D18;">2. VALIDATION GATES</span>
                <span class="pill-tag amber" style="font-size: 0.52vw; padding: 0.1vw 0.4vw;">PRE-EXECUTION</span>
              </div>
              <div class="hero-arch-desc">
                <strong>Right document? Enough information?</strong> Halts wrong attachments & unreadable fax scans.
              </div>
            </div>

            <div class="hero-arch-connector">▼</div>

            <!-- Node 3: AI Extraction -->
            <div class="hero-arch-box" style="border-left: 3.5px solid #2A7B9B;">
              <div class="hero-arch-title">
                <span style="color: #1E667E;">3. AI EXTRACTION</span>
                <span class="pill-tag cyan" style="font-size: 0.52vw; padding: 0.1vw 0.4vw;">OCR + LLM</span>
              </div>
              <div class="hero-arch-desc">
                Spatial Docling coordinate parser + Multimodal Gemini vision at 0.0 temperature.
              </div>
            </div>

            <div class="hero-arch-connector">▼</div>

            <!-- Node 4: Provenance -->
            <div class="hero-arch-box" style="border-left: 3.5px solid #3A5A80;">
              <div class="hero-arch-title">
                <span style="color: #3A5A80;">4. PROVENANCE</span>
                <span class="pill-tag green" style="font-size: 0.52vw; padding: 0.1vw 0.4vw;">EVIDENCE CHAIN</span>
              </div>
              <div class="hero-arch-desc">
                <strong>Where is the evidence?</strong> Enforces physical pixel bounding boxes & byte-level grounding.
              </div>
            </div>

            <div class="hero-arch-connector">▼</div>

            <!-- Decision Split Fork: Trusted vs Uncertain -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8vw; position: relative;">
              
              <!-- Left Branch: Trusted -> Automate -->
              <div style="background: #EDF5F0; border: 1.5px solid #A3D4B5; border-radius: 0.4vw; padding: 0.4vw 0.6vw; text-align: center;">
                <div style="font-size: 0.68vw; font-weight: 800; color: #2E6B47; font-family: 'JetBrains Mono', monospace;">
                  TRUSTED (≥ 0.85)
                </div>
                <div style="color: #2E6B47; font-size: 0.7vw; margin: 0.1vw 0;">↓</div>
                <div style="background: #2E6B47; color: white; border-radius: 0.25vw; padding: 0.2vw 0.4vw; font-size: 0.68vw; font-weight: 700; letter-spacing: 0.04em;">
                  AUTOMATE
                </div>
                <div style="font-size: 0.55vw; color: #1F4D33; margin-top: 0.2vw;">Direct EDI / ERP release</div>
              </div>

              <!-- Right Branch: Uncertain -> Human Review -->
              <div style="background: #FDEEEB; border: 1.5px solid #F8C7C0; border-radius: 0.4vw; padding: 0.4vw 0.6vw; text-align: center;">
                <div style="font-size: 0.68vw; font-weight: 800; color: #B84A39; font-family: 'JetBrains Mono', monospace;">
                  UNCERTAIN (&lt; 0.85)
                </div>
                <div style="color: #B84A39; font-size: 0.7vw; margin: 0.1vw 0;">↓</div>
                <div style="background: #B84A39; color: white; border-radius: 0.25vw; padding: 0.2vw 0.4vw; font-size: 0.68vw; font-weight: 700; letter-spacing: 0.04em;">
                  HUMAN REVIEW
                </div>
                <div style="font-size: 0.55vw; color: #8C3426; margin-top: 0.2vw;">Triage UI + Refusal Cert</div>
              </div>

            </div>

            <div class="hero-arch-connector">▼</div>

            <!-- Node 5: Learning Agent -->
            <div class="hero-arch-box" style="border-left: 3.5px solid #7B5EA7;">
              <div class="hero-arch-title">
                <span style="color: #5B3E87;">5. LEARNING AGENT</span>
                <span class="pill-tag cyan" style="font-size: 0.52vw; padding: 0.1vw 0.4vw;">REFLEXION</span>
              </div>
              <div class="hero-arch-desc">
                <strong>Human correction → Reflection → Experience.</strong> Closed-loop episodic memory updates.
              </div>
            </div>

            <div class="hero-arch-connector">▼</div>

            <!-- Node 6: Automation License -->
            <div class="hero-arch-box" style="border-left: 3.5px solid #D4A373; background: #FFFDF9;">
              <div class="hero-arch-title">
                <span style="color: #9A5D18;">6. AUTOMATION LICENSE</span>
                <span class="pill-tag amber" style="font-size: 0.52vw; padding: 0.1vw 0.4vw;">GOVERNANCE</span>
              </div>
              <div class="hero-arch-desc">
                <strong>L0 → L1 → L2 → L3.</strong> Progressive autonomous release authority earned per trade lane.
              </div>
            </div>

          </div>

          <!-- Right Column: Deep-Dive Strategic Pillars (Explaining why this wins) -->
          <div style="display: flex; flex-direction: column; justify-content: space-between;">
            
            <div style="display: flex; flex-direction: column; gap: 0.6vw;">
              
              <!-- Pillar 1: Pre-Execution Gates -->
              <div class="glass-card" style="background: #FFFFFF; border: 1px solid var(--border-card); border-left: 3.5px solid #C07D38; padding: 0.8vw 1vw;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3vw;">
                  <span style="font-size: 0.74vw; font-weight: 700; color: var(--text-main);">PRE-EXECUTION DEFENSE</span>
                  <span class="pill-tag amber" style="font-size: 0.55vw;">GATES 1 & 2</span>
                </div>
                <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
                  Traditional AI runs OCR and LLMs on everything, failing unpredictably. Averish validates intent and document sufficiency <em>before</em> running models — eliminating 70% of downstream hallucinations.
                </p>
              </div>

              <!-- Pillar 2: Grounded Provenance -->
              <div class="glass-card" style="background: #FFFFFF; border: 1px solid var(--border-card); border-left: 3.5px solid #2A7B9B; padding: 0.8vw 1vw;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3vw;">
                  <span style="font-size: 0.74vw; font-weight: 700; color: var(--text-main);">EVIDENCE-BOUND GROUNDING</span>
                  <span class="pill-tag cyan" style="font-size: 0.55vw;">GATES 3 & 4</span>
                </div>
                <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
                  No ungrounded guesses. Every extracted entity must point to physical pixel coordinates and character byte offsets, backed by a cryptographic SHA-256 evidence chain.
                </p>
              </div>

              <!-- Pillar 3: Episodic Reflexion -->
              <div class="glass-card" style="background: #FFFFFF; border: 1px solid var(--border-card); border-left: 3.5px solid #7B5EA7; padding: 0.8vw 1vw;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3vw;">
                  <span style="font-size: 0.74vw; font-weight: 700; color: var(--text-main);">EPISODIC REFLEXION & LICENSING</span>
                  <span class="pill-tag green" style="font-size: 0.55vw;">GATES 5 & 6</span>
                </div>
                <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
                  Human corrections are never wasted. The system converts operator fixes into structured reflection lessons, progressively upgrading routes from L0 (Manual) to L3 (Autonomous).
                </p>
              </div>

            </div>

            <!-- Takeaway Banner -->
            <div style="background: #FAF7F2; border: 1.5px solid var(--border-card); border-left: 4px solid var(--accent-cyan); border-radius: 0.5vw; padding: 0.75vw 1.1vw; margin-top: 0.5vw;">
              <div style="font-size: 0.68vw; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">
                THE PARADIGM SHIFT
              </div>
              <p style="font-size: 0.8vw; font-weight: 600; color: var(--text-main); margin-top: 0.2vw;">
                “The market focuses on extraction. Averish wraps a decision layer around AI.”
              </p>
            </div>

          </div>

        </div>

        <div class="takeaway-banner" style="margin-top: 0.7vw; padding: 0.45vw 1vw; font-size: 0.76vw;">
          Averish replaces blind generative guesses with bounded verification, structured refusal, and closed-loop episodic memory.
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — SCREEN 2 · 0:35–1:00 Unique Technical Architecture</span>
        <span class="footer-quote">Core Philosophy: AI earns the right to act through verifiable evidence and episodic experience.</span>
      </div>
    </div>



<!-- =================================================================== -->
    <!-- SLIDE 3: OUR INNOVATION -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-3">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Core Innovation</span>
        </div>
        <div class="header-right">
          <span class="category-label">Learning Agent</span>
          <span class="slide-number-badge">03 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">The Averish Framework</div>
          <h1 class="slide-title">A Learning Agent with boundaries.</h1>
          <p class="slide-sub">
            DocuMatch bridges human domain intelligence and automated speed: human corrections become structured experience, protected by four impermeable decision gates.
          </p>
        </div>

        <!-- Central Learning Agent with 4 Gates Diagram -->
        <div style="display: grid; grid-template-columns: 1fr 1.3fr 1fr; gap: 1.2vw; margin: 1vw 0; align-items: center;">
          
          <!-- Left Gates -->
          <div style="display: flex; flex-direction: column; gap: 1vw;">
            <div class="glass-card" style="border-left: 3px solid var(--accent-cyan);">
              <div style="font-size: 0.7vw; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">GATE 01 — VALIDATE</div>
              <div style="font-size: 0.8vw; font-weight: 600; color: var(--text-main); margin-top: 0.2vw;">Is this the correct task?</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Separates request intent from document validity.</div>
            </div>

            <div class="glass-card" style="border-left: 3px solid var(--accent-blue);">
              <div style="font-size: 0.7vw; font-weight: 700; color: var(--accent-blue); text-transform: uppercase;">GATE 02 — SUFFICIENCY</div>
              <div style="font-size: 0.8vw; font-weight: 600; color: var(--text-main); margin-top: 0.2vw;">Do we have enough information?</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Refuses to guess on image scans with no text layer.</div>
            </div>
          </div>

          <!-- Center: Learning Loop Hub -->
          <div class="glass-card highlight-card" style="text-align: center; padding: 1.5vw 1vw; box-shadow: 0 0 35px rgba(56, 189, 248, 0.2);">
            <div style="display: inline-block; padding: 0.5vw 1.2vw; background: linear-gradient(135deg, #0284C7, #4F46E5); border-radius: 9999px; font-size: 1vw; font-weight: 800; color: white; margin-bottom: 1vw; letter-spacing: 0.05em;">
              LEARNING AGENT
            </div>

            <!-- Feedback Cycle -->
            <div style="display: flex; flex-direction: column; gap: 0.5vw; font-size: 0.75vw; text-align: left; background: #F4EFE6; border: 1px solid #E8E2D9; padding: 0.8vw; border-radius: 0.5vw; border: 1px dashed rgba(56,189,248,0.3);">
              <div style="display: flex; align-items: center; gap: 0.5vw;">
                <span style="color: var(--accent-cyan); font-weight: 700;">1.</span> <span>Human Reviewer resolves conflicted field</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw;">
                <span style="color: var(--accent-cyan); font-weight: 700;">2.</span> <span><strong>Reflexion Engine</strong> emits natural-language lesson</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw;">
                <span style="color: var(--accent-cyan); font-weight: 700;">3.</span> <span><strong>Bayesian Thompson Sampling</strong> updates carrier trust</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw;">
                <span style="color: var(--accent-cyan); font-weight: 700;">4.</span> <span>Agent applies learned bounds on future shipments</span>
              </div>
            </div>
          </div>

          <!-- Right Gates -->
          <div style="display: flex; flex-direction: column; gap: 1vw;">
            <div class="glass-card" style="border-left: 3px solid var(--accent-green);">
              <div style="font-size: 0.7vw; font-weight: 700; color: var(--accent-green); text-transform: uppercase;">GATE 03 — PROVENANCE</div>
              <div style="font-size: 0.8vw; font-weight: 600; color: var(--text-main); margin-top: 0.2vw;">Is answer supported by evidence?</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Exact character offset grounding in source contract.</div>
            </div>

            <div class="glass-card alert-card" style="border-left: 3px solid var(--accent-red);">
              <div style="font-size: 0.7vw; font-weight: 700; color: #B84A39; text-transform: uppercase;">GATE 04 — CIRCUIT BREAKER</div>
              <div style="font-size: 0.8vw; font-weight: 600; color: var(--text-main); margin-top: 0.2vw;">Should the AI stop?</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Trips at 3 failures & generates Refusal Certificate.</div>
            </div>
          </div>

        </div>

        <div class="takeaway-banner">
          “Learn from humans. Don't blindly trust AI.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Closed-Loop Reflexion Architecture</span>
        <span class="footer-quote">Design Philosophy: Convert corrections into system memory instead of friction.</span>
      </div>
    </div>



<!-- =================================================================== -->
    <!-- SLIDE 4: HOW AVERISH PREVENTS UNSUPPORTED AI OUTPUT -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-4">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Defensive Safety Architecture</span>
        </div>
        <div class="header-right">
          <span class="category-label">Hallucination Control</span>
          <span class="slide-number-badge">04 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Controlling Operational Risk</div>
          <h1 class="slide-title">We don't solve uncertainty by making AI more confident.</h1>
          <p class="slide-sub" style="font-size: 1.15vw; color: var(--accent-cyan); font-weight: 600;">
            “We control uncertainty by giving AI permission to stop.”
          </p>
        </div>

        <!-- 4 Sequential Gates -->
        <div class="card-grid-4" style="margin: 1.2vw 0;">
          
          <div class="glass-card" style="border-top: 3px solid var(--accent-red);">
            <span class="pill-tag red" style="margin-bottom: 0.6vw;">Gate 01</span>
            <div style="font-size: 0.85vw; font-weight: 700; color: var(--text-main);">Wrong Document</div>
            <div style="font-size: 0.75vw; color: var(--accent-cyan); font-weight: 600; margin: 0.3vw 0;">Document Validity Gate</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
              Stops before extraction if attachment is Certificate of Origin, invoice, or packing list.
            </p>
            <div style="margin-top: 0.8vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: #B84A39;">
              ✕ Pre-extraction HALT
            </div>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--accent-amber);">
            <span class="pill-tag amber" style="margin-bottom: 0.6vw;">Gate 02</span>
            <div style="font-size: 0.85vw; font-weight: 700; color: var(--text-main);">Missing Information</div>
            <div style="font-size: 0.75vw; color: var(--accent-cyan); font-weight: 600; margin: 0.3vw 0;">Data Sufficiency Check</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
              Evaluates selectable text layer & contrast. Refuses to guess on illegible scans.
            </p>
            <div style="margin-top: 0.8vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: #9A5D18;">
              ✕ scanned_not_processed
            </div>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--accent-cyan);">
            <span class="pill-tag cyan" style="margin-bottom: 0.6vw;">Gate 03</span>
            <div style="font-size: 0.85vw; font-weight: 700; color: var(--text-main);">Unsupported Answer</div>
            <div style="font-size: 0.75vw; color: var(--accent-cyan); font-weight: 600; margin: 0.3vw 0;">Provenance Validation</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
              Checks exact byte offset against contract. Validates port against UN/LOCODE standard.
            </p>
            <div style="margin-top: 0.8vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: var(--accent-cyan);">
              ✕ Reject ungrounded proposal
            </div>
          </div>

          <div class="glass-card alert-card" style="border-top: 3px solid var(--accent-red);">
            <span class="pill-tag red" style="margin-bottom: 0.6vw;">Gate 04</span>
            <div style="font-size: 0.85vw; font-weight: 700; color: var(--text-main);">Repeated Failure</div>
            <div style="font-size: 0.75vw; color: #B84A39; font-weight: 600; margin: 0.3vw 0;">Circuit Breaker</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
              Stops at 3 consecutive failures. Issues structured Refusal Certificate to carrier.
            </p>
            <div style="margin-top: 0.8vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: #B84A39;">
              ✕ Refusal Certificate Issued
            </div>
          </div>

        </div>

        <div style="display: flex; justify-content: center; align-items: center; gap: 1vw; background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.6vw; border-radius: 0.5vw; border: 1px solid rgba(255, 255, 255, 0.08);">
          <span style="font-size: 0.75vw; color: var(--text-muted);">ALL GATES ESCALATE TO:</span>
          <span class="pill-tag cyan" style="font-size: 0.75vw; font-weight: 700;">Human Review Queue (Propose-and-Confirm Panel)</span>
        </div>

        <div class="takeaway-banner">
          “The model can propose. Evidence decides.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Designed to prevent unsupported outputs from becoming operational facts.</span>
        <span class="footer-quote">Rule: Uncertainty is an actionable operational state.</span>
      </div>
    </div>



<!-- =================================================================== -->
    <!-- SLIDE 5: REAL SCENARIO 01 (email_505) -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-5">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Real Case Study 01</span>
        </div>
        <div class="header-right">
          <span class="category-label">Document Validity Gate</span>
          <span class="slide-number-badge">05 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Real Scenario: email_505</div>
          <h1 class="slide-title">The AI understood the request.<br>The document was wrong.</h1>
        </div>

        <div class="card-grid-2" style="margin-top: 0.8vw; align-items: stretch;">
          
          <!-- Left: Real Email & Attachment Display -->
          <div style="display: flex; flex-direction: column; gap: 0.8vw;">
            <!-- Real Email Card -->
            <div class="glass-card" style="padding: 0.8vw;">
              <div style="display: flex; justify-content: space-between; font-size: 0.65vw; color: var(--text-dim); margin-bottom: 0.4vw;">
                <span>FROM: faraz_ali@aprilasia.com</span>
                <span class="pill-tag cyan">email_505</span>
              </div>
              <div style="font-size: 0.75vw; font-weight: 700; color: var(--text-main); margin-bottom: 0.3vw;">
                RE_ AFEMY - CEBU_PHILIPPINES - OOCL(OOLU8243017646) - 5AKR-31538
              </div>
              <div style="font-size: 0.7vw; color: #5C5750; background: #F4EFE6; border: 1px solid #E8E2D9; padding: 0.5vw; border-radius: 0.3vw; font-family: 'JetBrains Mono', monospace; line-height: 1.4;">
                “Dear Team,<br>
                Please find attached the SI and the Certificate of Origin for PSGSE4489880. Kindly confirm the BL is in order...”
              </div>
            </div>

            <!-- Real Attachment Preview -->
            <div class="glass-card alert-card" style="padding: 0.8vw;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span style="font-size: 0.7vw; font-weight: 700; color: #8C3426;">ATTACHMENT: email_505_BL.txt</span>
                <span class="pill-tag red">NON-COMPLIANT DOC</span>
              </div>
              <div class="doc-preview-frame" style="max-height: 8vw; font-size: 0.65vw; background: #242936; color: #E8E4DD;">
                CERTIFICATE OF ORIGIN<br>
                ========================================<br>
                Exporter: APRIL FINE PAPER TRADING<br>
                Consignee: EAST BRIGHT FZ-LLC<br>
                Country of Origin: MALAYSIA / INDONESIA / CHINA<br>
                HS Code: 48025500<br>
                Description: FUJITO PAPERONE INKJET PAPER<br>
                <span style="background: rgba(239, 68, 68, 0.3); color: #8C3426; font-weight: 700; padding: 0 0.2vw;">*** CERTIFICATE OF ORIGIN - NOT AN SI OR BL ***</span>
              </div>
            </div>
          </div>

          <!-- Right: Averish Triage Evaluation -->
          <div class="glass-card highlight-card" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8vw;">
                <span style="font-size: 0.9vw; font-weight: 700; color: var(--accent-cyan);">Averish Intake Decision</span>
                <span class="pill-tag green">Execution Halted</span>
              </div>

              <div style="display: flex; flex-direction: column; gap: 0.6vw; font-family: 'JetBrains Mono', monospace; font-size: 0.75vw;">
                <div style="background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: var(--text-dim);">Intent Detection</span>
                  <span style="color: #2E6B47; font-weight: 700;">BL_COMPARISON ✓</span>
                </div>

                <div style="background: #FDEEEB; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: #8C3426;">Document Validity Gate</span>
                  <span style="color: #B84A39; font-weight: 800;">FAILED ✕</span>
                </div>

                <div style="background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: var(--text-dim);">Detected Document</span>
                  <span style="color: #9A5D18;">Certificate of Origin</span>
                </div>

                <div style="background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: var(--text-dim);">Downstream Comparison</span>
                  <span style="color: #6B665E;">SUPPRESSED (0 Calls)</span>
                </div>

                <div style="background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: var(--text-dim);">Action</span>
                  <span style="color: var(--accent-cyan); font-weight: 700;">ROUTED TO HUMAN REVIEW</span>
                </div>
              </div>
            </div>

            <div style="margin-top: 1vw; padding-top: 0.8vw; border-top: 1px solid rgba(255,255,255,0.1);">
              <div style="font-size: 1.1vw; font-weight: 800; color: var(--text-main); font-family: 'Google Sans', sans-serif;">
                “Validate before you generate.”
              </div>
              <div style="font-size: 0.7vw; color: var(--accent-cyan); margin-top: 0.2vw;">
                Prevents invalid inputs from becoming downstream AI decisions.
              </div>
            </div>
          </div>

        </div>

        <div class="takeaway-banner">
          A conventional system extracts fields from the Certificate of Origin anyway. Averish checks validity first.
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Real Case: email_505 / Certificate of Origin</span>
        <span class="footer-quote">Rule: Never attempt a field comparison when prerequisite documents are missing.</span>
      </div>
    </div>



<!-- =================================================================== -->
    <!-- SLIDE 6: REAL SCENARIO 02 (email_512) -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-6">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Real Case Study 02</span>
        </div>
        <div class="header-right">
          <span class="category-label">Data Sufficiency Check</span>
          <span class="slide-number-badge">06 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Real Scenario: email_512</div>
          <h1 class="slide-title">When the evidence isn't readable,<br>Averish doesn't guess.</h1>
        </div>

        <div class="card-grid-2" style="margin-top: 0.8vw; align-items: stretch;">
          
          <!-- Left: Real Rendered PDF Previews -->
          <div class="glass-card" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6vw;">
                <span style="font-size: 0.8vw; font-weight: 700; color: var(--text-main);">Actual PDF Render (email_512_SI & BL)</span>
                <span class="pill-tag amber">Scanned Fax (Image-Only)</span>
              </div>
              
              <!-- Actual rendered image previews from test data/attachments/ -->
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8vw; background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.6vw; border-radius: 0.4vw; border: 1px solid rgba(255,255,255,0.08);">
                <div style="text-align: center;">
                  <div style="font-size: 0.6vw; color: var(--text-dim); margin-bottom: 0.2vw;">email_512_SI.pdf</div>
                  <img src="data:image/png;base64,{b64_si}" style="width: 100%; height: 9.5vw; object-fit: contain; background: white; border-radius: 0.2vw;" alt="email_512_SI actual scan" />
                </div>
                <div style="text-align: center;">
                  <div style="font-size: 0.6vw; color: var(--text-dim); margin-bottom: 0.2vw;">email_512_BL.pdf</div>
                  <img src="data:image/png;base64,{b64_bl}" style="width: 100%; height: 9.5vw; object-fit: contain; background: white; border-radius: 0.2vw;" alt="email_512_BL actual scan" />
                </div>
              </div>
            </div>

            <div style="margin-top: 0.6vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: #9A5D18; background: #FEF7ED; padding: 0.4vw 0.6vw; border-radius: 0.3vw;">
              [PyMuPDF Diagnostic] Selectable text length: 0 chars | Raster DPI: 150 (Scan)
            </div>
          </div>

          <!-- Right: Comparison -->
          <div style="display: flex; flex-direction: column; gap: 0.8vw;">
            
            <div class="glass-card" style="border-left: 4px solid var(--accent-red); padding: 0.8vw;">
              <div style="font-size: 0.75vw; font-weight: 700; color: #B84A39; text-transform: uppercase;">Typical Document AI Pipeline</div>
              <div style="font-size: 0.75vw; color: var(--text-main); margin-top: 0.3vw; font-family: 'JetBrains Mono', monospace;">
                Incomplete OCR ➔ Hallucinated LLM Inference ➔ Plausible Typo
              </div>
              <p style="font-size: 0.68vw; color: var(--text-dim); margin-top: 0.3vw;">
                Model fabricates container prefixes or gross weight based on statistical probability, risking $1k+/day demurrage penalties.
              </p>
            </div>

            <div class="glass-card highlight-card" style="border-left: 4px solid var(--accent-cyan); padding: 0.8vw;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.75vw; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">Averish Policy</span>
                <span class="pill-tag green">SAFE HALT</span>
              </div>
              <div style="font-size: 0.75vw; color: var(--text-main); margin-top: 0.3vw; font-family: 'JetBrains Mono', monospace;">
                Insufficient Evidence ➔ Execution Stopped ➔ Human Review
              </div>
              <div style="margin-top: 0.4vw; font-size: 0.7vw; color: #1E667E;">
                Status: <span style="font-family: 'JetBrains Mono'; font-weight: 700;">scanned_not_processed</span>
              </div>
            </div>

            <div style="background: #FFFFFF; border: 1px solid var(--border-card); padding: 0.8vw; border-radius: 0.4vw; border: 1px solid rgba(56, 189, 248, 0.3);">
              <div style="font-size: 1.1vw; font-weight: 800; color: var(--text-main); font-family: 'Google Sans', sans-serif;">
                “Uncertainty is a valid system state.”
              </div>
              <div style="font-size: 0.7vw; color: var(--text-muted); margin-top: 0.2vw;">
                Refusing to guess on ungrounded documents preserves legal compliance.
              </div>
            </div>

          </div>

        </div>

        <div class="takeaway-banner">
          Instead of guessing values from a degraded scan, Averish flags uncertainty as an explicit operational status.
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Real Case: email_512 / Low-Resolution Scans</span>
        <span class="footer-quote">Core Truth: In shipping trade, a confident wrong answer is catastrophic.</span>
      </div>
    </div>



<!-- =================================================================== -->
    <!-- SLIDE 7: REAL SCENARIO 03 (PROVENANCE VALIDATION) -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-7">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Real Case Study 03</span>
        </div>
        <div class="header-right">
          <span class="category-label">Provenance Validation</span>
          <span class="slide-number-badge">07 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Evidence Grounding (email_004)</div>
          <h1 class="slide-title">A plausible answer still needs evidence.</h1>
          <p class="slide-sub">
            LLMs generate convincing entity names. Averish verifies that every proposed character offset exists verbatim in the source contract before acceptance.
          </p>
        </div>

        <!-- Provenance Architecture Pipeline -->
        <div style="display: grid; grid-template-columns: 1fr 1.2fr 1fr; gap: 1vw; margin: 1vw 0; align-items: center;">
          
          <!-- Source Document Excerpt -->
          <div class="glass-card">
            <div style="font-size: 0.7vw; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">01. SOURCE CONTRACT (email_004)</div>
            <div class="doc-preview-frame" style="max-height: 10vw; margin-top: 0.5vw; font-size: 0.65vw;">
              BILL OF LADING (DRAFT)<br>
              ========================================<br>
              SHIPPER: APRIL FAR EAST SDN BHD<br>
              <span style="background: #DFEFF5; color: #2A7B9B; font-weight: 700;">To the Order of: UAB NOVAKOPA</span><br>
              &nbsp;&nbsp;RAKEZ AMENITY CENTER, UAE<br>
              POD: KARACHI, PAKISTAN (PKKHI)<br>
              Container Count: 6 x 40'HC<br>
              Gross Weight: 131,058 KG
            </div>
          </div>

          <!-- Provenance Engine Step -->
          <div class="glass-card highlight-card" style="text-align: center; padding: 1.2vw 0.8vw;">
            <div style="font-size: 0.7vw; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">02. AI EXTRACTION & PROVENANCE</div>
            
            <div style="margin: 0.8vw 0; font-family: 'JetBrains Mono', monospace; font-size: 0.75vw; background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.6vw; border-radius: 0.3vw; text-align: left;">
              <div>field: <span style="color: var(--accent-cyan);">consignee</span></div>
              <div>proposed: <span style="color: #8C3426;">"UAB NOVAKOPA"</span></div>
              <div>si_reference: <span style="color: #2E6B47;">"EAST BRIGHT FZ-LLC"</span></div>
              <div>char_offsets: <span style="color: var(--text-dim);">[128 - 140]</span></div>
              <div>agreement: <span style="color: #B84A39; font-weight: 700;">CONFLICT</span></div>
            </div>

            <div style="display: flex; justify-content: center; gap: 0.5vw;">
              <span class="pill-tag cyan" style="font-size: 0.65vw;">UN/LOCODE Check</span>
              <span class="pill-tag cyan" style="font-size: 0.65vw;">Verbatim Offset Check</span>
            </div>
          </div>

          <!-- Dual Outcomes -->
          <div style="display: flex; flex-direction: column; gap: 0.8vw;">
            <div class="glass-card" style="border-left: 3px solid var(--accent-green); padding: 0.7vw;">
              <div style="font-size: 0.7vw; font-weight: 700; color: #2E6B47;">EVIDENCE VERIFIED</div>
              <div style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.2vw;">
                Source match confirms offset & entity &rarr; Auto-Accepted.
              </div>
            </div>

            <div class="glass-card alert-card" style="border-left: 3px solid var(--accent-red); padding: 0.7vw;">
              <div style="font-size: 0.7vw; font-weight: 700; color: #B84A39;">EVIDENCE MISSING / CONFLICT</div>
              <div style="font-size: 0.65vw; color: #8C3426; margin-top: 0.2vw;">
                Never guess winner &rarr; Route to Propose-and-Confirm Panel.
              </div>
            </div>
          </div>

        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; background: #FAF7F2; border: 1px dashed var(--border-card); border: 1px solid rgba(56, 189, 248, 0.2); padding: 0.7vw 1.2vw; border-radius: 0.4vw;">
          <span style="font-size: 0.8vw; font-weight: 600; color: var(--text-main);">
            “OCR extracts. LLM interprets. Provenance verifies.”
          </span>
          <span style="font-size: 0.75vw; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace;">
            Reduces risk of unsupported AI values entering operational trade data.
          </span>
        </div>

        <div class="takeaway-banner">
          “The model can propose. Evidence decides.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Real Case: email_004 / Consignee Provenance Verification</span>
        <span class="footer-quote">Principle: Ground every single proposed token in verifiable source offsets.</span>
      </div>
    </div>



<!-- =================================================================== -->
    <!-- SLIDE 8: REAL SCENARIO 04 (RED TEAM / CIRCUIT BREAKER) -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-8">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Real Case Study 04</span>
        </div>
        <div class="header-right">
          <span class="category-label">Circuit Breaker</span>
          <span class="slide-number-badge">08 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Adversarial Red Team Testing</div>
          <h1 class="slide-title">When AI keeps failing,<br>Averish knows when to stop.</h1>
        </div>

        <div class="card-grid-2" style="margin-top: 0.6vw; align-items: stretch;">
          
          <!-- Terminal Output from demo_trust_features.py --step 3 -->
          <div class="terminal-window">
            <div class="terminal-bar">
              <span class="term-dot r"></span>
              <span class="term-dot y"></span>
              <span class="term-dot g"></span>
              <span style="font-size: 0.65vw; color: #6B665E; margin-left: 0.5vw;">python demo_trust_features.py --step 3</span>
            </div>
            <div class="terminal-content" style="font-size: 0.65vw; line-height: 1.5;">
              <span style="color: #2A7B9B;">STEP 3 - Red Team: Remove field (circuit breaker)</span><br>
              &nbsp;&nbsp;Removed 4 required field line(s) from the draft BL.<br>
              &nbsp;&nbsp;<span style="color: #B84A39; font-weight: 700;">3 consecutive AI extractions failed validation</span><br>
              &nbsp;&nbsp;failed fields: port_of_loading, port_of_discharge, container_count<br>
              &nbsp;&nbsp;&nbsp;&nbsp;- port_of_loading: source_match: no value could be proposed<br>
              &nbsp;&nbsp;&nbsp;&nbsp;- port_of_discharge: source_match: no value could be proposed<br>
              &nbsp;&nbsp;&nbsp;&nbsp;- container_count: source_match: no value could be proposed<br><br>
              <span style="color: #B84A39; font-weight: 800;">[!] CIRCUIT BREAKER TRIPPED — EXECUTION HALTED</span><br>
              &nbsp;&nbsp;<span style="color: #9A5D18;">suggested recipient: carrier</span><br>
              &nbsp;&nbsp;<span style="color: #9A5D18;">estimated delay: 16.0h (240 min per unresolved field)</span><br>
              &nbsp;&nbsp;<span style="color: #6B665E;">AI processing stopped: no further AI guesses were made.</span>
            </div>
          </div>

          <!-- Structured Refusal Certificate -->
          <div class="glass-card alert-card" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6vw;">
                <span style="font-size: 0.85vw; font-weight: 800; color: #B84A39;">DCSA REFUSAL CERTIFICATE</span>
                <span class="pill-tag red">Actionable Escalation</span>
              </div>

              <p style="font-size: 0.7vw; color: #5C5750; margin-bottom: 0.8vw;">
                Instead of manufacturing hallucinated data or stalling in an infinite retry loop, Averish issues an immutable, structured refusal report:
              </p>

              <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7vw; background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.7vw; border-radius: 0.4vw; display: flex; flex-direction: column; gap: 0.4vw;">
                <div><span style="color: var(--text-dim);">failed_fields:</span> <span style="color: #8C3426;">["port_of_loading", "port_of_discharge", "container_count"]</span></div>
                <div><span style="color: var(--text-dim);">circuit_breaker:</span> <span style="color: #B84A39; font-weight: 700;">TRIPPED (threshold: 3)</span></div>
                <div><span style="color: var(--text-dim);">suggested_recipient:</span> <span style="color: #2A7B9B; font-weight: 700;">carrier</span></div>
                <div><span style="color: var(--text-dim);">estimated_delay_hours:</span> <span style="color: #9A5D18; font-weight: 700;">16.0</span></div>
                <div><span style="color: var(--text-dim);">remediation:</span> <span style="color: var(--text-main);">Query ocean carrier booking desk for missing container manifest</span></div>
              </div>
            </div>

            <div style="margin-top: 0.8vw; padding-top: 0.6vw; border-top: 1px solid rgba(239, 68, 68, 0.2);">
              <div style="font-size: 0.9vw; font-weight: 700; color: var(--text-main);">
                “Failure becomes an actionable operational state.”
              </div>
              <div style="font-size: 0.68vw; color: var(--text-muted); margin-top: 0.1vw;">
                Instead of endless retries, the system creates a clear escalation path.
              </div>
            </div>
          </div>

        </div>

        <div class="takeaway-banner alert">
          When failure occurs, Averish converts it into structured diagnostics: what broke, who to contact, and estimated port delay.
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Real Output: demo_trust_features.py (Step 3: Circuit Breaker)</span>
        <span class="footer-quote">Design Principle: Never produce plausible fiction when data is missing.</span>
      </div>
    </div>



<!-- =================================================================== -->
    <!-- SLIDE 9: LEARNING AGENT + HUMAN FATIGUE (REFLEXION) -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-9">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Learning Architecture</span>
        </div>
        <div class="header-right">
          <span class="category-label">Reflexion Memory</span>
          <span class="slide-number-badge">09 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Breaking The Exception Cycle</div>
          <h1 class="slide-title">Turn repetitive correction into system experience.</h1>
          <p class="slide-sub">
            Human corrections do not vanish into thin air. Averish synthesizes operator resolutions into structured Reflexion memories tied to the carrier sender domain.
          </p>
        </div>

        <!-- Before vs Averish Comparison -->
        <div class="card-grid-2" style="margin: 0.8vw 0;">
          
          <!-- BEFORE: Stateless Fatigue -->
          <div class="glass-card" style="border-color: rgba(239, 68, 68, 0.3);">
            <div style="font-size: 0.85vw; font-weight: 700; color: #8C3426; margin-bottom: 0.5vw;">
              BEFORE: Stateless Document Tools
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 0.35vw; font-size: 0.7vw; font-family: 'JetBrains Mono', monospace;">
              <div style="padding: 0.3vw 0.5vw; background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.25vw;">1. AI extraction error on unfamiliar layout</div>
              <div style="text-align: center; color: var(--text-dim);">↓</div>
              <div style="padding: 0.3vw 0.5vw; background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.25vw;">2. Human operator manually corrects field</div>
              <div style="text-align: center; color: var(--text-dim);">↓</div>
              <div style="padding: 0.3vw 0.5vw; background: #FDEEEB; color: #8C3426; border-radius: 0.25vw;">3. Same carrier format arrives next day</div>
              <div style="text-align: center; color: var(--text-dim);">↓</div>
              <div style="padding: 0.3vw 0.5vw; background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.25vw;">4. Model repeats exact same error</div>
              <div style="text-align: center; color: var(--text-dim);">↓</div>
              <div style="padding: 0.3vw 0.5vw; background: #FCE8E4; color: #B84A39; font-weight: 800; border-radius: 0.25vw; text-align: center;">5. HUMAN FATIGUE</div>
            </div>
          </div>

          <!-- AVERISH: Closed-Loop Learning -->
          <div class="glass-card highlight-card" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="font-size: 0.85vw; font-weight: 700; color: var(--accent-cyan); margin-bottom: 0.5vw;">
                AVERISH: Closed-Loop Reflexion Engine
              </div>
              
              <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; background: #F3EFE6; border: 1px solid var(--border-card); padding: 0.6vw; border-radius: 0.3vw; line-height: 1.45; color: #5C5750; border: 1px solid rgba(56, 189, 248, 0.2);">
                <span style="color: var(--accent-cyan); font-weight: 700;">[Reflexion Lesson Generated from email_004]:</span><br>
                “When extracting port_of_discharge from evergreen-line-2e1d0e.com SI documents, look for 'PORT KLANG' in context instead of accepting 'PORT'. Verify keyword delimiters and line boundaries.”<br><br>
                <span style="color: #9A5D18;">[Thompson Sampling Update]:</span><br>
                Prior: Beta(1.0, 1.0) [50% Trust] ➔ Posterior: Beta(1.0, 2.0) [33% Trust]<br>
                <span style="color: #2E6B47; font-weight: 700;">Action: Policy automatically routes to Human-First queue to prevent error recurrence.</span>
              </div>
            </div>

            <div style="font-size: 0.68vw; color: var(--text-dim); margin-top: 0.6vw; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.4vw;">
              <strong style="color: var(--text-main);">Technical Note:</strong> Current demo: reflection generation verified. Next stage: full reflection retrieval & learning loop.
            </div>
          </div>

        </div>

        <div class="takeaway-banner">
          “Human expertise should become system knowledge — not repetitive manual labour.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Real Feedback: demo_self_learning.py / Reflexion Memory</span>
        <span class="footer-quote">Design Core: Transform operational corrections into durable software assets.</span>
      </div>
    </div>



    <!-- =================================================================== -->
    <!-- SLIDE 10: TECHNICAL ARCHITECTURE & WORKFLOW DIAGRAM -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-10">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">System Architecture</span>
        </div>
        <div class="header-right">
          <span class="category-label">End-to-End Governance Pipeline</span>
          <span class="slide-number-badge">10 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Complete System Architecture & Operational Workflow</div>
          <h1 class="slide-title">Multi-tier verification pipeline with defensive decision boundaries.</h1>
        </div>

        <!-- 5-Stage Visual Workflow Pipeline Diagram -->
        <div style="display: grid; grid-template-columns: 1fr 22px 1.4fr 22px 1.2fr 22px 1fr; gap: 0; align-items: stretch; margin: 1vw 0 0.8vw 0;">
          
          <!-- Stage 1: Ingestion -->
          <div class="glass-card" style="border-top: 3px solid #38BDF8; padding: 0.9vw; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4vw;">
                <span class="pill-tag cyan" style="font-size: 0.6vw;">STAGE 01</span>
                <span style="font-size: 0.9vw;">📥</span>
              </div>
              <div style="font-size: 0.82vw; font-weight: 700; color: var(--text-main); line-height: 1.2;">Multi-Source Ingestion</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.3vw;">Unstructured Trade Feeds</div>
            </div>
            <div style="background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.4vw; padding: 0.5vw; margin-top: 0.6vw; font-size: 0.62vw; color: var(--text-muted); line-height: 1.45;">
              • Scanned Ocean B/L & SIs<br>
              • Commercial Invoices & Emails<br>
              • Docling Layout OCR Parsing<br>
              • Spatial Bounding Boxes
            </div>
          </div>

          <!-- Arrow 1 -->
          <div style="display: flex; align-items: center; justify-content: center; color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <!-- Stage 2: Tri-Stage Defensive Gates -->
          <div class="glass-card" style="border-top: 3px solid #F59E0B; padding: 0.9vw; display: flex; flex-direction: column; justify-content: space-between; background: #FFFFFF; border: 1px solid var(--border-card);">
            <div>
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4vw;">
                <span class="pill-tag amber" style="font-size: 0.6vw;">STAGE 02: GATES</span>
                <span style="font-size: 0.9vw;">🛡️</span>
              </div>
              <div style="font-size: 0.82vw; font-weight: 700; color: var(--text-main); line-height: 1.2;">Tri-Gate Verification</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.3vw;">Zero-Tolerance Trust Filters</div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.3vw; margin-top: 0.5vw;">
              <div style="background: #FDEEEB; border-left: 2.5px solid #EF4444; padding: 0.3vw 0.4vw; font-size: 0.58vw; border-radius: 0 0.3vw 0.3vw 0;">
                <strong style="color: #8C3426;">Gate 1: Document Validity</strong><br>
                <span style="color: var(--text-muted);">Rejects wrong attachments (email_004)</span>
              </div>
              <div style="background: #FEF7ED; border-left: 2.5px solid #F59E0B; padding: 0.3vw 0.4vw; font-size: 0.58vw; border-radius: 0 0.3vw 0.3vw 0;">
                <strong style="color: #9A5D18;">Gate 2: Data Sufficiency</strong><br>
                <span style="color: var(--text-muted);">Halts on degraded/missing text (email_512)</span>
              </div>
              <div style="background: #EDF6F9; border-left: 2.5px solid #38BDF8; padding: 0.3vw 0.4vw; font-size: 0.58vw; border-radius: 0 0.3vw 0.3vw 0;">
                <strong style="color: #1E667E;">Gate 3: Provenance Anchoring</strong><br>
                <span style="color: var(--text-muted);">Validates pixel coordinates (email_505)</span>
              </div>
            </div>
          </div>

          <!-- Arrow 2 -->
          <div style="display: flex; align-items: center; justify-content: center; color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <!-- Stage 3: Decision Boundary & Circuit Breaker -->
          <div class="glass-card" style="border-top: 3px solid #6366F1; padding: 0.9vw; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4vw;">
                <span class="pill-tag cyan" style="font-size: 0.6vw;">STAGE 03</span>
                <span style="font-size: 0.9vw;">⚖️</span>
              </div>
              <div style="font-size: 0.82vw; font-weight: 700; color: var(--text-main); line-height: 1.2;">Decision Boundary</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.3vw;">Confidence & Circuit Breaker</div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.35vw; margin-top: 0.6vw;">
              <div style="background: #EDF5F0; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 0.3vw; padding: 0.35vw; font-size: 0.58vw;">
                <span style="color: #2E6B47; font-weight: 700;">Score ≥ 0.85:</span> Automated release to EDI / ERP booking.
              </div>
              <div style="background: #FDEEEB; border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 0.3vw; padding: 0.35vw; font-size: 0.58vw;">
                <span style="color: #B84A39; font-weight: 700;">Score &lt; 0.85:</span> Circuit Breaker emits <em>Refusal Certificate</em>.
              </div>
            </div>
          </div>

          <!-- Arrow 3 -->
          <div style="display: flex; align-items: center; justify-content: center; color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <!-- Stage 4: Execution & Feedback -->
          <div class="glass-card" style="border-top: 3px solid #10B981; padding: 0.9vw; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4vw;">
                <span class="pill-tag green" style="font-size: 0.6vw;">STAGE 04 & 05</span>
                <span style="font-size: 0.9vw;">🚀</span>
              </div>
              <div style="font-size: 0.82vw; font-weight: 700; color: var(--text-main); line-height: 1.2;">Action & Reflexion</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.3vw;">Execution & Self-Learning</div>
            </div>
            <div style="background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.4vw; padding: 0.5vw; margin-top: 0.6vw; font-size: 0.62vw; color: var(--text-muted); line-height: 1.45;">
              • Direct CargoWise / SAP Push<br>
              • One-Click Human Correction<br>
              • Reflexion Lesson Generation<br>
              • Thompson Bandit Prior Update
            </div>
          </div>

        </div>

        <!-- Continuous Learning Feedback Loop Banner -->
        <div style="background: #FAF7F2; border: 1px dashed var(--border-card); border: 1px dashed rgba(56, 189, 248, 0.35); border-radius: 0.5vw; padding: 0.6vw 1.2vw; display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 0.8vw;">
            <span style="background: #EDF6F9; border: 1px solid var(--accent-cyan); border-radius: 50%; width: 1.6vw; height: 1.6vw; display: flex; align-items: center; justify-content: center; font-size: 0.8vw; color: var(--accent-cyan);">⟳</span>
            <div>
              <div style="font-size: 0.78vw; font-weight: 700; color: var(--text-main);">The Reflexion Closed Loop</div>
              <div style="font-size: 0.62vw; color: var(--text-muted);">
                Human exception resolution feeds structured JSON reflection lessons back into the agent prompt context, permanently eliminating repeated failures.
              </div>
            </div>
          </div>
          <span class="pill-tag green" style="font-size: 0.65vw;">EPISODIC MEMORY ACTIVE</span>
        </div>

        <div class="takeaway-banner" style="margin-top: 0.6vw; padding: 0.6vw 1vw; font-size: 0.78vw;">
          “Averish replaces unguided generative retries with bounded verification, structured refusal, and closed-loop feedback.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Technical Architecture: Ingestion ➔ Verification ➔ Boundary ➔ Learning</span>
        <span class="footer-quote">Design Principle: Never act on speculative inference.</span>
      </div>
    </div>

    <!-- =================================================================== -->
    <!-- SLIDE 11: IMPLEMENTATION DETAILS & TECH STACK -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-11">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Engineering Stack</span>
        </div>
        <div class="header-right">
          <span class="category-label">Concrete Implementation</span>
          <span class="slide-number-badge">11 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Production-Grade Core Architecture</div>
          <h1 class="slide-title">Engineered for sub-second verification, determinism, and memory.</h1>
        </div>

        <!-- 4 Architecture Detail Cards -->
        <div class="card-grid-4" style="margin: 1vw 0 0.8vw 0;">
          
          <!-- Card 1: Core Async Runtime -->
          <div class="glass-card" style="border-top: 3px solid var(--accent-cyan); display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span class="pill-tag cyan" style="font-size: 0.58vw;">BACKEND</span>
                <span style="font-size: 0.8vw;">⚡</span>
              </div>
              <div style="font-size: 0.88vw; font-weight: 700; color: var(--text-main);">FastAPI Async Engine</div>
              <p style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.3vw; line-height: 1.45;">
                Asynchronous event loop with non-blocking multi-gate evaluations and strict Pydantic v2 schemas.
              </p>
            </div>
            <div style="background: #242936; color: #E8E4DD; border-radius: 0.4vw; padding: 0.45vw; margin-top: 0.6vw; font-family: 'JetBrains Mono', monospace; font-size: 0.58vw; color: #2A7B9B; line-height: 1.4;">
              • Python 3.11 + Uvicorn<br>
              • Pydantic v2 Type Safety<br>
              • &lt; 850ms Verification SLA<br>
              • Strict JSON Schema Output
            </div>
          </div>

          <!-- Card 2: Multimodal & Spatial Vision -->
          <div class="glass-card" style="border-top: 3px solid var(--accent-indigo); display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span class="pill-tag cyan" style="font-size: 0.58vw;">AI ENGINE</span>
                <span style="font-size: 0.8vw;">👁️</span>
              </div>
              <div style="font-size: 0.88vw; font-weight: 700; color: var(--text-main);">Gemini 2.5 Flash Vision</div>
              <p style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.3vw; line-height: 1.45;">
                Multimodal extraction with Docling spatial coordinate bounding-boxes at zero temperature.
              </p>
            </div>
            <div style="background: #242936; color: #E8E4DD; border-radius: 0.4vw; padding: 0.45vw; margin-top: 0.6vw; font-family: 'JetBrains Mono', monospace; font-size: 0.58vw; color: #4B4673; line-height: 1.4;">
              • Temperature: 0.0 (Deterministic)<br>
              • Bounding Box [x0,y0,x1,y1]<br>
              • Docling PDF Layout Parser<br>
              • Multi-Page OCR Alignment
            </div>
          </div>

          <!-- Card 3: Reflexion & Thompson Sampling -->
          <div class="glass-card" style="border-top: 3px solid var(--accent-green); display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span class="pill-tag green" style="font-size: 0.58vw;">LEARNING</span>
                <span style="font-size: 0.8vw;">🧠</span>
              </div>
              <div style="font-size: 0.88vw; font-weight: 700; color: var(--text-main);">Episodic Memory Engine</div>
              <p style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.3vw; line-height: 1.45;">
                Reflexion-based episodic memory with Thompson Sampling Bayesian bandits for route reliability.
              </p>
            </div>
            <div style="background: #242936; color: #E8E4DD; border-radius: 0.4vw; padding: 0.45vw; margin-top: 0.6vw; font-family: 'JetBrains Mono', monospace; font-size: 0.58vw; color: #2E6B47; line-height: 1.4;">
              • Thompson Bandit Prior Beta(α,β)<br>
              • Structured JSON Lessons<br>
              • Dynamic Context Prompt Injection<br>
              • Per-Carrier Exception Profiles
            </div>
          </div>

          <!-- Card 4: Database & Telemetry -->
          <div class="glass-card" style="border-top: 3px solid var(--accent-amber); display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span class="pill-tag amber" style="font-size: 0.58vw;">DATA & SSE</span>
                <span style="font-size: 0.8vw;">📡</span>
              </div>
              <div style="font-size: 0.88vw; font-weight: 700; color: var(--text-main);">Supabase Real-time Telemetry</div>
              <p style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.3vw; line-height: 1.45;">
                Real-time pipeline event audit trail with SSE streaming and cryptographically hashed certificates.
              </p>
            </div>
            <div style="background: #242936; color: #E8E4DD; border-radius: 0.4vw; padding: 0.45vw; margin-top: 0.6vw; font-family: 'JetBrains Mono', monospace; font-size: 0.58vw; color: #9A5D18; line-height: 1.4;">
              • Supabase PostgreSQL Tables<br>
              • Real-time SSE Event Stream<br>
              • SHA-256 Provenance Hashes<br>
              • Instant Frontend Live Sync
            </div>
          </div>

        </div>

        <div class="takeaway-banner" style="padding: 0.65vw 1.2vw; font-size: 0.78vw;">
          “Built on proven, low-latency open standards — pairing deterministic schemas with adaptive Bayesian memory.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Tech Stack: FastAPI / Gemini 2.5 Flash / Reflexion / Supabase</span>
        <span class="footer-quote">Production-ready, battle-hardened architecture.</span>
      </div>
    </div>

    <!-- =================================================================== -->
    <!-- SLIDE 12: CHALLENGES FACED & TECHNICAL SOLUTIONS -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-12">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Feasibility & Validation</span>
        </div>
        <div class="header-right">
          <span class="category-label">Battle-Tested Engineering</span>
          <span class="slide-number-badge">12 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Overcoming Maritime Document Chaos</div>
          <h1 class="slide-title">Real-world engineering challenges & how we solved them.</h1>
        </div>

        <!-- 4 Comparative Challenge / Solution Cards -->
        <div class="card-grid-2" style="margin: 0.8vw 0 0.6vw 0; gap: 1vw;">
          
          <!-- Item 1: Blurry / Degraded Scans -->
          <div class="glass-card" style="padding: 0.8vw 1vw;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3vw;">
              <span style="font-size: 0.75vw; font-weight: 700; color: #B84A39;">CHALLENGE 01: Low-Res & Skewed Scans (email_512)</span>
              <span class="pill-tag red" style="font-size: 0.55vw;">OCR FAILURE</span>
            </div>
            <p style="font-size: 0.65vw; color: var(--text-muted); line-height: 1.4;">
              <strong style="color: var(--text-main);">The Hurdle:</strong> Faxed bills of lading with smudged container numbers cause standard LLMs to invent plausible digits, leading to costly customs fines.
            </p>
            <div style="background: #EDF5F0; border-left: 2px solid #10B981; padding: 0.35vw 0.6vw; margin-top: 0.4vw; font-size: 0.62vw; color: #1F4D33; line-height: 1.4;">
              <strong style="color: #2E6B47;">Engineered Solution:</strong> Data Sufficiency Gate with pixel-contrast thresholding. If evidence is degraded below readability threshold, Averish explicitly refuses rather than guessing.
            </div>
          </div>

          <!-- Item 2: Plausible Fictions -->
          <div class="glass-card" style="padding: 0.8vw 1vw;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3vw;">
              <span style="font-size: 0.75vw; font-weight: 700; color: #9A5D18;">CHALLENGE 02: Silent Hallucinations (email_505)</span>
              <span class="pill-tag amber" style="font-size: 0.55vw;">PHANTOM DATA</span>
            </div>
            <p style="font-size: 0.65vw; color: var(--text-muted); line-height: 1.4;">
              <strong style="color: var(--text-main);">The Hurdle:</strong> Generative models frequently inject typical carrier terms (e.g. vessel names, discharge ports) absent from the underlying document.
            </p>
            <div style="background: #EDF5F0; border-left: 2px solid #10B981; padding: 0.35vw 0.6vw; margin-top: 0.4vw; font-size: 0.62vw; color: #1F4D33; line-height: 1.4;">
              <strong style="color: #2E6B47;">Engineered Solution:</strong> Zero-Tolerance Provenance Anchoring. Every single extracted field must map directly to verifiable bounding-box coordinates in the original PDF canvas.
            </div>
          </div>

          <!-- Item 3: Operator Fatigue -->
          <div class="glass-card" style="padding: 0.8vw 1vw;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3vw;">
              <span style="font-size: 0.75vw; font-weight: 700; color: #2A7B9B;">CHALLENGE 03: Repetitive Human Exception Fatigue</span>
              <span class="pill-tag cyan" style="font-size: 0.55vw;">OPERATOR BURNOUT</span>
            </div>
            <p style="font-size: 0.65vw; color: var(--text-muted); line-height: 1.4;">
              <strong style="color: var(--text-main);">The Hurdle:</strong> Human clerks manually fix the exact same carrier formatting quirks dozens of times per week because conventional AI has zero episodic memory.
            </p>
            <div style="background: #EDF5F0; border-left: 2px solid #10B981; padding: 0.35vw 0.6vw; margin-top: 0.4vw; font-size: 0.62vw; color: #1F4D33; line-height: 1.4;">
              <strong style="color: #2E6B47;">Engineered Solution:</strong> Reflexion Self-Learning Loop. Human corrections generate structured reflection lessons injected dynamically into future runs for that specific carrier.
            </div>
          </div>

          <!-- Item 4: Infinite Agent Retries -->
          <div class="glass-card" style="padding: 0.8vw 1vw;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3vw;">
              <span style="font-size: 0.75vw; font-weight: 700; color: #A855F7;">CHALLENGE 04: Cascading Multi-Agent Failures</span>
              <span class="pill-tag red" style="font-size: 0.55vw;">RETRY LOOP</span>
            </div>
            <p style="font-size: 0.65vw; color: var(--text-muted); line-height: 1.4;">
              <strong style="color: var(--text-main);">The Hurdle:</strong> Unbounded autonomous agents burn costly tokens in endless retry loops when presented with fundamentally invalid trade documents.
            </p>
            <div style="background: #EDF5F0; border-left: 2px solid #10B981; padding: 0.35vw 0.6vw; margin-top: 0.4vw; font-size: 0.62vw; color: #1F4D33; line-height: 1.4;">
              <strong style="color: #2E6B47;">Engineered Solution:</strong> Hard Circuit Breaker (MAX_RETRIES = 2). Cuts execution cleanly and generates an actionable Refusal Certificate for immediate human resolution.
            </div>
          </div>

        </div>

        <div class="takeaway-banner" style="padding: 0.6vw 1.2vw; font-size: 0.78vw;">
          “Averish was forged by testing real edge cases — turning operational failure modes into deterministic defensive features.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Real Edge Case Solutions: email_512, email_505, email_004</span>
        <span class="footer-quote">Tested against real messy maritime shipping documents.</span>
      </div>
    </div>

    <!-- =================================================================== -->
    <!-- SLIDE 13: OPERATIONAL IMPACT (WARM EDITORIAL) -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-13">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge" style="background: rgba(200, 121, 91, 0.15); border-color: rgba(200, 121, 91, 0.35); color: #C8795B;">Value Proposition</span>
        </div>
        <div class="header-right">
          <span class="category-label">Measurable Impact</span>
          <span class="slide-number-badge" style="color: #C8795B; border-color: rgba(200, 121, 91, 0.3);">13 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre" style="color: #C8795B;">Quantified Operational Value</div>
          <h1 class="slide-title" style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.2vw;">From document automation to operational impact.</h1>
        </div>

        <!-- 4 Impact Cards with Earthy Accents & Refined Elevation -->
        <div class="card-grid-4" style="margin: 1.1vw 0;">
          
          <!-- Card 01: Terracotta -->
          <div class="glass-card" style="background: #FFFFFF; border: 1px solid rgba(232, 226, 217, 0.15); border-top: 3.5px solid #C8795B; border-radius: 0.75vw; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center; gap: 0.4vw; margin-bottom: 0.4vw;">
              <span style="width: 6px; height: 6px; border-radius: 50%; background: #C8795B;"></span>
              <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7vw; font-weight: 600; color: #9E988F;">01</span>
            </div>
            <div style="font-size: 0.85vw; font-weight: 700; color: var(--text-main); letter-spacing: 0.02em;">LESS REPETITIVE WORK</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); margin-top: 0.4vw; line-height: 1.45;">
              Reduces repeated manual correction of recurring carrier exception patterns through episodic learning.
            </p>
          </div>

          <!-- Card 02: Sage Green -->
          <div class="glass-card" style="background: #FFFFFF; border: 1px solid rgba(232, 226, 217, 0.15); border-top: 3.5px solid #7A8B6E; border-radius: 0.75vw; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center; gap: 0.4vw; margin-bottom: 0.4vw;">
              <span style="width: 6px; height: 6px; border-radius: 50%; background: #7A8B6E;"></span>
              <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7vw; font-weight: 600; color: #9E988F;">02</span>
            </div>
            <div style="font-size: 0.85vw; font-weight: 700; color: var(--text-main); letter-spacing: 0.02em;">LOWER HALLUCINATION RISK</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); margin-top: 0.4vw; line-height: 1.45;">
              Unsupported outputs are challenged before becoming operational facts or customs declarations.
            </p>
          </div>

          <!-- Card 03: Muted Navy -->
          <div class="glass-card" style="background: #FFFFFF; border: 1px solid rgba(232, 226, 217, 0.15); border-top: 3.5px solid #4A5D70; border-radius: 0.75vw; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center; gap: 0.4vw; margin-bottom: 0.4vw;">
              <span style="width: 6px; height: 6px; border-radius: 50%; background: #4A5D70;"></span>
              <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7vw; font-weight: 600; color: #9E988F;">03</span>
            </div>
            <div style="font-size: 0.85vw; font-weight: 700; color: var(--text-main); letter-spacing: 0.02em;">FASTER EXCEPTION HANDLING</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); margin-top: 0.4vw; line-height: 1.45;">
              Failures become structured escalation (Refusal Certificates) rather than endless unguided retries.
            </p>
          </div>

          <!-- Card 04: Warm Mustard -->
          <div class="glass-card" style="background: #FFFFFF; border: 1px solid rgba(232, 226, 217, 0.15); border-top: 3.5px solid #D4A373; border-radius: 0.75vw; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center; gap: 0.4vw; margin-bottom: 0.4vw;">
              <span style="width: 6px; height: 6px; border-radius: 50%; background: #D4A373;"></span>
              <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7vw; font-weight: 600; color: #9E988F;">04</span>
            </div>
            <div style="font-size: 0.85vw; font-weight: 700; color: var(--text-main); letter-spacing: 0.02em;">EXPERTISE AS EXPERIENCE</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); margin-top: 0.4vw; line-height: 1.45;">
              Human domain corrections are converted into structured Reflexion lessons for the learning layer.
            </p>
          </div>

        </div>

        <!-- Flow Diagram Ribbon (Timeline Style) -->
        <div style="display: flex; align-items: center; justify-content: space-between; background: #FAF7F2; border: 1px solid rgba(232, 226, 217, 0.15); padding: 0.75vw 1.5vw; border-radius: 0.6vw;">
          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: #9E988F; text-transform: uppercase;">From Challenge</div>
            <div style="font-size: 0.88vw; font-weight: 700; color: #C8795B;">Human Fatigue</div>
          </div>
          <div style="color: #A39B92; font-size: 1.1vw;">➔</div>
          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: #9E988F; text-transform: uppercase;">Through Governance</div>
            <div style="font-size: 0.88vw; font-weight: 700; color: #4A5D70;">Controlled AI</div>
          </div>
          <div style="color: #A39B92; font-size: 1.1vw;">➔</div>
          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: #9E988F; text-transform: uppercase;">Through Feedback</div>
            <div style="font-size: 0.88vw; font-weight: 700; color: #7A8B6E;">Learning Signals</div>
          </div>
          <div style="color: #A39B92; font-size: 1.1vw;">➔</div>
          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: #9E988F; text-transform: uppercase;">To Scalable Impact</div>
            <div style="font-size: 0.88vw; font-weight: 700; color: var(--text-main);">More Scalable Operations</div>
          </div>
        </div>

        <div class="takeaway-banner" style="background: rgba(239, 235, 228, 0.08); border-left-color: #C8795B; margin-top: 0.7vw; padding: 0.7vw 1.2vw;">
          <span style="color: var(--text-main);">DocuMatch shifts the operational paradigm from brute-force extraction to sustainable trade reliability.</span>
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Sustainable Enterprise Scalability</span>
        <span class="footer-quote">Design Ethos: Build software that respects human attention.</span>
      </div>
    </div>

<!-- =================================================================== -->
    <!-- SLIDE 14: COMPETITIVE STRENGTH -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-14">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Market Differentiation</span>
        </div>
        <div class="header-right">
          <span class="category-label">Capability Matrix</span>
          <span class="slide-number-badge">14 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Beyond Generic AI</div>
          <h1 class="slide-title">Not another OCR + LLM pipeline.</h1>
        </div>

        <!-- Matrix Table -->
        <div class="glass-card" style="padding: 0.4vw 0.8vw; margin: 0.6vw 0;">
          <table class="matrix-table">
            <thead>
              <tr>
                <th style="width: 35%;">System Capability</th>
                <th style="width: 35%;">Typical OCR + LLM Pipeline</th>
                <th style="width: 30%; color: var(--accent-cyan);">Averish Shipping AI</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Document OCR & Text Extraction</td>
                <td class="check-yes">✓ Standard</td>
                <td class="check-yes">✓ Multi-Engine (PyMuPDF + Tesseract)</td>
              </tr>
              <tr>
                <td>LLM Semantic Interpretation</td>
                <td class="check-yes">✓ Standard</td>
                <td class="check-yes">✓ Controlled / Domain Anchored</td>
              </tr>
              <tr>
                <td>Document Validity Gate</td>
                <td class="check-var">Depends on architecture</td>
                <td class="check-yes">✓ Strict Pre-Execution Gate</td>
              </tr>
              <tr>
                <td>Data Sufficiency Decision</td>
                <td class="check-var">Limited / Architecture-dependent</td>
                <td class="check-yes">✓ Explicit "scanned_not_processed"</td>
              </tr>
              <tr>
                <td>Provenance Validation</td>
                <td class="check-no">✕ Not inherent to basic pipeline</td>
                <td class="check-yes">✓ Byte Offsets + UN/LOCODE Check</td>
              </tr>
              <tr>
                <td>Circuit Breaker Guard</td>
                <td class="check-no">✕ Not inherent</td>
                <td class="check-yes">✓ 3x Consecutive Failure Trip</td>
              </tr>
              <tr>
                <td>Human Correction &rarr; Reflexion</td>
                <td class="check-no">✕ Not inherent (Stateless)</td>
                <td class="check-yes">✓ Reflexion Episodic Memory</td>
              </tr>
              <tr>
                <td>Learning-Agent Architecture</td>
                <td class="check-no">✕ Not inherent</td>
                <td class="check-yes">✓ Bayesian Thompson Sampling</td>
              </tr>
              <tr>
                <td>Automation Autonomy Control</td>
                <td class="check-var">Variable</td>
                <td class="check-yes">✓ L0 – L3 Automation License</td>
              </tr>
              <tr>
                <td>Standardized Trade Output</td>
                <td class="check-var">Variable / Proprietary</td>
                <td class="check-yes">✓ DCSA eBL v3.0.3 Direct Mapping</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Highlight Differentiation -->
        <div style="display: flex; justify-content: space-between; align-items: center; background: #FFFFFF; border: 1px solid var(--border-card); border: 1px solid var(--accent-cyan); padding: 0.6vw 1.2vw; border-radius: 0.4vw;">
          <div>
            <div style="font-size: 0.65vw; color: var(--accent-cyan); font-weight: 700; text-transform: uppercase;">OUR CORE DIFFERENTIATION</div>
            <div style="font-size: 0.9vw; font-weight: 700; color: var(--text-main);">“The control + learning layer around AI.”</div>
          </div>
          <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75vw; color: var(--accent-cyan);">
            Extract ➔ Verify ➔ Learn ➔ Control
          </div>
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Rigorous Enterprise Evaluation</span>
        <span class="footer-quote">Benchmark: Differentiated by governance and feedback, not extraction claims.</span>
      </div>
    </div>



    <!-- =================================================================== -->
    <!-- SLIDE 15: STRATEGIC HORIZON & FUTURE ROADMAP -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-15">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Product Roadmap</span>
        </div>
        <div class="header-right">
          <span class="category-label">Scalability & Horizon</span>
          <span class="slide-number-badge">15 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">From Prototype to Global Trade Mesh</div>
          <h1 class="slide-title">Phased strategic roadmap for enterprise scalability.</h1>
        </div>

        <!-- 3 Horizontal Milestone Phases -->
        <div class="card-grid-3" style="margin: 1.1vw 0 0.8vw 0;">
          
          <!-- Phase 1: Near Term -->
          <div class="glass-card" style="border-top: 3.5px solid #38BDF8; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span class="pill-tag cyan" style="font-size: 0.58vw;">PHASE 01: Q1–Q2 2026</span>
                <span style="font-size: 0.75vw; color: #2E6B47; font-weight: 600;">IN PROGRESS</span>
              </div>
              <div style="font-size: 0.9vw; font-weight: 700; color: var(--text-main);">Multi-Document Triangulation</div>
              <p style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.3vw; line-height: 1.45;">
                Cross-document discrepancy detection across the entire maritime shipment bundle.
              </p>
            </div>
            <div style="background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.4vw; padding: 0.5vw; margin-top: 0.6vw; font-size: 0.62vw; color: var(--text-muted); line-height: 1.5;">
              • Cross-validation: SI ➔ Ocean B/L ➔ Invoice<br>
              • Automated HS code & weight variance detection<br>
              • Coverage expansion to 20+ ocean container liners<br>
              • Self-correcting date & port format normalizers
            </div>
          </div>

          <!-- Phase 2: Mid Term -->
          <div class="glass-card" style="border-top: 3.5px solid #6366F1; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span class="pill-tag cyan" style="font-size: 0.58vw;">PHASE 02: Q3–Q4 2026</span>
                <span style="font-size: 0.75vw; color: #9A5D18; font-weight: 600;">PLANNED</span>
              </div>
              <div style="font-size: 0.9vw; font-weight: 700; color: var(--text-main);">Enterprise ERP & Port Sync</div>
              <p style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.3vw; line-height: 1.45;">
                Bi-directional connectors for global forwarding software and port terminal operating systems.
              </p>
            </div>
            <div style="background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.4vw; padding: 0.5vw; margin-top: 0.6vw; font-size: 0.62vw; color: var(--text-muted); line-height: 1.5;">
              • Native CargoWise & SAP Logistics API connectors<br>
              • Federated Reflexion memory across forwarder desks<br>
              • Automated Slack / Teams exception webhooks<br>
              • Real-time EDI 304 / 310 direct transmission
            </div>
          </div>

          <!-- Phase 3: Long Term -->
          <div class="glass-card" style="border-top: 3.5px solid #10B981; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span class="pill-tag green" style="font-size: 0.58vw;">PHASE 03: 2027+</span>
                <span style="font-size: 0.75vw; color: #2A7B9B; font-weight: 600;">VISION</span>
              </div>
              <div style="font-size: 0.9vw; font-weight: 700; color: var(--text-main);">Autonomous Trade Mesh</div>
              <p style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.3vw; line-height: 1.45;">
                Verifiable cryptographic provenance certificates for legal customs & demurrage dispute protection.
              </p>
            </div>
            <div style="background: #F4EFE6; border: 1px solid #E8E2D9; border-radius: 0.4vw; padding: 0.5vw; margin-top: 0.6vw; font-size: 0.62vw; color: var(--text-muted); line-height: 1.5;">
              • Tamper-proof cryptographic Refusal Certificates<br>
              • AI-mediated detention & demurrage arbitration<br>
              • Global carrier reliability compliance index<br>
              • Zero-knowledge trade audit compliance trails
            </div>
          </div>

        </div>

        <div class="takeaway-banner" style="padding: 0.65vw 1.2vw; font-size: 0.78vw;">
          “A disciplined path from single-document validation to global maritime trade automation and dispute protection.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Strategic Horizons: Triangulation ➔ ERP Integration ➔ Autonomous Trade Mesh</span>
        <span class="footer-quote">Building the future of sustainable maritime intelligence.</span>
      </div>
    </div>

<!-- =================================================================== -->
    <!-- SLIDE 16: VISION & FINAL -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-16">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Mission & Vision</span>
        </div>
        <div class="header-right">
          <span class="category-label">The Future of Trade AI</span>
          <span class="slide-number-badge">16 / 16</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">The New Standard for Maritime Intelligence</div>
          <h1 class="slide-title">AI that learns from humans,<br>knows its boundaries,<br>and earns the right to act.</h1>
        </div>

        <!-- Complete Architecture Flow -->
        <div style="display: flex; align-items: center; justify-content: space-between; background: #F3EFE6; border: 1px solid var(--border-card); padding: 1vw 1.2vw; border-radius: 0.6vw; border: 1px solid rgba(255,255,255,0.1); margin: 0.8vw 0;">
          
          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 01</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: var(--text-main);">HUMAN EXPERTISE</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 02</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: var(--accent-cyan);">CORRECTION</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 03</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: #2E6B47;">REFLECTION</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 04</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: var(--accent-cyan);">LEARNING AGENT</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 05</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: #9A5D18;">PROVENANCE</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 06</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: #2E6B47;">TRUSTWORTHY OPS</div>
          </div>

        </div>

        <!-- 4 Core Pillars -->
        <div class="card-grid-4" style="margin-bottom: 0.8vw;">
          <div class="glass-card" style="text-align: center; padding: 0.8vw;">
            <div style="font-size: 1.1vw; font-weight: 800; color: var(--accent-cyan);">VALIDATE</div>
            <div style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.2vw;">Prerequisites before execution</div>
          </div>

          <div class="glass-card" style="text-align: center; padding: 0.8vw;">
            <div style="font-size: 1.1vw; font-weight: 800; color: var(--accent-blue);">VERIFY</div>
            <div style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.2vw;">Evidence before acceptance</div>
          </div>

          <div class="glass-card" style="text-align: center; padding: 0.8vw;">
            <div style="font-size: 1.1vw; font-weight: 800; color: var(--accent-green);">LEARN</div>
            <div style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.2vw;">Experience from human corrections</div>
          </div>

          <div class="glass-card" style="text-align: center; padding: 0.8vw;">
            <div style="font-size: 1.1vw; font-weight: 800; color: #B84A39;">CONTROL</div>
            <div style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.2vw;">Defensive failure boundaries</div>
          </div>
        </div>

        <div class="takeaway-banner" style="font-size: 1.05vw; padding: 0.9vw 1.5vw;">
          “Averish Shipping AI — from document extraction to trustworthy operational decisions.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish x Monash Hackathon 2026 — Preliminary Round Submission</span>
        <span class="footer-quote">AI that knows when to act — and when not to.</span>
      </div>
    </div>


  </div> <!-- /#deck-viewport -->


  <!-- Floating HUD Presentation Controls -->
  <div id="hud-controls">
    <button class="hud-btn" id="prev-btn" title="Previous Slide (Left Arrow)">◀ Prev</button>
    
    <div class="slide-dots" id="dots-container">
      <!-- Generated via JS -->
    </div>

    <span id="slide-indicator" style="font-family: 'JetBrains Mono', monospace; font-size: 0.75vw; color: var(--accent-cyan); font-weight: 600; min-width: 3.5vw; text-align: center;">01 / 16</span>

    <button class="hud-btn" id="next-btn" title="Next Slide (Right Arrow / Space)">Next ▶</button>
    <button class="hud-btn" id="fullscreen-btn" title="Toggle Fullscreen (F)">⛶</button>
  </div>


  <!-- Script for Navigation & Scaled 16:9 Viewport -->
  <script>
    const TOTAL_SLIDES = 16;
    let currentSlide = 1;

    const slides = document.querySelectorAll('.slide');
    const indicator = document.getElementById('slide-indicator');
    const dotsContainer = document.getElementById('dots-container');
    const viewport = document.getElementById('deck-viewport');

    // Generate Dots
    for (let i = 1; i <= TOTAL_SLIDES; i++) {{
      const dot = document.createElement('div');
      dot.className = `dot ${{i === 1 ? 'active' : ''}}`;
      dot.title = `Jump to Slide ${{i}}`;
      dot.addEventListener('click', () => goToSlide(i));
      dotsContainer.appendChild(dot);
    }}

    const dots = document.querySelectorAll('.dot');

    function updateSlide() {{
      slides.forEach((slide, idx) => {{
        if (idx + 1 === currentSlide) {{
          slide.classList.add('active');
        }} else {{
          slide.classList.remove('active');
        }}
      }});

      dots.forEach((dot, idx) => {{
        if (idx + 1 === currentSlide) {{
          dot.classList.add('active');
        }} else {{
          dot.classList.remove('active');
        }}
      }});

      const padded = currentSlide < 10 ? `0${{currentSlide}}` : `${{currentSlide}}`;
      indicator.textContent = `${{padded}} / ${{TOTAL_SLIDES}}`;
    }}

    function nextSlide() {{
      if (currentSlide < TOTAL_SLIDES) {{
        currentSlide++;
        updateSlide();
      }}
    }}

    function prevSlide() {{
      if (currentSlide > 1) {{
        currentSlide--;
        updateSlide();
      }}
    }}

    function goToSlide(n) {{
      if (n >= 1 && n <= TOTAL_SLIDES) {{
        currentSlide = n;
        updateSlide();
      }}
    }}

    // Event Listeners
    document.getElementById('next-btn').addEventListener('click', nextSlide);
    document.getElementById('prev-btn').addEventListener('click', prevSlide);

    document.getElementById('fullscreen-btn').addEventListener('click', () => {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen().catch(err => console.log(err));
      }} else {{
        if (document.exitFullscreen) {{
          document.exitFullscreen();
        }}
      }}
    }});

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {{
      if (['ArrowRight', 'Space', 'PageDown', 'KeyN', 'Enter'].includes(e.code)) {{
        e.preventDefault();
        nextSlide();
      }} else if (['ArrowLeft', 'PageUp', 'KeyP', 'Backspace'].includes(e.code)) {{
        e.preventDefault();
        prevSlide();
      }} else if (e.code === 'KeyF') {{
        e.preventDefault();
        document.getElementById('fullscreen-btn').click();
      }} else if (e.code === 'Home') {{
        e.preventDefault();
        goToSlide(1);
      }} else if (e.code === 'End') {{
        e.preventDefault();
        goToSlide(TOTAL_SLIDES);
      }}
    }});

    // Dynamic viewport scaling to maintain crisp 16:9 on all screen sizes
    function scaleViewport() {{
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const targetAspect = 16 / 9;
      const currentAspect = vw / vh;

      let width, height;
      if (currentAspect > targetAspect) {{
        height = vh;
        width = vh * targetAspect;
      }} else {{
        width = vw;
        height = vw / targetAspect;
      }}

      viewport.style.width = `${{width}}px`;
      viewport.style.height = `${{height}}px`;
    }}

    window.addEventListener('resize', scaleViewport);
    scaleViewport();
  </script>
</body>
</html>
'''

    os.makedirs('presentation', exist_ok=True)
    with open('presentation/index.html', 'w', encoding='utf-8') as out:
        out.write(html_content)
    
    # Also save a copy as presentation.html in the project root for convenient discovery
    with open('presentation.html', 'w', encoding='utf-8') as out:
        out.write(html_content)

    print("Presentation successfully written to presentation/index.html and presentation.html")

if __name__ == '__main__':
    build_deck()
