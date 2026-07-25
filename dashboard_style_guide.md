# 🎨 Student Drowsiness Detection System: Master UI/UX Design System & Style Guide

## 1. Executive Summary & Design System Philosophy

The **Dashboard Design System & Style Guide** serves as the authoritative visual specification for the **Student Drowsiness Detection System Dashboard**.

Built for mission-critical real-time telemetry monitoring, the design system prioritizes:
1. **Ergonomic Ergonomics**: Low-eyestrain dark background palettes (`#0D0E12`, `#14161F`, `#1A1D28`).
2. **Instant Cognitive Recognition**: High-contrast, state-based severity color coding (`ALERT` Teal, `DROWSY` Orange, `CRITICAL` Crimson).
3. **Typographic Rigor**: Dual-font stack pairing `Inter` (UI labels) and `JetBrains Mono` (numerical telemetry).
4. **Spatial Geometry**: Enforced 8pt spatial grid system and unified corner radius scales.

---

## 2. Color Palette & State Tokens

### 2.1 Surfaces & Backgrounds

```css
:root {
  /* Surface Tokens */
  --bg-base:             #0D0E12; /* Main application background */
  --bg-surface:          #14161F; /* Main grid container surface */
  --bg-card:             rgba(26, 29, 40, 0.85); /* Card surface with glass blur */
  --bg-header-strip:     #222634; /* Card top title strip */
  --bg-track:            #2A2F40; /* Progress gauge track background */

  /* Border Tokens */
  --border-subtle:       #2E3446; /* Card border stroke */
  --border-active:       #454E69; /* Focused/hover card border stroke */
  --border-glass:        rgba(255, 255, 255, 0.08); /* Translucent glass stroke */
}
```

### 2.2 State-Based Severity Accent Palette

| State Token | Hex Code | RGB Value | Visual Scope & Application |
| :--- | :--- | :--- | :--- |
| `--color-alert` | `#10B981` | `rgb(16, 185, 129)` | Nominal state, open eyes, closed mouth, nominal posture |
| `--color-slightly`| `#F59E0B` | `rgb(245, 158, 11)` | Cautionary state, minor EAR dip, slight head turn |
| `--color-drowsy` | `#F97316` | `rgb(249, 115, 22)` | High risk state, extended eye closure, yawning |
| `--color-critical`| `#EF4444` | `rgb(239, 68, 68)` | Critical state, alarm escalation, flashing pulses |
| `--color-cyan` | `#38BDF8` | `rgb(56, 189, 248)` | Nominal ratio averages, system tags, confidence fill |

---

## 3. Typography System

The interface pairs a clean sans-serif UI font with an ultra-legible monospaced font for telemetry values:

```css
:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Roboto Mono', Consolas, monospace;
}
```

### 3.1 Typographic Scale

```css
/* Sans-Serif UI Hierarchy */
.title-app      { font-family: var(--font-sans); font-size: 18px; font-weight: 700; color: #F3F4F6; }
.title-card     { font-family: var(--font-sans); font-size: 14px; font-weight: 700; color: #F3F4F6; }
.label-standard { font-family: var(--font-sans); font-size: 12px; font-weight: 500; color: #9CA3AF; }
.label-caption  { font-family: var(--font-sans); font-size: 11px; font-weight: 400; color: #6B7280; }

/* Monospaced Telemetry Scale */
.mono-xl        { font-family: var(--font-mono); font-size: 28px; font-weight: 800; color: #F3F4F6; }
.mono-lg        { font-family: var(--font-mono); font-size: 24px; font-weight: 800; color: #F3F4F6; }
.mono-md        { font-family: var(--font-mono); font-size: 15px; font-weight: 600; color: #F3F4F6; }
.mono-sm        { font-family: var(--font-mono); font-size: 12px; font-weight: 500; color: #9CA3AF; }
```

---

## 4. Spacing & Spatial Grid Architecture

All margins, paddings, and grid gaps adhere to an **8pt Spatial Grid**:

```css
:root {
  --space-1: 4px;   /* Micro element gap */
  --space-2: 8px;   /* Sub-widget gap & badge margin */
  --space-3: 12px;  /* Vertical inner card row gap */
  --space-4: 16px;  /* Card padding & grid container gap */
  --space-5: 24px;  /* Main header padding */
  --space-6: 32px;  /* Major section separation */
}
```

---

## 5. Border Radii & Geometry Scale

Corners are systematically rounded across component layers:

```css
:root {
  --radius-container: 16px;  /* Main outer application container & camera viewport */
  --radius-card:      12px;  /* Telemetry cards (Eye, Mouth, Pose, Decision, Alerts, Stats, Timeline) */
  --radius-inner:     8px;   /* Reticle box, inner text boxes, event log container */
  --radius-track:     6px;   /* Progress bar tracks and fill meters */
  --radius-pill:      9999px;/* Dynamic status pill badges & camera HUD badges */
}
```

---

## 6. Shadows, Elevation & Glassmorphism

```css
/* Depth Elevation Tokens */
:root {
  --shadow-card:   0 8px 24px -4px rgba(0, 0, 0, 0.4), 0 2px 6px -1px rgba(0, 0, 0, 0.3);
  --shadow-active: 0 14px 32px -6px rgba(0, 0, 0, 0.55), 0 4px 10px -2px rgba(0, 0, 0, 0.4);
  --shadow-glow:   0 0 24px 4px rgba(239, 68, 68, 0.45);
}

/* Glassmorphism Blur Token */
.glass-surface {
  background: rgba(26, 29, 40, 0.85);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
```

---

## 7. Vector Icon Taxonomy

| Dashboard Panel | Icon | Vector Unicode / Class | Color Spec |
| :--- | :--- | :--- | :--- |
| **System Header** | `🛡️` | Shield Symbol | Mint Teal `#10B981` |
| **Eye Analysis** | `👁️` | Ocular Symbol | Emerald `#10B981` |
| **Mouth Analysis** | `👄` | Oral Symbol | Teal `#10B981` / Magenta `#EC4899` |
| **Head Pose** | `👤` | Portrait Symbol | Slate White `#F3F4F6` |
| **Decision Engine** | `🧠` | Brain Symbol | Cyan `#38BDF8` |
| **Alert Center** | `🚨` | Alarm Symbol | Crimson Red `#EF4444` |
| **Session Statistics** | `📈` | Chart Symbol | Cyan `#38BDF8` |
| **Event Timeline** | `📜` | Scroll Symbol | Slate White `#F3F4F6` |

---

## 8. Micro-Animation Keyframe Specifications

```css
/* 1. Viewport & Card Entry Fade-In */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 2. Critical Alert Pulse Glow */
@keyframes pulseGlow {
  0%   { box-shadow: 0 0 12px 2px rgba(239, 68, 68, 0.3); border-color: rgba(239, 68, 68, 0.5); }
  50%  { box-shadow: 0 0 28px 6px rgba(239, 68, 68, 0.65); border-color: rgba(239, 68, 68, 0.9); }
  100% { box-shadow: 0 0 12px 2px rgba(239, 68, 68, 0.3); border-color: rgba(239, 68, 68, 0.5); }
}

/* 3. Progress Meter Fill Shimmer */
@keyframes progressShimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```
