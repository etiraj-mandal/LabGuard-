# LabGuard Pro | Advanced Client-Server Terminal Monitor

LabGuard Pro is a robust, real-time computer lab management and cybersecurity enforcement system designed for academic institutions and corporate environments. Built with a decoupled client-server architecture, the system provides administrators with a centralized web dashboard to monitor hardware resource metrics and instantly enforce application-blocking and web-filtering policies across distributed network nodes.

## 🚀 Key Features

* **Real-Time Terminal Monitoring:** Dynamically tracks active client nodes, capturing hostnames, real-time CPU utilization, and RAM allocation metrics.
* **Automated Threat & Violation Enforcement:** Continuously audits client process trees. Instantly terminates unauthorized applications (`.exe`) and forces target window closure upon detecting blacklisted browser keywords (e.g., streaming, gaming, or social media handles).
* **Two-Tier Compliance Logic:** Implements a graceful enforcement policy. The first infraction displays a transient system warning; a secondary breach activates an uncompromising, full-screen hardware lock overlay.
* **Centralized Security Orchestration:** Administrators can monitor violations globally from a live-updating Flask dashboard and issue encrypted remote unlock clearances to restore hijacked student terminals.
* **Self-Healing Database Initialization:** Features automated schema execution that dynamically provisions relational MySQL tables (`pc_logs`, `violation_history`) upon backend boot.

## 🛠️ Tech Stack

* **Backend / Server Architecture:** Python, Flask, MySQL, MySQL-Connector
* **Client Monitoring & Automation:** Python, `psutil` (Process Management), `pygetwindow` (OS Window Automation), `requests`
* **Frontend Interface:** Responsive HTML5, CSS3 (Glassmorphism UI, Dark/Light Mode Engine), JavaScript (Asynchronous Polling)
* **GUI Subsystem:** Tkinter (Custom OS-level security overlay)

---

## 🏗️ System Architecture

```text
  [ Student Client Node ]                               [ Admin Control Server ]
  +-------------------------+                           +------------------------+
  |  - Process Auditor      | -- HTTP POST (Metrics) -> |  - Flask Core Engine   |
  |  - Active Window Closer |                           |  - Dashboard View Engine|
  |  - Security Lock UI     | <- HTTP GET (Pin/State) - |  - MySQL Schema Matrix |
  +-------------------------+                           +------------------------+
