#!/usr/bin/env python3
"""
host_check_tk.py

Quick runtime check to ensure Tkinter GUI is available. Exits with code 0
when a simple hidden Tk window can be created; otherwise prints error and
exits non-zero so automated targets can detect absence of GUI support.
"""
import sys
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    # Attempt a minimal operation to ensure Tcl/Tk initialized
    try:
        ver = root.tk.call('info', 'patchlevel')
    except Exception:
        ver = 'unknown'
    print('tkinter ok; tcl/tk version:', ver)
    root.destroy()
    sys.exit(0)
except Exception as e:
    print('tkinter not available:', e)
    sys.exit(2)
