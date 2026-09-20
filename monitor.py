#!/usr/bin/env python3
"""
Linux System Health Monitor
---------------------------
Checks CPU, memory, disk, uptime, top processes and network
connectivity against configured thresholds, then prints a
structured report to the terminal.

Usage:
    python3 monitor.py            # print one report and exit
    python3 monitor.py --watch    # refresh every 5 seconds (Ctrl+C to stop)
"""

import sys         # lets us read command-line arguments
import socket      # used for the network connectivity check
import time        # used for sleeping in watch mode
import datetime    # used for formatting timestamps and uptime

import psutil      # the library that reads system metrics


# ----------------------------------------------------------
# CONFIGURATION
# If usage goes above these percentages, we show a warning.
# Lower them temporarily to see the alert logic fire.
# ----------------------------------------------------------
CPU_THRESHOLD = 80.0      # percent
MEMORY_THRESHOLD = 80.0   # percent
DISK_THRESHOLD = 85.0     # percent

DISK_PATH = "/"           # which filesystem to check ("/" = root)
TOP_PROCESS_COUNT = 5     # how many processes to list
WATCH_INTERVAL = 5        # seconds between refreshes in watch mode

# Host and port used to test internet connectivity.
# 8.8.8.8 is Google's public DNS server, port 53 is DNS.
# We pick this because it is almost always reachable and responds fast.
NETWORK_TEST_HOST = "8.8.8.8"
NETWORK_TEST_PORT = 53


# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------

def check_status(value, threshold):
    """
    Compare a measured value against its threshold.
    Returns a short status string we can print.
    """
    if value >= threshold:
        return f"[WARNING - above {threshold}% threshold]"
    else:
        return "[OK]"


def format_bytes(num_bytes):
    """
    Turn a raw byte count into something human-readable.
    1610612736 -> '1.5 GB'

    We divide by 1024 repeatedly, stepping up through the units,
    until the number is small enough to read.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes = num_bytes / 1024
    return f"{num_bytes:.1f} PB"


# ----------------------------------------------------------
# METRIC COLLECTION
# Each function collects one thing and returns it.
# Keeping them separate makes the code easy to test and extend.
# ----------------------------------------------------------

def get_cpu_usage():
    """
    Returns CPU usage as a percentage.

    interval=1 means psutil samples the CPU, waits 1 second,
    samples again, and reports the difference. CPU usage is a
    rate over time, so it NEEDS two samples. If you call this
    with no interval, the very first result is meaningless (0.0).
    """
    return psutil.cpu_percent(interval=1)


def get_memory_info():
    """
    virtual_memory() returns an object with several fields.
    We return the whole object so the report can show both
    the percentage and the actual used/total figures.
    """
    return psutil.virtual_memory()


def get_disk_info(path=DISK_PATH):
    """
    disk_usage() needs a path. On Linux "/" is the root
    filesystem, which is usually what we care about.
    """
    return psutil.disk_usage(path)


def get_uptime():
    """
    psutil.boot_time() gives the time the machine booted, as a
    Unix timestamp (seconds since 1 Jan 1970).

    Subtracting it from the current time gives us how long the
    system has been running. timedelta formats that nicely as
    '3 days, 4:12:07'.
    """
    boot_timestamp = psutil.boot_time()
    now_timestamp = time.time()
    uptime_seconds = now_timestamp - boot_timestamp

    # int() strips the fractional seconds so it prints cleanly
    return datetime.timedelta(seconds=int(uptime_seconds))


def get_top_processes(count=TOP_PROCESS_COUNT):
    """
    Returns the processes using the most CPU.

    process_iter() walks every running process. We ask for the
    fields we want up front, which is faster than querying each
    process separately.
    """
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            # proc.info is a dictionary of the fields we requested
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # A process can exit while we are iterating, or be owned
            # by another user. Skipping it is the correct behaviour -
            # without this, the script would crash on a busy system.
            continue

    # Sort highest CPU first. "or 0" guards against None values,
    # which psutil can return for processes it could not read.
    processes.sort(key=lambda p: p['cpu_percent'] or 0, reverse=True)

    return processes[:count]


def check_network():
    """
    Tests whether the machine can reach the internet.

    We open a TCP socket to a known-good host with a short timeout.
    If it connects, the network is up. If it fails for any reason,
    we treat that as unreachable.

    Note: this tests connectivity, not DNS. We use an IP address
    deliberately so a broken DNS server does not look like a
    dead network.
    """
    try:
        socket.setdefaulttimeout(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((NETWORK_TEST_HOST, NETWORK_TEST_PORT))
        sock.close()
        return True
    except OSError:
        return False


# ----------------------------------------------------------
# REPORTING
# ----------------------------------------------------------

def print_report():
    """
    Collect every metric, then print the formatted report.
    """
    # --- collect ---
    cpu = get_cpu_usage()
    memory = get_memory_info()
    disk = get_disk_info()
    uptime = get_uptime()
    processes = get_top_processes()
    network_up = check_network()

    hostname = socket.gethostname()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- print ---
    print()
    print("=" * 52)
    print("           SYSTEM HEALTH REPORT")
    print("=" * 52)
    print(f"Hostname  : {hostname}")
    print(f"Timestamp : {timestamp}")
    print(f"Uptime    : {uptime}")
    print("-" * 52)

    # f-string formatting notes:
    #   {cpu:>6.1f}  right-aligned, 6 wide, 1 decimal place
    # This keeps all the numbers lined up in a neat column.
    print(f"CPU       : {cpu:>6.1f}%   {check_status(cpu, CPU_THRESHOLD)}")

    print(f"Memory    : {memory.percent:>6.1f}%   "
          f"{check_status(memory.percent, MEMORY_THRESHOLD)}")
    print(f"            {format_bytes(memory.used)} used "
          f"of {format_bytes(memory.total)}")

    print(f"Disk ({DISK_PATH})  : {disk.percent:>6.1f}%   "
          f"{check_status(disk.percent, DISK_THRESHOLD)}")
    print(f"            {format_bytes(disk.used)} used "
          f"of {format_bytes(disk.total)}")

    if network_up:
        print("Network   : reachable        [OK]")
    else:
        print("Network   : UNREACHABLE      [WARNING]")

    print("-" * 52)
    print(f"Top {len(processes)} processes by CPU:")
    for proc in processes:
        name = proc['name'] or "unknown"
        cpu_pct = proc['cpu_percent'] or 0
        mem_pct = proc['memory_percent'] or 0
        # :<20 left-aligns the name in a 20-character column
        print(f"  {name:<20} CPU {cpu_pct:>5.1f}%   MEM {mem_pct:>5.1f}%")

    print("=" * 52)
    print()


def main():
    """
    Decide whether to run once or loop, based on the
    command-line argument the user passed.
    """
    # sys.argv is the list of words typed on the command line.
    # sys.argv[0] is the script name, so we check everything after it.
    watch_mode = "--watch" in sys.argv[1:]

    if watch_mode:
        print("Watch mode - press Ctrl+C to stop.")
        try:
            while True:
                print_report()
                time.sleep(WATCH_INTERVAL)
        except KeyboardInterrupt:
            # Without this, Ctrl+C prints an ugly traceback.
            # Catching it lets us exit cleanly.
            print("\nStopped.")
    else:
        print_report()


# This means: only run main() if the file is executed directly
# (python3 monitor.py), not if it is imported by another file.
# It is a standard Python convention - interviewers do ask about it.
if __name__ == "__main__":
    main()
