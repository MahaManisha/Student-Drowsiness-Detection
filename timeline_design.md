# 📜 Student Drowsiness Detection System: Event Timeline Design Specification (Phase D8)

## 1. Executive Summary & Design Objective

Phase D8 establishes the technical design specification, component blueprints, vertical spine node geometry, color-coded event tags, and telemetry bindings for the **Event Timeline Component** in the **Student Drowsiness Detection System Dashboard**.

The Event Timeline acts as a real-time chronological log stream, capturing and displaying critical session milestones (session startup, valid blinks, yawns, alert escalations, and alert recoveries) in a scrollable, high-density stream panel.

As strictly mandated, the **Session Logger backend (`SessionLogger` in `logging/session_logger.py`) and JSON Lines log file handlers remain 100% untouched**.

---

## 2. Component Overview & Structural Wireframe

### 2.1 Component Wireframe

```
+-------------------------------------------------------------------+
| 📜 EVENT TIMELINE                                [ STREAM ACTIVE ]|
+-------------------------------------------------------------------+
|  |                                                                |
| (🚀) [09:24:00] SYSTEM: Session monitoring initialized.           |  <- Monitoring Started
|  |   Details: Camera ID: 0 (1280x720 @ 30.0 FPS)                 |
|  |                                                                |
| (👁️) [09:24:12] TELEMETRY: Eye blink detected (#142).             |  <- Blink Detected
|  |   Details: Avg EAR: 0.19 (Duration: 0.18s)                    |
|  |                                                                |
| (👄) [09:24:18] TELEMETRY: Yawn event completed (#2).             |  <- Yawn Detected
|  |   Details: MAR: 0.62 (Duration: 2.10s)                        |
|  |                                                                |
| (🚨) [09:24:25] ALERT: Strong drowsiness alarm triggered!         |  <- Alert Triggered
|  |   Details: Score: 68/100 | State: DROWSY | Channels: HUD+Audio |
|  |                                                                |
| (🛡️) [09:24:35] RECOVERY: Alert state cleared. Return to ALERT.   |  <- Alert Cleared
|  |   Details: Score: 12/100 | Duration: 10.0s                      |
|  v                                                                |
+-------------------------------------------------------------------+
```

---

## 3. Vertical Timeline Spine & Node Architecture

The Event Timeline uses a continuous vertical line (spine) connecting circular event node badges.

### 3.1 Timeline Spine Geometry
* **Vertical Connector Line**: `width: 2px`, `background: #2E3446`, aligned vertically along the node centers ($X = 16\text{px}$).
* **Node Icon Circle**: $24\times 24\text{px}$ circular badge (`border-radius: 50%`) centered on the spine line.
* **Node Padding & Gap**: `margin-bottom: 16px` between consecutive timeline items.

```
       Spine (2px)
           |
         ( 🚀 )  Node 1: Monitoring Started
           |
           |
         ( 👁️ )  Node 2: Blink Detected
           |
           |
         ( 👄 )  Node 3: Yawn Detected
           |
           |
         ( 🚨 )  Node 4: Alert Triggered
           |
           |
         ( 🛡️ )  Node 5: Alert Cleared
           |
```

---

## 4. Required Event Types & Color Coding Specifications

| Event Type | Event Key | Node Icon | Accent Color | Hex Token | Event Description Format |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Monitoring Started** | `MONITORING_STARTED` | `🚀` | System Blue | `#38BDF8` | Session monitoring initialized (1280x720 @ 30 FPS). |
| **Blink Detected** | `BLINK_DETECTED` | `👁️` | Teal Green | `#10B981` | Valid eye blink detected (Avg EAR: 0.19, Duration: 0.18s). |
| **Yawn Detected** | `YAWN_DETECTED` | `👄` | Yawn Magenta| `#EC4899` | Complete yawn event logged (MAR: 0.62, Duration: 2.10s). |
| **Alert Triggered** | `ALERT_TRIGGERED` | `🚨` | Alert Crimson| `#EF4444` | Strong drowsiness alarm triggered (Score: 68, State: DROWSY).|
| **Alert Cleared** | `ALERT_CLEARED` | `🛡️` | Recovery Mint| `#10B981` | Alert state cleared. Return to ALERT (Score: 12). |

---

## 5. Timestamp & Monospaced Typography Standards

To guarantee high readability for session audits, all timestamps and log metadata follow strict typography rules:

* **Timestamp Format**: Monospaced timestamp (`09:24:15` formatted in `JetBrains Mono`, Color `#9CA3AF`).
* **Event Type Tag**: `11px` Bold uppercase tag (`SYSTEM`, `TELEMETRY`, `ALERT`, `RECOVERY`).
* **Log Description**: `12px` Regular sans-serif font (`Inter`, Color `#F3F4F6`).
* **Sub-Details Payload**: `11px` Monospaced muted metadata line (`Details: Score: 68/100 | State: DROWSY`).

---

## 6. Scrollable Panel & Custom Dark Scrollbar

The timeline panel is contained within a fixed-height scrollable viewport that automatically scrolls to the newest log entries.

```css
.timeline-scroll-panel {
  max-height: 240px;
  overflow-y: auto;
  padding-right: 8px;
  scroll-behavior: smooth;
}

/* Custom Sleek Dark Scrollbar */
.timeline-scroll-panel::-webkit-scrollbar {
  width: 6px;
}

.timeline-scroll-panel::-webkit-scrollbar-track {
  background: #14161F;
  border-radius: 4px;
}

.timeline-scroll-panel::-webkit-scrollbar-thumb {
  background: #2E3446;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.timeline-scroll-panel::-webkit-scrollbar-thumb:hover {
  background: #454E69;
}
```

---

## 7. HTML / CSS Component Specifications (`EventTimelinePanel.html`)

```html
<div class="telemetry-card timeline-card">
  <!-- Card Header -->
  <div class="card-header">
    <div class="header-title">
      <span class="card-icon">📜</span>
      <span class="title-text">Event Timeline</span>
    </div>
    <div class="state-badge badge-stream">STREAM ACTIVE</div>
  </div>

  <!-- Scrollable Timeline Stream Panel -->
  <div class="timeline-scroll-panel">
    <div class="timeline-container">
      <!-- Vertical Continuous Spine Line -->
      <div class="timeline-spine"></div>

      <!-- Item 1: Monitoring Started -->
      <div class="timeline-item type-system">
        <div class="timeline-node node-blue">🚀</div>
        <div class="timeline-content">
          <div class="timeline-meta">
            <span class="time mono">[09:24:00]</span>
            <span class="tag tag-system">SYSTEM</span>
          </div>
          <p class="timeline-text">Session monitoring initialized.</p>
          <div class="timeline-payload mono">Camera ID: 0 (1280x720 @ 30.0 FPS)</div>
        </div>
      </div>

      <!-- Item 2: Blink Detected -->
      <div class="timeline-item type-telemetry">
        <div class="timeline-node node-teal">👁️</div>
        <div class="timeline-content">
          <div class="timeline-meta">
            <span class="time mono">[09:24:12]</span>
            <span class="tag tag-telemetry">TELEMETRY</span>
          </div>
          <p class="timeline-text">Eye blink detected (#142).</p>
          <div class="timeline-payload mono">Avg EAR: 0.19 | Duration: 0.18s</div>
        </div>
      </div>

      <!-- Item 3: Yawn Detected -->
      <div class="timeline-item type-telemetry">
        <div class="timeline-node node-magenta">👄</div>
        <div class="timeline-content">
          <div class="timeline-meta">
            <span class="time mono">[09:24:18]</span>
            <span class="tag tag-magenta">YAWN</span>
          </div>
          <p class="timeline-text">Yawn event completed (#2).</p>
          <div class="timeline-payload mono">MAR: 0.62 | Duration: 2.10s</div>
        </div>
      </div>

      <!-- Item 4: Alert Triggered -->
      <div class="timeline-item type-alert">
        <div class="timeline-node node-crimson">🚨</div>
        <div class="timeline-content">
          <div class="timeline-meta">
            <span class="time mono">[09:24:25]</span>
            <span class="tag tag-alert">ALERT TRIGGERED</span>
          </div>
          <p class="timeline-text text-alert">Strong drowsiness alarm triggered!</p>
          <div class="timeline-payload mono">Score: 68/100 | State: DROWSY</div>
        </div>
      </div>

      <!-- Item 5: Alert Cleared -->
      <div class="timeline-item type-recovery">
        <div class="timeline-node node-mint">🛡️</div>
        <div class="timeline-content">
          <div class="timeline-meta">
            <span class="time mono">[09:24:35]</span>
            <span class="tag tag-recovery">ALERT CLEARED</span>
          </div>
          <p class="timeline-text">Alert state cleared. Return to ALERT.</p>
          <div class="timeline-payload mono">Score: 12/100 | Duration: 10.0s</div>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

## 8. CSS Styling Rules

```css
.timeline-card {
  background: rgba(26, 29, 40, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid #2E3446;
  border-radius: 12px;
  padding: 16px;
}

.timeline-container {
  position: relative;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-spine {
  position: absolute;
  left: 11px;
  top: 12px;
  bottom: 12px;
  width: 2px;
  background-color: #2E3446;
  z-index: 1;
}

.timeline-item {
  position: relative;
  display: flex;
  gap: 12px;
  z-index: 2;
}

.timeline-node {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.5);
}

.node-blue    { background: #0284C7; color: #FFFFFF; }
.node-teal    { background: #059669; color: #FFFFFF; }
.node-magenta { background: #DB2777; color: #FFFFFF; }
.node-crimson { background: #DC2626; color: #FFFFFF; animation: pulse-node 1.2s infinite; }
.node-mint    { background: #10B981; color: #FFFFFF; }

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.timeline-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.timeline-meta .time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: #9CA3AF;
}

.timeline-text {
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 500;
  color: #F3F4F6;
  margin: 0;
}

.timeline-payload {
  font-family: var(--font-mono);
  font-size: 11px;
  color: #6B7280;
}
```

---

## 9. Telemetry Data Binding Matrix

| Backend Telemetry Log Field | Data Type | Target UI Timeline Slot | Rendering Format |
| :--- | :--- | :--- | :--- |
| `timestamp` | `str` | `TimelineItem -> Monospaced Time` | `[09:24:15]` |
| `event_type` | `str` | `TimelineItem -> Event Node & Tag` | Node Icon + Accent Tag |
| `state` | `str` | `TimelineItem -> Description & Payload`| State Name (`DROWSY`) |
| `score` | `float` | `TimelineItem -> Payload String` | Score Readout (`68/100`) |
| `duration` | `float` | `TimelineItem -> Payload String` | Duration Text (`0.18s`) |

---

## 10. Decoupling & Zero-Backend-Modification Verification

- **Session Logger Protection**: `SessionLogger` (`logging/session_logger.py`), JSON Lines serialization formats, file writing locks, and timestamps remain **100% untouched**.
- **Pure Presentational Contract**: The Event Timeline component acts purely as a visual consumer of structured session log events.
