# -*- coding: utf-8 -*-
"""
Builds the 12-slide 16:9 competition-ready HTML presentation deck for Averish Shipping AI.
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
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-midnight: #070B14;
      --bg-surface: #0E1626;
      --bg-card: rgba(18, 28, 48, 0.75);
      --border-card: rgba(56, 189, 248, 0.15);
      --border-subtle: rgba(255, 255, 255, 0.08);
      --accent-cyan: #38BDF8;
      --accent-blue: #3B82F6;
      --accent-indigo: #6366F1;
      --accent-green: #10B981;
      --accent-red: #EF4444;
      --accent-amber: #F59E0B;
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
      --text-dim: #64748B;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: #030712;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      color: var(--text-main);
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      user-select: none;
    }}

    /* 16:9 Presentation Viewport Container */
    #deck-viewport {{
      position: relative;
      width: 100vw;
      height: 56.25vw; /* 16:9 ratio */
      max-height: 100vh;
      max-width: 177.78vh; /* 16:9 ratio */
      background: radial-gradient(circle at 50% -20%, rgba(30, 58, 138, 0.35) 0%, #080D1A 65%, #050811 100%);
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.9), 0 0 0 1px rgba(255, 255, 255, 0.05);
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
      border-bottom: 1px solid var(--border-subtle);
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
      background: linear-gradient(135deg, #0284C7, #4F46E5);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
      font-size: 1vw;
    }}

    .brand-title {{
      font-size: 1.05vw;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #FFFFFF;
      font-family: 'Google Sans', sans-serif;
    }}

    .brand-badge {{
      font-size: 0.65vw;
      font-weight: 600;
      padding: 0.2vw 0.5vw;
      border-radius: 0.25vw;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--accent-cyan);
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
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 600;
    }}

    .slide-number-badge {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85vw;
      font-weight: 600;
      color: var(--accent-cyan);
      background: rgba(255, 255, 255, 0.05);
      padding: 0.2vw 0.6vw;
      border-radius: 0.3vw;
      border: 1px solid rgba(255, 255, 255, 0.1);
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
      color: #FFFFFF;
      letter-spacing: -0.03em;
    }}

    h1.slide-title.alert {{
      color: #F87171;
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
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 9999px;
      padding: 0.4vw 0.8vw;
      display: flex;
      align-items: center;
      gap: 0.8vw;
      z-index: 1000;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    }}

    .hud-btn {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: white;
      padding: 0.35vw 0.75vw;
      border-radius: 9999px;
      font-size: 0.75vw;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.3vw;
      transition: all 0.2s;
    }}

    .hud-btn:hover {{
      background: rgba(56, 189, 248, 0.25);
      border-color: var(--accent-cyan);
      color: var(--accent-cyan);
    }}

    .slide-dots {{
      display: flex;
      gap: 0.35vw;
    }}

    .dot {{
      width: 0.5vw;
      height: 0.5vw;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      cursor: pointer;
      transition: all 0.2s;
    }}

    .dot.active {{
      background: var(--accent-cyan);
      box-shadow: 0 0 8px var(--accent-cyan);
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
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-card);
      border-radius: 0.8vw;
      padding: 1.2vw;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
      position: relative;
    }}

    .glass-card.alert-card {{
      border-color: rgba(239, 68, 68, 0.4);
      background: rgba(36, 15, 20, 0.6);
    }}

    .glass-card.highlight-card {{
      border-color: rgba(56, 189, 248, 0.5);
      background: rgba(14, 30, 56, 0.7);
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
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.35);
      color: #F87171;
    }}

    .pill-tag.green {{
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.35);
      color: #34D399;
    }}

    .pill-tag.cyan {{
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.35);
      color: #38BDF8;
    }}

    .pill-tag.amber {{
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid rgba(245, 158, 11, 0.35);
      color: #FBBF24;
    }}

    /* Terminal Window Mock */
    .terminal-window {{
      background: #090D16;
      border: 1px solid rgba(255, 255, 255, 0.12);
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
      color: #CBD5E1;
    }}

    /* Document Preview Frame */
    .doc-preview-frame {{
      background: #1E293B;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 0.5vw;
      padding: 0.8vw;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7vw;
      line-height: 1.5;
      color: #E2E8F0;
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
      background: rgba(255, 255, 255, 0.06);
      text-align: left;
      padding: 0.55vw 0.8vw;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .matrix-table td {{
      padding: 0.5vw 0.8vw;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: #E2E8F0;
    }}

    .matrix-table tr:hover td {{
      background: rgba(56, 189, 248, 0.04);
    }}

    .matrix-table .check-yes {{
      color: #10B981;
      font-weight: 700;
    }}

    .matrix-table .check-no {{
      color: #EF4444;
      font-weight: 700;
    }}

    .matrix-table .check-var {{
      color: #94A3B8;
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
      color: #FFFFFF;
      margin-top: 0.8vw;
    }}

    .takeaway-banner.alert {{
      background: linear-gradient(90deg, rgba(239, 68, 68, 0.2), rgba(245, 158, 11, 0.1));
      border-left-color: var(--accent-red);
    }}
  </style>
</head>
<body>

  <div id="deck-viewport">

    <!-- =================================================================== -->
    <!-- SLIDE 1: HUMAN FATIGUE -->
    <!-- =================================================================== -->
    <div class="slide active" id="slide-1">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Operational Reality</span>
        </div>
        <div class="header-right">
          <span class="category-label">Human Fatigue</span>
          <span class="slide-number-badge">01 / 12</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">The Enterprise Dilemma</div>
          <h1 class="slide-title">AI was supposed to reduce workload.</h1>
          <p class="slide-sub">
            Traditional document AI acts as an isolated extraction transaction — each exception requires human intervention, but the system learns nothing from the correction.
          </p>
        </div>

        <!-- Operational Fatigue Loop Visual -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin: 1.8vw 0; position: relative;">
          
          <div class="glass-card" style="flex: 1; text-align: center; border-color: rgba(255, 255, 255, 0.1);">
            <div style="font-size: 1.3vw; margin-bottom: 0.3vw;">🤖</div>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">AI Extraction Error</div>
            <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Model guesses on edge case</div>
          </div>

          <div style="color: var(--accent-cyan); font-size: 1.2vw; padding: 0 0.6vw;">➔</div>

          <div class="glass-card" style="flex: 1; text-align: center; border-color: rgba(255, 255, 255, 0.1);">
            <div style="font-size: 1.3vw; margin-bottom: 0.3vw;">🔍</div>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">Human Checks</div>
            <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Operator reviews documents</div>
          </div>

          <div style="color: var(--accent-cyan); font-size: 1.2vw; padding: 0 0.6vw;">➔</div>

          <div class="glass-card" style="flex: 1; text-align: center; border-color: rgba(255, 255, 255, 0.1);">
            <div style="font-size: 1.3vw; margin-bottom: 0.3vw;">✏️</div>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">Human Correction</div>
            <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Fixes container / weight discrepancy</div>
          </div>

          <div style="color: var(--accent-cyan); font-size: 1.2vw; padding: 0 0.6vw;">➔</div>

          <div class="glass-card" style="flex: 1; text-align: center; border-color: rgba(255, 255, 255, 0.1);">
            <div style="font-size: 1.3vw; margin-bottom: 0.3vw;">🔄</div>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">Similar Exception Appears</div>
            <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Same carrier format next morning</div>
          </div>

          <div style="color: var(--accent-cyan); font-size: 1.2vw; padding: 0 0.6vw;">➔</div>

          <div class="glass-card alert-card" style="flex: 1.3; text-align: center; box-shadow: 0 0 25px rgba(239, 68, 68, 0.25);">
            <div style="font-size: 1.3vw; margin-bottom: 0.3vw;">⚠️</div>
            <div style="font-size: 0.95vw; font-weight: 800; color: #EF4444; letter-spacing: 0.04em;">HUMAN FATIGUE</div>
            <div style="font-size: 0.65vw; color: #FCA5A5; margin-top: 0.2vw;">Repeated clerical triage overhead</div>
          </div>
        </div>

        <div class="glass-card" style="background: rgba(15, 23, 42, 0.6); border-left: 4px solid var(--accent-cyan); padding: 0.9vw 1.4vw;">
          <p style="font-size: 0.95vw; color: #E2E8F0; font-style: italic;">
            “When every exception still requires human attention, automation can simply move the workload instead of removing it.”
          </p>
        </div>

        <div class="takeaway-banner alert">
          The problem is not only AI accuracy. It is the operational cost of repeated correction.
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Maritime Document Intelligence</span>
        <span class="footer-quote">Core Finding: Stateless automation shifts human labor rather than eliminating it.</span>
      </div>
    </div>


    <!-- =================================================================== -->
    <!-- SLIDE 2: MARKET GAP -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-2">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Market Gap Analysis</span>
        </div>
        <div class="header-right">
          <span class="category-label">Architectural Gap</span>
          <span class="slide-number-badge">02 / 12</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Decision Layer vs. Extraction Pipe</div>
          <h1 class="slide-title">OCR + LLM can generate an answer.<br>But should it act on that answer?</h1>
        </div>

        <div class="card-grid-2" style="margin-top: 0.8vw;">
          <!-- Left: Typical OCR + LLM -->
          <div class="glass-card" style="border-color: rgba(239, 68, 68, 0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8vw;">
              <span style="font-size: 0.95vw; font-weight: 700; color: #FCA5A5;">Typical OCR + LLM Pipeline</span>
              <span class="pill-tag red">Stateless Extraction</span>
            </div>

            <!-- Steps -->
            <div style="display: flex; align-items: center; gap: 0.5vw; margin-bottom: 1vw; font-size: 0.75vw; font-family: 'JetBrains Mono', monospace;">
              <span style="padding: 0.3vw 0.6vw; background: rgba(255,255,255,0.06); border-radius: 0.25vw;">Document</span>
              <span>➔</span>
              <span style="padding: 0.3vw 0.6vw; background: rgba(255,255,255,0.06); border-radius: 0.25vw;">OCR</span>
              <span>➔</span>
              <span style="padding: 0.3vw 0.6vw; background: rgba(255,255,255,0.06); border-radius: 0.25vw;">LLM</span>
              <span>➔</span>
              <span style="padding: 0.3vw 0.6vw; background: rgba(239, 68, 68, 0.2); border-radius: 0.25vw; color: #F87171; font-weight: 700;">Blind Answer</span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 0.4vw; font-size: 0.75vw;">
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #FDA4AF;">
                <span>✕</span> <span><strong>Wrong document:</strong> Processes Certificate of Origin as BL</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #FDA4AF;">
                <span>✕</span> <span><strong>Incomplete extraction:</strong> Fails silently on unread fields</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #FDA4AF;">
                <span>✕</span> <span><strong>Unsupported values:</strong> Guesses container counts from pixel noise</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #FDA4AF;">
                <span>✕</span> <span><strong>Plausible hallucination:</strong> Fabricates port codes</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #FDA4AF;">
                <span>✕</span> <span><strong>Repeated correction:</strong> No memory of yesterday's fix</span>
              </div>
            </div>
          </div>

          <!-- Right: Averish -->
          <div class="glass-card highlight-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8vw;">
              <span style="font-size: 0.95vw; font-weight: 700; color: var(--accent-cyan);">Averish Decision Architecture</span>
              <span class="pill-tag green">Bounded Learning Agent</span>
            </div>

            <!-- Steps -->
            <div style="display: flex; align-items: center; gap: 0.4vw; margin-bottom: 1vw; font-size: 0.7vw; font-family: 'JetBrains Mono', monospace; flex-wrap: wrap;">
              <span style="padding: 0.25vw 0.5vw; background: rgba(56, 189, 248, 0.15); border-radius: 0.2vw;">Intent</span>
              <span>➔</span>
              <span style="padding: 0.25vw 0.5vw; background: rgba(56, 189, 248, 0.15); border-radius: 0.2vw;">Validate</span>
              <span>➔</span>
              <span style="padding: 0.25vw 0.5vw; background: rgba(56, 189, 248, 0.15); border-radius: 0.2vw;">Extract</span>
              <span>➔</span>
              <span style="padding: 0.25vw 0.5vw; background: rgba(56, 189, 248, 0.15); border-radius: 0.2vw;">Verify</span>
              <span>➔</span>
              <span style="padding: 0.25vw 0.5vw; background: rgba(56, 189, 248, 0.15); border-radius: 0.2vw;">Decision</span>
              <span>➔</span>
              <span style="padding: 0.25vw 0.5vw; background: rgba(16, 185, 129, 0.25); border-radius: 0.2vw; color: #34D399; font-weight: 700;">Act / Stop</span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 0.4vw; font-size: 0.75vw;">
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #BAE6FD;">
                <span>✓</span> <span><strong>Pre-execution Gate:</strong> Halts before reading wrong documents</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #BAE6FD;">
                <span>✓</span> <span><strong>Data Sufficiency:</strong> Rejects unreadable scanned faxes safely</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #BAE6FD;">
                <span>✓</span> <span><strong>Provenance Validation:</strong> Enforces exact byte offsets</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #BAE6FD;">
                <span>✓</span> <span><strong>Circuit Breaker:</strong> Trips at 3 failures & generates Refusal Certificate</span>
              </div>
              <div style="display: flex; align-items: center; gap: 0.5vw; color: #BAE6FD;">
                <span>✓</span> <span><strong>Stateful Memory:</strong> Converts corrections into Reflexion lessons</span>
              </div>
            </div>
          </div>
        </div>

        <div class="takeaway-banner">
          “The market focuses on extraction. Averish adds a decision layer around AI.”
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Decision Boundary vs Extraction Pipe</span>
        <span class="footer-quote">Design Principle: AI should earn the right to act.</span>
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
          <span class="slide-number-badge">03 / 12</span>
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
              <div style="font-size: 0.8vw; font-weight: 600; color: #F8FAFC; margin-top: 0.2vw;">Is this the correct task?</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Separates request intent from document validity.</div>
            </div>

            <div class="glass-card" style="border-left: 3px solid var(--accent-blue);">
              <div style="font-size: 0.7vw; font-weight: 700; color: var(--accent-blue); text-transform: uppercase;">GATE 02 — SUFFICIENCY</div>
              <div style="font-size: 0.8vw; font-weight: 600; color: #F8FAFC; margin-top: 0.2vw;">Do we have enough information?</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Refuses to guess on image scans with no text layer.</div>
            </div>
          </div>

          <!-- Center: Learning Loop Hub -->
          <div class="glass-card highlight-card" style="text-align: center; padding: 1.5vw 1vw; box-shadow: 0 0 35px rgba(56, 189, 248, 0.2);">
            <div style="display: inline-block; padding: 0.5vw 1.2vw; background: linear-gradient(135deg, #0284C7, #4F46E5); border-radius: 9999px; font-size: 1vw; font-weight: 800; color: white; margin-bottom: 1vw; letter-spacing: 0.05em;">
              LEARNING AGENT
            </div>

            <!-- Feedback Cycle -->
            <div style="display: flex; flex-direction: column; gap: 0.5vw; font-size: 0.75vw; text-align: left; background: rgba(0,0,0,0.3); padding: 0.8vw; border-radius: 0.5vw; border: 1px dashed rgba(56,189,248,0.3);">
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
              <div style="font-size: 0.8vw; font-weight: 600; color: #F8FAFC; margin-top: 0.2vw;">Is answer supported by evidence?</div>
              <div style="font-size: 0.65vw; color: var(--text-dim); margin-top: 0.2vw;">Exact character offset grounding in source contract.</div>
            </div>

            <div class="glass-card alert-card" style="border-left: 3px solid var(--accent-red);">
              <div style="font-size: 0.7vw; font-weight: 700; color: #EF4444; text-transform: uppercase;">GATE 04 — CIRCUIT BREAKER</div>
              <div style="font-size: 0.8vw; font-weight: 600; color: #F8FAFC; margin-top: 0.2vw;">Should the AI stop?</div>
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
          <span class="slide-number-badge">04 / 12</span>
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
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">Wrong Document</div>
            <div style="font-size: 0.75vw; color: var(--accent-cyan); font-weight: 600; margin: 0.3vw 0;">Document Validity Gate</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
              Stops before extraction if attachment is Certificate of Origin, invoice, or packing list.
            </p>
            <div style="margin-top: 0.8vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: #EF4444;">
              ✕ Pre-extraction HALT
            </div>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--accent-amber);">
            <span class="pill-tag amber" style="margin-bottom: 0.6vw;">Gate 02</span>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">Missing Information</div>
            <div style="font-size: 0.75vw; color: var(--accent-cyan); font-weight: 600; margin: 0.3vw 0;">Data Sufficiency Check</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
              Evaluates selectable text layer & contrast. Refuses to guess on illegible scans.
            </p>
            <div style="margin-top: 0.8vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: #F59E0B;">
              ✕ scanned_not_processed
            </div>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--accent-cyan);">
            <span class="pill-tag cyan" style="margin-bottom: 0.6vw;">Gate 03</span>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">Unsupported Answer</div>
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
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">Repeated Failure</div>
            <div style="font-size: 0.75vw; color: #EF4444; font-weight: 600; margin: 0.3vw 0;">Circuit Breaker</div>
            <p style="font-size: 0.68vw; color: var(--text-muted); line-height: 1.45;">
              Stops at 3 consecutive failures. Issues structured Refusal Certificate to carrier.
            </p>
            <div style="margin-top: 0.8vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: #EF4444;">
              ✕ Refusal Certificate Issued
            </div>
          </div>

        </div>

        <div style="display: flex; justify-content: center; align-items: center; gap: 1vw; background: rgba(0, 0, 0, 0.4); padding: 0.6vw; border-radius: 0.5vw; border: 1px solid rgba(255, 255, 255, 0.08);">
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
          <span class="slide-number-badge">05 / 12</span>
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
              <div style="font-size: 0.75vw; font-weight: 700; color: #F8FAFC; margin-bottom: 0.3vw;">
                RE_ AFEMY - CEBU_PHILIPPINES - OOCL(OOLU8243017646) - 5AKR-31538
              </div>
              <div style="font-size: 0.7vw; color: #CBD5E1; background: rgba(0,0,0,0.3); padding: 0.5vw; border-radius: 0.3vw; font-family: 'JetBrains Mono', monospace; line-height: 1.4;">
                “Dear Team,<br>
                Please find attached the SI and the Certificate of Origin for PSGSE4489880. Kindly confirm the BL is in order...”
              </div>
            </div>

            <!-- Real Attachment Preview -->
            <div class="glass-card alert-card" style="padding: 0.8vw;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4vw;">
                <span style="font-size: 0.7vw; font-weight: 700; color: #FCA5A5;">ATTACHMENT: email_505_BL.txt</span>
                <span class="pill-tag red">NON-COMPLIANT DOC</span>
              </div>
              <div class="doc-preview-frame" style="max-height: 8vw; font-size: 0.65vw; background: #0E1626;">
                CERTIFICATE OF ORIGIN<br>
                ========================================<br>
                Exporter: APRIL FINE PAPER TRADING<br>
                Consignee: EAST BRIGHT FZ-LLC<br>
                Country of Origin: MALAYSIA / INDONESIA / CHINA<br>
                HS Code: 48025500<br>
                Description: FUJITO PAPERONE INKJET PAPER<br>
                <span style="background: rgba(239, 68, 68, 0.3); color: #FCA5A5; font-weight: 700; padding: 0 0.2vw;">*** CERTIFICATE OF ORIGIN - NOT AN SI OR BL ***</span>
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
                <div style="background: rgba(0,0,0,0.4); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: var(--text-dim);">Intent Detection</span>
                  <span style="color: #34D399; font-weight: 700;">BL_COMPARISON ✓</span>
                </div>

                <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: #FCA5A5;">Document Validity Gate</span>
                  <span style="color: #EF4444; font-weight: 800;">FAILED ✕</span>
                </div>

                <div style="background: rgba(0,0,0,0.4); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: var(--text-dim);">Detected Document</span>
                  <span style="color: #FBBF24;">Certificate of Origin</span>
                </div>

                <div style="background: rgba(0,0,0,0.4); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: var(--text-dim);">Downstream Comparison</span>
                  <span style="color: #94A3B8;">SUPPRESSED (0 Calls)</span>
                </div>

                <div style="background: rgba(0,0,0,0.4); padding: 0.5vw 0.8vw; border-radius: 0.3vw; display: flex; justify-content: space-between;">
                  <span style="color: var(--text-dim);">Action</span>
                  <span style="color: var(--accent-cyan); font-weight: 700;">ROUTED TO HUMAN REVIEW</span>
                </div>
              </div>
            </div>

            <div style="margin-top: 1vw; padding-top: 0.8vw; border-top: 1px solid rgba(255,255,255,0.1);">
              <div style="font-size: 1.1vw; font-weight: 800; color: #FFFFFF; font-family: 'Google Sans', sans-serif;">
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
          <span class="slide-number-badge">06 / 12</span>
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
                <span style="font-size: 0.8vw; font-weight: 700; color: #F8FAFC;">Actual PDF Render (email_512_SI & BL)</span>
                <span class="pill-tag amber">Scanned Fax (Image-Only)</span>
              </div>
              
              <!-- Actual rendered image previews from test data/attachments/ -->
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8vw; background: rgba(0,0,0,0.5); padding: 0.6vw; border-radius: 0.4vw; border: 1px solid rgba(255,255,255,0.08);">
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

            <div style="margin-top: 0.6vw; font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; color: #F59E0B; background: rgba(245, 158, 11, 0.1); padding: 0.4vw 0.6vw; border-radius: 0.3vw;">
              [PyMuPDF Diagnostic] Selectable text length: 0 chars | Raster DPI: 150 (Scan)
            </div>
          </div>

          <!-- Right: Comparison -->
          <div style="display: flex; flex-direction: column; gap: 0.8vw;">
            
            <div class="glass-card" style="border-left: 4px solid var(--accent-red); padding: 0.8vw;">
              <div style="font-size: 0.75vw; font-weight: 700; color: #F87171; text-transform: uppercase;">Typical Document AI Pipeline</div>
              <div style="font-size: 0.75vw; color: #E2E8F0; margin-top: 0.3vw; font-family: 'JetBrains Mono', monospace;">
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
              <div style="font-size: 0.75vw; color: #E2E8F0; margin-top: 0.3vw; font-family: 'JetBrains Mono', monospace;">
                Insufficient Evidence ➔ Execution Stopped ➔ Human Review
              </div>
              <div style="margin-top: 0.4vw; font-size: 0.7vw; color: #BAE6FD;">
                Status: <span style="font-family: 'JetBrains Mono'; font-weight: 700;">scanned_not_processed</span>
              </div>
            </div>

            <div style="background: rgba(14, 30, 56, 0.6); padding: 0.8vw; border-radius: 0.4vw; border: 1px solid rgba(56, 189, 248, 0.3);">
              <div style="font-size: 1.1vw; font-weight: 800; color: #FFFFFF; font-family: 'Google Sans', sans-serif;">
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
          <span class="slide-number-badge">07 / 12</span>
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
              <span style="background: rgba(56, 189, 248, 0.25); color: #38BDF8; font-weight: 700;">To the Order of: UAB NOVAKOPA</span><br>
              &nbsp;&nbsp;RAKEZ AMENITY CENTER, UAE<br>
              POD: KARACHI, PAKISTAN (PKKHI)<br>
              Container Count: 6 x 40'HC<br>
              Gross Weight: 131,058 KG
            </div>
          </div>

          <!-- Provenance Engine Step -->
          <div class="glass-card highlight-card" style="text-align: center; padding: 1.2vw 0.8vw;">
            <div style="font-size: 0.7vw; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">02. AI EXTRACTION & PROVENANCE</div>
            
            <div style="margin: 0.8vw 0; font-family: 'JetBrains Mono', monospace; font-size: 0.75vw; background: rgba(0,0,0,0.4); padding: 0.6vw; border-radius: 0.3vw; text-align: left;">
              <div>field: <span style="color: var(--accent-cyan);">consignee</span></div>
              <div>proposed: <span style="color: #FCA5A5;">"UAB NOVAKOPA"</span></div>
              <div>si_reference: <span style="color: #34D399;">"EAST BRIGHT FZ-LLC"</span></div>
              <div>char_offsets: <span style="color: var(--text-dim);">[128 - 140]</span></div>
              <div>agreement: <span style="color: #EF4444; font-weight: 700;">CONFLICT</span></div>
            </div>

            <div style="display: flex; justify-content: center; gap: 0.5vw;">
              <span class="pill-tag cyan" style="font-size: 0.65vw;">UN/LOCODE Check</span>
              <span class="pill-tag cyan" style="font-size: 0.65vw;">Verbatim Offset Check</span>
            </div>
          </div>

          <!-- Dual Outcomes -->
          <div style="display: flex; flex-direction: column; gap: 0.8vw;">
            <div class="glass-card" style="border-left: 3px solid var(--accent-green); padding: 0.7vw;">
              <div style="font-size: 0.7vw; font-weight: 700; color: #34D399;">EVIDENCE VERIFIED</div>
              <div style="font-size: 0.65vw; color: var(--text-muted); margin-top: 0.2vw;">
                Source match confirms offset & entity &rarr; Auto-Accepted.
              </div>
            </div>

            <div class="glass-card alert-card" style="border-left: 3px solid var(--accent-red); padding: 0.7vw;">
              <div style="font-size: 0.7vw; font-weight: 700; color: #EF4444;">EVIDENCE MISSING / CONFLICT</div>
              <div style="font-size: 0.65vw; color: #FCA5A5; margin-top: 0.2vw;">
                Never guess winner &rarr; Route to Propose-and-Confirm Panel.
              </div>
            </div>
          </div>

        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(14, 30, 56, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); padding: 0.7vw 1.2vw; border-radius: 0.4vw;">
          <span style="font-size: 0.8vw; font-weight: 600; color: #FFFFFF;">
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
          <span class="slide-number-badge">08 / 12</span>
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
              <span style="font-size: 0.65vw; color: #94A3B8; margin-left: 0.5vw;">python demo_trust_features.py --step 3</span>
            </div>
            <div class="terminal-content" style="font-size: 0.65vw; line-height: 1.5;">
              <span style="color: #38BDF8;">STEP 3 - Red Team: Remove field (circuit breaker)</span><br>
              &nbsp;&nbsp;Removed 4 required field line(s) from the draft BL.<br>
              &nbsp;&nbsp;<span style="color: #F87171; font-weight: 700;">3 consecutive AI extractions failed validation</span><br>
              &nbsp;&nbsp;failed fields: port_of_loading, port_of_discharge, container_count<br>
              &nbsp;&nbsp;&nbsp;&nbsp;- port_of_loading: source_match: no value could be proposed<br>
              &nbsp;&nbsp;&nbsp;&nbsp;- port_of_discharge: source_match: no value could be proposed<br>
              &nbsp;&nbsp;&nbsp;&nbsp;- container_count: source_match: no value could be proposed<br><br>
              <span style="color: #EF4444; font-weight: 800;">[!] CIRCUIT BREAKER TRIPPED — EXECUTION HALTED</span><br>
              &nbsp;&nbsp;<span style="color: #FBBF24;">suggested recipient: carrier</span><br>
              &nbsp;&nbsp;<span style="color: #FBBF24;">estimated delay: 16.0h (240 min per unresolved field)</span><br>
              &nbsp;&nbsp;<span style="color: #94A3B8;">AI processing stopped: no further AI guesses were made.</span>
            </div>
          </div>

          <!-- Structured Refusal Certificate -->
          <div class="glass-card alert-card" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6vw;">
                <span style="font-size: 0.85vw; font-weight: 800; color: #EF4444;">DCSA REFUSAL CERTIFICATE</span>
                <span class="pill-tag red">Actionable Escalation</span>
              </div>

              <p style="font-size: 0.7vw; color: #CBD5E1; margin-bottom: 0.8vw;">
                Instead of manufacturing hallucinated data or stalling in an infinite retry loop, Averish issues an immutable, structured refusal report:
              </p>

              <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7vw; background: rgba(0,0,0,0.5); padding: 0.7vw; border-radius: 0.4vw; display: flex; flex-direction: column; gap: 0.4vw;">
                <div><span style="color: var(--text-dim);">failed_fields:</span> <span style="color: #FCA5A5;">["port_of_loading", "port_of_discharge", "container_count"]</span></div>
                <div><span style="color: var(--text-dim);">circuit_breaker:</span> <span style="color: #EF4444; font-weight: 700;">TRIPPED (threshold: 3)</span></div>
                <div><span style="color: var(--text-dim);">suggested_recipient:</span> <span style="color: #38BDF8; font-weight: 700;">carrier</span></div>
                <div><span style="color: var(--text-dim);">estimated_delay_hours:</span> <span style="color: #FBBF24; font-weight: 700;">16.0</span></div>
                <div><span style="color: var(--text-dim);">remediation:</span> <span style="color: #E2E8F0;">Query ocean carrier booking desk for missing container manifest</span></div>
              </div>
            </div>

            <div style="margin-top: 0.8vw; padding-top: 0.6vw; border-top: 1px solid rgba(239, 68, 68, 0.2);">
              <div style="font-size: 0.9vw; font-weight: 700; color: #FFFFFF;">
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
          <span class="slide-number-badge">09 / 12</span>
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
            <div style="font-size: 0.85vw; font-weight: 700; color: #FCA5A5; margin-bottom: 0.5vw;">
              BEFORE: Stateless Document Tools
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 0.35vw; font-size: 0.7vw; font-family: 'JetBrains Mono', monospace;">
              <div style="padding: 0.3vw 0.5vw; background: rgba(0,0,0,0.3); border-radius: 0.25vw;">1. AI extraction error on unfamiliar layout</div>
              <div style="text-align: center; color: var(--text-dim);">↓</div>
              <div style="padding: 0.3vw 0.5vw; background: rgba(0,0,0,0.3); border-radius: 0.25vw;">2. Human operator manually corrects field</div>
              <div style="text-align: center; color: var(--text-dim);">↓</div>
              <div style="padding: 0.3vw 0.5vw; background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border-radius: 0.25vw;">3. Same carrier format arrives next day</div>
              <div style="text-align: center; color: var(--text-dim);">↓</div>
              <div style="padding: 0.3vw 0.5vw; background: rgba(0,0,0,0.3); border-radius: 0.25vw;">4. Model repeats exact same error</div>
              <div style="text-align: center; color: var(--text-dim);">↓</div>
              <div style="padding: 0.3vw 0.5vw; background: rgba(239, 68, 68, 0.25); color: #EF4444; font-weight: 800; border-radius: 0.25vw; text-align: center;">5. HUMAN FATIGUE</div>
            </div>
          </div>

          <!-- AVERISH: Closed-Loop Learning -->
          <div class="glass-card highlight-card" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="font-size: 0.85vw; font-weight: 700; color: var(--accent-cyan); margin-bottom: 0.5vw;">
                AVERISH: Closed-Loop Reflexion Engine
              </div>
              
              <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65vw; background: rgba(0,0,0,0.4); padding: 0.6vw; border-radius: 0.3vw; line-height: 1.45; color: #CBD5E1; border: 1px solid rgba(56, 189, 248, 0.2);">
                <span style="color: var(--accent-cyan); font-weight: 700;">[Reflexion Lesson Generated from email_004]:</span><br>
                “When extracting port_of_discharge from evergreen-line-2e1d0e.com SI documents, look for 'PORT KLANG' in context instead of accepting 'PORT'. Verify keyword delimiters and line boundaries.”<br><br>
                <span style="color: #FBBF24;">[Thompson Sampling Update]:</span><br>
                Prior: Beta(1.0, 1.0) [50% Trust] ➔ Posterior: Beta(1.0, 2.0) [33% Trust]<br>
                <span style="color: #34D399; font-weight: 700;">Action: Policy automatically routes to Human-First queue to prevent error recurrence.</span>
              </div>
            </div>

            <div style="font-size: 0.68vw; color: var(--text-dim); margin-top: 0.6vw; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.4vw;">
              <strong style="color: #F8FAFC;">Technical Note:</strong> Current demo: reflection generation verified. Next stage: full reflection retrieval & learning loop.
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
    <!-- SLIDE 10: OPERATIONAL IMPACT -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-10">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Value Proposition</span>
        </div>
        <div class="header-right">
          <span class="category-label">Measurable Impact</span>
          <span class="slide-number-badge">10 / 12</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">Quantified Operational Value</div>
          <h1 class="slide-title">From document automation to operational impact.</h1>
        </div>

        <!-- 4 Impact Cards -->
        <div class="card-grid-4" style="margin: 1.2vw 0;">
          
          <div class="glass-card" style="border-top: 3px solid var(--accent-cyan);">
            <div style="font-size: 1.2vw; font-weight: 800; color: var(--accent-cyan); margin-bottom: 0.4vw;">01</div>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">LESS REPETITIVE WORK</div>
            <p style="font-size: 0.7vw; color: var(--text-muted); margin-top: 0.4vw; line-height: 1.45;">
              Reduces repeated manual correction of recurring carrier exception patterns through episodic learning.
            </p>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--accent-green);">
            <div style="font-size: 1.2vw; font-weight: 800; color: var(--accent-green); margin-bottom: 0.4vw;">02</div>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">LOWER HALLUCINATION RISK</div>
            <p style="font-size: 0.7vw; color: var(--text-muted); margin-top: 0.4vw; line-height: 1.45;">
              Unsupported outputs are challenged before becoming operational facts or customs declarations.
            </p>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--accent-blue);">
            <div style="font-size: 1.2vw; font-weight: 800; color: var(--accent-blue); margin-bottom: 0.4vw;">03</div>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">FASTER EXCEPTION HANDLING</div>
            <p style="font-size: 0.7vw; color: var(--text-muted); margin-top: 0.4vw; line-height: 1.45;">
              Failures become structured escalation (Refusal Certificates) rather than endless unguided retries.
            </p>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--accent-indigo);">
            <div style="font-size: 1.2vw; font-weight: 800; color: var(--accent-indigo); margin-bottom: 0.4vw;">04</div>
            <div style="font-size: 0.85vw; font-weight: 700; color: #F8FAFC;">EXPERTISE AS EXPERIENCE</div>
            <p style="font-size: 0.7vw; color: var(--text-muted); margin-top: 0.4vw; line-height: 1.45;">
              Human domain corrections are converted into structured Reflexion lessons for the learning layer.
            </p>
          </div>

        </div>

        <!-- Transformation Ribbon -->
        <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(14, 30, 56, 0.8); border: 1px solid rgba(56, 189, 248, 0.25); padding: 0.8vw 1.5vw; border-radius: 0.5vw;">
          <div style="text-align: center;">
            <div style="font-size: 0.7vw; color: var(--text-dim); text-transform: uppercase;">From Problem</div>
            <div style="font-size: 0.9vw; font-weight: 700; color: #EF4444;">Human Fatigue</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1.2vw;">➔</div>
          <div style="text-align: center;">
            <div style="font-size: 0.7vw; color: var(--text-dim); text-transform: uppercase;">Through Control</div>
            <div style="font-size: 0.9vw; font-weight: 700; color: var(--accent-cyan);">Controlled AI</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1.2vw;">➔</div>
          <div style="text-align: center;">
            <div style="font-size: 0.7vw; color: var(--text-dim); text-transform: uppercase;">Through Feedback</div>
            <div style="font-size: 0.9vw; font-weight: 700; color: var(--accent-green);">Learning Signals</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1.2vw;">➔</div>
          <div style="text-align: center;">
            <div style="font-size: 0.7vw; color: var(--text-dim); text-transform: uppercase;">To Scalable Impact</div>
            <div style="font-size: 0.9vw; font-weight: 700; color: #FFFFFF;">More Scalable Operations</div>
          </div>
        </div>

        <div class="takeaway-banner">
          DocuMatch shifts the operational paradigm from brute-force extraction to sustainable trade reliability.
        </div>
      </div>

      <div class="slide-footer">
        <span>Averish Shipping AI — Sustainable Enterprise Scalability</span>
        <span class="footer-quote">Design Ethos: Build software that respects human attention.</span>
      </div>
    </div>


    <!-- =================================================================== -->
    <!-- SLIDE 11: COMPETITIVE STRENGTH -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-11">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Market Differentiation</span>
        </div>
        <div class="header-right">
          <span class="category-label">Capability Matrix</span>
          <span class="slide-number-badge">11 / 12</span>
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
        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(14, 30, 56, 0.9); border: 1px solid var(--accent-cyan); padding: 0.6vw 1.2vw; border-radius: 0.4vw;">
          <div>
            <div style="font-size: 0.65vw; color: var(--accent-cyan); font-weight: 700; text-transform: uppercase;">OUR CORE DIFFERENTIATION</div>
            <div style="font-size: 0.9vw; font-weight: 700; color: #FFFFFF;">“The control + learning layer around AI.”</div>
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
    <!-- SLIDE 12: VISION & FINAL -->
    <!-- =================================================================== -->
    <div class="slide" id="slide-12">
      <div class="slide-header">
        <div class="brand-cluster">
          <div class="brand-logo-icon">🚢</div>
          <span class="brand-title">Averish Shipping AI</span>
          <span class="brand-badge">Mission & Vision</span>
        </div>
        <div class="header-right">
          <span class="category-label">The Future of Trade AI</span>
          <span class="slide-number-badge">12 / 12</span>
        </div>
      </div>

      <div class="slide-body">
        <div class="headline-wrap">
          <div class="headline-pre">The New Standard for Maritime Intelligence</div>
          <h1 class="slide-title">AI that learns from humans,<br>knows its boundaries,<br>and earns the right to act.</h1>
        </div>

        <!-- Complete Architecture Flow -->
        <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.4); padding: 1vw 1.2vw; border-radius: 0.6vw; border: 1px solid rgba(255,255,255,0.1); margin: 0.8vw 0;">
          
          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 01</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: #F8FAFC;">HUMAN EXPERTISE</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 02</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: var(--accent-cyan);">CORRECTION</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 03</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: #A7F3D0;">REFLECTION</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 04</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: var(--accent-cyan);">LEARNING AGENT</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 05</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: #FDE68A;">PROVENANCE</div>
          </div>
          <div style="color: var(--accent-cyan); font-size: 1vw;">➔</div>

          <div style="text-align: center;">
            <div style="font-size: 0.65vw; color: var(--text-dim);">STAGE 06</div>
            <div style="font-size: 0.8vw; font-weight: 700; color: #6EE7B7;">TRUSTWORTHY OPS</div>
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
            <div style="font-size: 1.1vw; font-weight: 800; color: #EF4444;">CONTROL</div>
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

    <span id="slide-indicator" style="font-family: 'JetBrains Mono', monospace; font-size: 0.75vw; color: var(--accent-cyan); font-weight: 600; min-width: 3.5vw; text-align: center;">01 / 12</span>

    <button class="hud-btn" id="next-btn" title="Next Slide (Right Arrow / Space)">Next ▶</button>
    <button class="hud-btn" id="fullscreen-btn" title="Toggle Fullscreen (F)">⛶</button>
  </div>


  <!-- Script for Navigation & Scaled 16:9 Viewport -->
  <script>
    const TOTAL_SLIDES = 12;
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
      indicator.textContent = `${{padded}} / 12`;
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
