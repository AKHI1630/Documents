# Interview Prep — System Health Monitor

Read this the night before. Say the answers out loud once; reading
silently doesn't build the same fluency.

---

## The opener: "Walk me through your project"

Keep it to 30 seconds. They'll follow up on whatever interests them.

> It's a command-line tool that checks a Linux host's CPU, memory,
> disk, uptime, top processes and network reachability, compares each
> against a configurable threshold, and prints a report. I set it to
> run every ten minutes via cron and append to a log file, so there's a
> record rather than just a live view. I wrote it with Python and
> psutil. It's deliberately small — I built it to learn how Linux
> exposes these metrics.

That last sentence matters. It sets expectations honestly and stops
them probing for sophistication that isn't there.

---

## Questions about the code

**Why psutil instead of parsing `/proc` yourself?**
psutil handles the parsing and works across platforms. The data mostly
comes from `/proc` either way — `/proc/stat` for CPU, `/proc/meminfo`
for memory. I used the library to focus on the logic rather than
text parsing.

**What does `cpu_percent(interval=1)` actually do?**
CPU usage is a rate, not a state. It samples CPU time counters, waits a
second, samples again, and reports the difference as a percentage. If
you call it with no interval, the first call has nothing to compare
against and returns 0.0 — a classic bug.

**Why did you pick 80%?**
It's a common default and it's configurable at the top of the file. In
a real environment you'd tune it per host — a database box sitting at
85% memory might be perfectly healthy, while the same on an app server
could mean a leak.

**What's `if __name__ == "__main__"` for?**
It means the code below only runs when the file is executed directly,
not when it's imported. So the functions can be reused elsewhere
without the report printing as a side effect.

**Why do you catch `NoSuchProcess` and `AccessDenied`?**
Processes can exit while you're iterating over them, and some belong to
other users. Without that catch the script crashes on a busy system.

**Why connect to 8.8.8.8 rather than pinging a domain?**
Using an IP tests connectivity without involving DNS. If I resolved a
hostname, a broken DNS server would look identical to a dead network.
Those are different problems with different fixes.

---

## The question that separates candidates

**"Why not just use top, or Nagios, or Prometheus?"**

Don't get defensive, and don't claim you built something better.

> Those are what I'd use in production. I built this to understand what
> they're reading underneath — which is mostly `/proc`. It's also
> agent-free, so it runs on a box with nothing installed, which is
> occasionally useful for a quick check.

Showing you know the real tools exist is worth more than the project.

---

## "What would you add next?"

Have three ready:

1. **Persistence** — log to SQLite so I can answer "was this high an
   hour ago?" instead of only "is it high now?"
2. **Alert hysteresis** — only fire after several consecutive breaches,
   and don't re-alert every run. Alert fatigue is a real operational
   problem.
3. **systemd service and timer** instead of cron — it's what modern
   distros use, and it gives proper logging through journald.

---

## "What are its limitations?"

Volunteering these makes you look more credible, not less.

- Inside a container, psutil reports host memory, not the cgroup limit,
  so the numbers would be wrong there.
- No history — every run is a snapshot.
- Alerts only print to the terminal; nothing is notified.
- Single host only; it doesn't aggregate across machines.

---

## Linux fundamentals they'll likely ask

A sysadmin interview leans on these more than on Python. Your project
is a natural doorway into all of them.

**What's in `/proc`?**
A virtual filesystem — not real files on disk. The kernel exposes
process and system information through it. `/proc/stat` has CPU
counters, `/proc/meminfo` memory, `/proc/uptime` uptime, and each
running process gets a numbered directory.

**What does load average mean?**
The average number of processes running or waiting to run, over 1, 5
and 15 minutes. It's relative to core count — a load of 4.0 is fine on
an 8-core machine and bad on a 2-core one. Unlike most systems, Linux
also counts processes blocked on I/O, so high load can mean slow disk
rather than busy CPU.

**`df` vs `du`?**
`df` asks the filesystem how much space it reports free. `du` adds up
file sizes in a directory tree. They disagree when a deleted file is
still held open by a running process — the space isn't freed until the
process closes it. That's a classic "disk full but I can't find
anything" situation; `lsof | grep deleted` finds it.

**Disk is full. What do you do?**
`df -h` to find which filesystem. `du -sh /*` then walk down into the
biggest directory. Usually logs — check `/var/log`. If `du` doesn't
account for the space, look for deleted-but-open files with `lsof`.

**A process is eating CPU. How do you investigate?**
`top` or `htop` to identify it, note the PID. `ps -p PID -o
cmd` for the full command line. Check how long it's been running, who
owns it, whether it's expected. `kill` if it needs stopping, `kill -9`
only as a last resort since it prevents cleanup.

**How do you check if a service is running?**
`systemctl status servicename`. `systemctl start/stop/restart` to
control it, `systemctl enable` to start it at boot. `journalctl -u
servicename` for its logs.

---

## Before you walk in

- Can you run the project from memory, without notes?
- Can you explain every line you didn't write yourself?
- Do you have the screenshots on your phone as a backup?
- Have you actually run `yes > /dev/null` and watched it spike?

If you can demo it live, do. Thirty seconds of a number climbing and a
status flipping to WARNING is more memorable than anything you can say.
