# 🎨 Student Drowsiness Detection System: Dashboard Design Theme (Phase D1)

## 1. Executive Summary & Design System Architecture

The **Dashboard Design Theme** establishes a modern, high-contrast **Sleek Dark Mode Design System** tailored for mission-critical real-time telemetry monitoring. The design prioritizes visual clarity, cognitive efficiency, immediate state recognition, and long-session ergonomic comfort.

---

## 2. Color Palette Specification

### 2.1 Core Dark Mode Surfaces & Structural Tokens

| Token Name | Hex Code | RGB / HSL | Application Scope |
| :--- | :--- | :--- | :--- |
| `--bg-base` | `#0D0E12` | `rgb(13, 14, 18)` | Full application outer body background |
| `--bg-surface-primary` | `#14161F` | `rgb(20, 22, 31)` | Dashboard container & glass backdrop layer |
| `--bg-card` | `#1A1D28` | `rgb(26, 29, 40)` | Telemetry card surface background |
| `--bg-card-header` | `#222634` | `rgb(34, 38, 52)` | Card top header strip background |
| `--bg-input-track` | `#2A2F40` | `rgb(42, 47, 64)` | Progress bar background track |
| `--border-subtle` | `#2E3446` | `rgb(46, 52, 70)` | Standard card borders & panel dividers |
| `--border-active` | `#454E69` | `rgb(69, 78, 105)` | Focused card border & active container stroke |

### 2.2 Text & Content Hierarchy Tokens

| Token Name | Hex Code | Opacity | Application Scope |
| :--- | :--- | :--- | :--- |
| `--text-primary` | `#F3F4F6` | `100%` | Primary titles, critical readouts, state text |
| `--text-secondary` | `#9CA3AF` | `85%` | Secondary labels, progress values, sub-headers |
| `--text-muted` | `#6B7280` | `65%` | Captions, non-critical metrics, log timestamps |
| `--text-accent` | `#38BDF8` | `100%` | Interactive links, latched badges, highlight text |

### 2.3 State-Based Severity Accent Palette

The visualizer dynamically shifts element accents, status pills, progress fill bars, and active borders according to four core evaluation states:

```
[ ALERT / NORMAL ] ----> [ SLIGHTLY DROWSY ] ----> [ DROWSY ] ----> [ HIGHLY DROWSY (CRITICAL) ]
  Mint Teal (#10B981)      Warm Amber (#F59E0B)    Vivid Orange (#F97316)  Crimson Red (#EF4444)
```

| Drowsiness State | Hex Code | RGB Values | Semantic Meaning | Visual Indicator |
| :--- | :--- | :--- | :--- | :--- |
| **`ALERT` (Normal)** | `#10B981` | `rgb(16, 185, 129)` | Student fully attentive, metrics within nominal bounds | Solid Mint Teal Pill Badge |
| **`SLIGHTLY DROWSY`** | `#F59E0B` | `rgb(245, 158, 11)` | Minor EAR dip or slight yawn detected | Solid Amber Gold Pill Badge |
| **`DROWSY`** | `#F97316` | `rgb(249, 115, 22)` | Extended closure or repeated yawning detected | Solid Deep Orange Pill Badge |
| **`HIGHLY DROWSY`** | `#EF4444` | `rgb(239, 68, 68)` | Critical drowsiness threshold breach; action required | Pulsing Crimson Red Pill Badge |

---

## 3. Typography System

The dashboard utilizes a dual-font typographic stack: a clean modern sans-serif for UI labels and layout hierarchy, combined with an ultra-legible monospaced font for telemetry numbers, formulas, and log streams.

### 3.1 Font Stack Definitions
* **Primary UI Font Family (`--font-sans`)**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `sans-serif`.
* **Telemetry Monospaced Font (`--font-mono`)**: `"JetBrains Mono"`, `"Fira Code"`, `"Roboto Mono"`, `Consolas`, `monospace`.

### 3.2 Type Scale & Hierarchy

| Element | Class / Token | Font Size | Weight | Line Height | Font Family |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Main Header Title** | `.title-header` | `18px` | `700` (Bold) | `24px` | `--font-sans` |
| **Card Header Title** | `.card-title` | `14px` | `600` (SemiBold)| `20px` | `--font-sans` |
| **Primary Telemetry Readout**|`.metric-large` | `24px` | `700` (Bold) | `28px` | `--font-mono` |
| **Secondary Telemetry Value**|`.metric-medium`| `15px` | `600` (SemiBold)| `20px` | `--font-mono` |
| **Field Labels** | `.label-standard`| `12px` | `500` (Medium) | `16px` | `--font-sans` |
| **Log Feed Stream** | `.log-line` | `11px` | `400` (Regular)| `16px` | `--font-mono` |
| **Status Pill Badges** | `.badge-text` | `11px` | `700` (Bold) | `14px` | `--font-sans` |

---

## 4. Spacing & Spatial Grid Architecture

The system strictly adheres to an **8pt Spatial Grid System** (`4px`, `8px`, `12px`, `16px`, `24px`, `32px`) to ensure spatial harmony and grid alignment.

```
Outer App Container Margin:  16px
Main CSS Grid Gap:           16px
Card Internal Padding:       16px
Card Header Strip Height:    36px
Sub-component Gap:           12px
Element Micro Gap:           8px
```

---

## 5. Border Radii & Geometry Scale

Rounded corners are systematically defined across component layers to convey modern, software-grade refinement.

| Token | Pixel Value | Application Target |
| :--- | :--- | :--- |
| `--radius-container` | `16px` | Dashboard main outer frame & Live Camera Viewport |
| `--radius-card` | `12px` | Standard telemetry cards (Eye, Mouth, Pose, Decision, Timeline) |
| `--radius-inner` | `8px` | Reticle box, inner text boxes, event log container |
| `--radius-track` | `6px` | Progress bar tracks and fill meters |
| `--radius-pill` | `9999px` | Dynamic status pill badges & camera HUD badges |

---

## 6. Shadows, Elevation & Glassmorphism

To establish visual separation between layered telemetry components, the theme employs subtle glassmorphic backdrop filters and multi-layered drop shadows.

### 6.1 Elevation Shadow Tokens
* **Standard Card Elevation (`--shadow-card`)**:
  `0 8px 24px -4px rgba(0, 0, 0, 0.4), 0 2px 6px -1px rgba(0, 0, 0, 0.3)`
* **Active Viewport Elevation (`--shadow-active`)**:
  `0 12px 32px -6px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.08)`
* **Critical Alert Glow Effect (`--shadow-critical`)**:
  `0 0 24px 4px rgba(239, 68, 68, 0.45)`

### 6.2 Glassmorphism Specification
Cards and header bars overlaying video layers utilize translucent backdrop blurring:
```css
background: rgba(26, 29, 40, 0.85);
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
border: 1px solid rgba(255, 255, 255, 0.08);
```

---

## 7. Micro-Animations & State Transitions

1. **Pill Badge State Transition**: Smooth color transition when state escalates (`transition: background-color 0.3s ease, border-color 0.3s ease`).
2. **Progress Bar Fill Interpolation**: Progress gauge fills update smoothly without step jitter (`transition: width 0.15s ease-out`).
3. **Critical Alert Pulsing Keyframes**:
   ```css
   @keyframes pulse-critical {
     0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
     70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
     100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
   }
   ```
