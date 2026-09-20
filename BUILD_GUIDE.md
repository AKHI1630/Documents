# Build Guide — Linux System Health Monitor

Everything you need to go from an empty laptop to a finished GitHub repo.
Work through it in order.

---

## Step 1 — Get Linux running

**If the laptop is already Linux:** skip to Step 2.

**If it's Windows:** open PowerShell **as Administrator** and run:

```powershell
wsl --install
```

Reboot when it asks. It installs Ubuntu. On first launch it asks you to
create a username and password — pick anything, but remember the password,
you need it for `sudo`.

From then on, search "Ubuntu" in the Start menu to get a Linux terminal.

**If `wsl --install` fails**, virtualization is probably disabled in BIOS.
Search your laptop model + "enable virtualization BIOS".

---

## Step 2 — Install Python and psutil

In the Linux terminal:

```bash
sudo apt update
sudo apt install python3 python3-pip -y
pip3 install psutil
```

Check it worked:

```bash
python3 -c "import psutil; print(psutil.cpu_percent(interval=1))"
```

If it prints a number, you're ready.

### If pip3 gives an "externally-managed-environment" error

Newer Ubuntu blocks system-wide pip installs. Use a virtual environment:

```bash
cd ~/system-health-monitor
python3 -m venv venv
source venv/bin/activate
pip install psutil
```

You'll see `(venv)` appear in your prompt. You need to run
`source venv/bin/activate` each time you open a new terminal in this project.

---

## Step 3 — Create the project

```bash
mkdir ~/system-health-monitor
cd ~/system-health-monitor
nano monitor.py
```

Paste in the contents of `monitor.py`.
Save with **Ctrl+O**, then Enter, then **Ctrl+X** to exit.

Run it:

```bash
python3 monitor.py
```

You should see the full report. Then try:

```bash
python3 monitor.py --watch
```

Ctrl+C to stop.

---

## Step 4 — Prove the alerts work

This is the part worth screenshotting.

**Generate real CPU load.** In a second terminal:

```bash
yes > /dev/null &
```

That pins one CPU core immediately. Now run the monitor — CPU should climb
and flip to `[WARNING]`. On a multi-core machine you may need several:

```bash
yes > /dev/null &
yes > /dev/null &
yes > /dev/null &
```

Stop them all with:

```bash
killall yes
```

**Or lower the threshold.** Change `CPU_THRESHOLD = 80.0` to `5.0`, run,
screenshot, then change it back. Do **not** commit it with the low value.

Take two screenshots: one healthy, one with the warning showing.

---

## Step 5 — Automate it with cron

This is what makes the word "automated" on your resume true.

First, create a log directory:

```bash
mkdir -p ~/system-health-monitor/logs
```

Open the cron table:

```bash
crontab -e
```

(If it asks which editor, pick nano — usually option 1.)

Add this line at the bottom:

```
*/10 * * * * /usr/bin/python3 /home/YOUR_USERNAME/system-health-monitor/monitor.py >> /home/YOUR_USERNAME/system-health-monitor/logs/health.log 2>&1
```

Replace `YOUR_USERNAME` with your actual username (run `whoami` if unsure).

Save and exit. Verify it's registered:

```bash
crontab -l
```

**What that line means** — worth knowing, they may ask:

```
*/10  *     *     *     *
 │    │     │     │     │
 │    │     │     │     └── day of week (0-6)
 │    │     │     └──────── month (1-12)
 │    │     └────────────── day of month (1-31)
 │    └──────────────────── hour (0-23)
 └───────────────────────── minute — */10 means "every 10 minutes"
```

`>>` appends output to the log file. `2>&1` sends error messages to the
same place, so failures get logged instead of vanishing.

Wait 10 minutes, then:

```bash
cat ~/system-health-monitor/logs/health.log
```

You should see reports stacking up. Screenshot that too — it's your proof
of automation.

**Note:** cron doesn't run in WSL by default. Start it with
`sudo service cron start`. It stops when you close WSL, which is fine for
a demo — just mention that if it comes up.

---

## Step 6 — Push to GitHub

Set up git (first time only):

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

Create a `.gitignore` so junk doesn't get committed:

```bash
nano .gitignore
```

Put this in it:

```
venv/
__pycache__/
logs/
*.pyc
```

Then:

```bash
git init
git add monitor.py .gitignore
git commit -m "Add CPU, memory and disk monitoring with thresholds"
```

**Make several commits, not one.** If you build it in stages, commit after
each one. A history of 8–15 commits looks like someone building something;
one commit called "project" looks like something downloaded.

Then on github.com: create a new repository (don't tick "add README",
you'll add your own), and follow the commands it shows you — they'll look
like:

```bash
git remote add origin https://github.com/YOURNAME/system-health-monitor.git
git branch -M main
git push -u origin main
```

GitHub will ask for a **Personal Access Token**, not your password.
Generate one at: Settings → Developer settings → Personal access tokens →
Tokens (classic) → Generate new token → tick `repo`. Copy it somewhere
safe, it's shown only once.

---

## Step 7 — Write the README

Create `README.md` in the project folder. Template below — fill in the
blanks and add your screenshots.

```markdown
# Linux System Health Monitor

A lightweight command-line utility that reports CPU, memory, disk,
uptime, top processes and network connectivity on a Linux host, with
configurable warning thresholds.

## Sample output

[screenshot of healthy output]

When a threshold is breached:

[screenshot of warning output]

## Why

Production monitoring stacks like Prometheus or Nagios solve this
properly. I built this to understand what those tools actually read
underneath, and to have something agent-free I can drop onto a box
and run immediately.

## Requirements

- Python 3.8+
- psutil

## Install and run

    git clone https://github.com/YOURNAME/system-health-monitor.git
    cd system-health-monitor
    pip3 install -r requirements.txt
    python3 monitor.py

Watch mode, refreshing every 5 seconds:

    python3 monitor.py --watch

## Configuration

Thresholds are set at the top of `monitor.py`:

| Setting            | Default | Meaning                        |
|--------------------|---------|--------------------------------|
| `CPU_THRESHOLD`    | 80%     | Warn above this CPU usage      |
| `MEMORY_THRESHOLD` | 80%     | Warn above this memory usage   |
| `DISK_THRESHOLD`   | 85%     | Warn above this disk usage     |
| `DISK_PATH`        | `/`     | Filesystem to check            |

## Scheduled runs

Runs every 10 minutes via cron, appending to a log file:

    */10 * * * * /usr/bin/python3 /path/to/monitor.py >> /path/to/logs/health.log 2>&1

## Notes and limitations

- Inside a container, psutil reports host memory rather than the
  cgroup limit, so figures would be misleading there.
- Alerts print to the terminal; there is no notification channel yet.
- No historical data — each run is a point-in-time snapshot.

## Next steps

- Log to SQLite so trends can be queried over time
- Email or webhook alerts
- Run as a systemd service with a timer instead of cron
- cgroup-aware memory reporting for containerised hosts
```

Also create a `requirements.txt` — one line:

```
psutil
```

Commit both:

```bash
git add README.md requirements.txt
git commit -m "Add README and requirements"
git push
```

---

## Step 8 — Check your resume matches

Read your bullets against what the code now does:

- CPU, memory, disk utilization — yes
- system uptime — yes
- running processes — yes
- network connectivity — yes
- threshold-based health checks and alerts — yes
- automated diagnostics — yes, via cron
- structured terminal reports — yes

If you skip Step 5, change "Automated" to "Scripted" on your resume.
Don't leave a claim the code doesn't support.

---

## If something breaks

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'psutil'` | `pip3 install psutil` — or activate your venv |
| `python3: command not found` | `sudo apt install python3` |
| `externally-managed-environment` | Use the venv method in Step 2 |
| `Permission denied` on the log file | Check the path in your crontab line is correct and the `logs/` folder exists |
| Cron never runs (WSL) | `sudo service cron start` |
| Network always shows unreachable | Corporate firewall blocking port 53 — try `NETWORK_TEST_HOST = "1.1.1.1"` or switch to a `ping` check |
