# 🚨 Student Drowsiness Detection System: Alert Center Design Specification (Phase D6)

## 1. Executive Summary & Design Objective

Phase D6 establishes the technical design specification, visual notification blueprints, alarm animation keyframes, audio channel status indicators, and telemetry bindings for the **Alert Center** in the **Student Drowsiness Detection System Dashboard**.

The Alert Center serves as the safety notification dispatch panel. It renders current active alert warnings, logs previous historical alerts, tracks alert trigger timestamps, monitors audio channel statuses, and triggers high-visibility visual alarm animations during critical drowsiness events.

As strictly mandated, the **Alert Manager backend (`AlertManager`, `HUDAlertChannel`, `AudioAlertChannel` in `alerts/alert_manager.py`) remains 100% untouched**.

---

## 2. Card Overview & Structural Wireframe

### 2.1 Component Wireframe

```
+-------------------------------------------------------------------+
| [🚨 ICON] Alert Center               [🔊 AUDIBLE]  [ STATUS: ACTIVE ] | <- Header + Controls
+-------------------------------------------------------------------+
|                                                                   |
|   CURRENT ALERT (Triggered at 09:24:14):                          |
|   +-----------------------------------------------------------+   |
|   | ⚠️ STRONG WARNING: High drowsiness detected! Take a break.|   | <- Active Alert Banner
|   | Severity: [ STRONG ]     Channel: HUD + Audio Synthesizer |   |
|   +-----------------------------------------------------------+   |
|                                                                   |
|   PREVIOUS ALERT HISTORY:                                         |
|   +-----------------------------------------------------------+   |
|   | [09:22:05] SUBTLE: Brief EAR dip detected (0.20s).        |   | <- Previous Alert
|   +-----------------------------------------------------------+   |
|                                                                   |
|   AUDIO CHANNEL STATUS:                                           |
|   Audio Synthesizer: [ READY ]          Alarm Cooldown: [ 0.0s ]  | <- Audio Status
+-------------------------------------------------------------------+
```

---

## 3. Current & Previous Alert Display Architecture

### 3.1 Current Alert Banner
* **Alert Message Text**: Displays active HUD notification (e.g., *"Strong warning: High drowsiness detected! Take a break."*).
* **Severity Tag**:
  - `SUBTLE` (Amber Gold `#F59E0B`)
  - `STRONG` (Vivid Orange `#F97316`)
  - `CRITICAL` (Crimson Red `#EF4444` with flashing animation)
* **Alert Trigger Time**: Monospaced timestamp counter (`Alert Time: 09:24:14`) formatted as `HH:MM:SS`.
* **Alert Operational Status**:
  - `ACTIVE` (Red/Orange fill when alert is firing)
  - `STANDBY` (Teal fill `#10B981` when state is nominal)
  - `COOLDOWN` (Blue fill `#38BDF8` when alarm cooldown is active)

### 3.2 Previous Alert History
* **Historical Log Entry**: Records the last triggered alert before the current state:
  `[09:22:05] SUBTLE: Brief EAR dip detected (0.20s).`
* **Clear State Display**: Displays `"No recent alerts. System operating normally."` when no prior alert is recorded.

---

## 4. Visual Alarm Animation Engine

When the system escalates to `HIGHLY_DROWSY` or triggers a `CRITICAL` alert, the Alert Center activates high-visibility CSS alarm keyframe animations:

### 4.1 Alarm Keyframe Animations

```css
/* Critical Alarm Flashing Background */
@keyframes alarm-pulse {
  0% {
    background-color: rgba(239, 68, 68, 0.15);
    box-shadow: 0 0 16px 2px rgba(239, 68, 68, 0.3);
  }
  50% {
    background-color: rgba(239, 68, 68, 0.35);
    box-shadow: 0 0 32px 8px rgba(239, 68, 68, 0.65);
  }
  100% {
    background-color: rgba(239, 68, 68, 0.15);
    box-shadow: 0 0 16px 2px rgba(239, 68, 68, 0.3);
  }
}

/* Active Warning Banner Flash */
.alert-banner-critical {
  animation: alarm-pulse 1.0s infinite ease-in-out;
  border-left: 4px solid #EF4444 !important;
}
```

---

## 5. Audio Controls & Muted Indicator

The Alert Center provides visual tracking of audio channel readiness and mute status:

### 5.1 Muted / Audible Indicator
* **`🔊 AUDIBLE` State**: Green badge (`rgba(16, 185, 129, 0.20)`, Text `#10B981`) indicating audio alerts are active.
* **`🔇 MUTED` State**: Muted badge (`rgba(156, 163, 175, 0.20)`, Text `#9CA3AF`) indicating audio alarms are suppressed or muted in configuration.

### 5.2 Real-Time Audio Status Pills
* **`[ READY ]`**: Audio synthesizer thread ready for playback (`#10B981`).
* **`[ PLAYING BEEP ]`**: Active audible alert sounding (`#EF4444` with pulse animation).
* **`[ COOLDOWN ]`**: Cooldown interval active to prevent sound spam (`#38BDF8`).
* **`[ DISABLED ]`**: Audio channel disabled in configuration (`#6B7280`).

---

## 6. HTML / CSS Component Specifications (`AlertCenterCard.html`)

```html
<div class="telemetry-card alert-center-card" data-alert-state="ACTIVE">
  <!-- Card Header -->
  <div class="card-header">
    <div class="header-title">
      <span class="card-icon">🚨</span>
      <span class="title-text">Alert Center</span>
    </div>
    <div class="header-controls">
      <div class="mute-indicator badge-audible">🔊 AUDIBLE</div>
      <div class="state-badge badge-active">STATUS: ACTIVE</div>
    </div>
  </div>

  <!-- Current Active Alert Banner -->
  <div class="current-alert-section">
    <div class="section-top">
      <span class="section-label">CURRENT ACTIVE ALERT</span>
      <span class="alert-timestamp mono">Triggered at: 09:24:14</span>
    </div>
    <div class="alert-banner alert-banner-strong">
      <div class="alert-icon">⚠️</div>
      <div class="alert-content">
        <p class="alert-message">Strong warning: High drowsiness detected! Take a break.</p>
        <div class="alert-tags">
          <span class="tag tag-strong">STRONG</span>
          <span class="tag tag-channel">HUD + Audio</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Previous Alert History -->
  <div class="previous-alert-section">
    <span class="section-label">PREVIOUS ALERT HISTORY</span>
    <div class="previous-alert-box">
      <span class="prev-time mono">[09:22:05]</span>
      <span class="prev-tag tag-subtle">SUBTLE</span>
      <span class="prev-desc">Brief EAR dip detected (0.20s).</span>
    </div>
  </div>

  <!-- Audio Channel Status Row -->
  <div class="audio-status-footer">
    <div class="audio-stat-item">
      <span class="label">Audio Channel</span>
      <span class="value badge-ready">[ READY ]</span>
    </div>
    <div class="audio-stat-item">
      <span class="label">Alarm Cooldown</span>
      <span class="value mono">0.0s</span>
    </div>
  </div>
</div>
```

---

## 7. CSS Styling Tokens

```css
/* Header Controls */
.header-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mute-indicator {
  padding: 4px 8px;
  border-radius: 6px;
  font-family: var(--font-sans);
  font-size: 10px;
  font-weight: 700;
}

.badge-audible {
  background: rgba(16, 185, 129, 0.18);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.badge-muted {
  background: rgba(156, 163, 175, 0.18);
  color: #9CA3AF;
  border: 1px solid rgba(156, 163, 175, 0.4);
}

/* Alert Banner Styling */
.current-alert-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alert-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(20, 22, 31, 0.8);
  border-left: 4px solid #F97316;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.alert-banner-strong {
  border-left-color: #F97316;
  background: rgba(249, 115, 22, 0.12);
}

.alert-message {
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 600;
  color: #F3F4F6;
  margin: 0 0 6px 0;
}

.alert-tags {
  display: flex;
  gap: 6px;
}

.tag {
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-sans);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}

.tag-strong {
  background: rgba(249, 115, 22, 0.25);
  color: #F97316;
}

.tag-channel {
  background: rgba(56, 189, 248, 0.2);
  color: #38BDF8;
}

/* Previous Alert Box */
.previous-alert-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(20, 22, 31, 0.6);
  border: 1px solid #2E3446;
  font-size: 11px;
}

.prev-time {
  color: #6B7280;
}

.prev-desc {
  color: #9CA3AF;
}

/* Audio Status Footer */
.audio-status-footer {
  display: flex;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.audio-stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.audio-stat-item .label {
  font-family: var(--font-sans);
  font-size: 11px;
  color: #9CA3AF;
}
```

---

## 8. Telemetry Data Binding Matrix

| Backend Telemetry Field Key | Data Type | Target UI Component Slot | Visual Representation |
| :--- | :--- | :--- | :--- |
| `current_message` | `str` | `AlertCenter -> Current Alert Message` | Banner Text |
| `current_severity` | `str` | `AlertCenter -> Severity Tag & Borders` | `SUBTLE`, `STRONG`, `CRITICAL` Tag |
| `last_alert_time` | `float` | `AlertCenter -> Alert Timestamp` | Monospaced Timestamp (`09:24:14`) |
| `previous_message` | `str` | `AlertCenter -> Previous Alert Box` | Historical Log Line |
| `audio_enabled` | `bool` | `AlertCenter -> Muted Indicator` | `🔊 AUDIBLE` / `🔇 MUTED` Badge |
| `audio_status` | `str` | `AlertCenter -> Audio Channel Status` | `[ READY ]` / `[ PLAYING BEEP ]` |

---

## 9. Decoupling & Zero-Backend-Modification Verification

- **Alert Manager Protection**: `AlertManager`, `HUDAlertChannel`, `AudioAlertChannel` (`alerts/alert_manager.py`), cooldown logic, and audio playback threads remain **100% untouched**.
- **Pure Presentational Contract**: The Alert Center strictly reads alert telemetry outputs and maps them visually to notification banners, mute indicators, and alarm animations.
