import numpy as np
import sys
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import time

sys.path.append(r"C:\Users\lette\OneDrive\Desktop\modules_self") #Change based on serial utils location (Or make dynamic)
import serial_utils

#  Serial Setup 
BAUD = 9600
ser = serial_utils.find_serial_port(BAUD)

#  GUI Setup
fig = plt.figure(facecolor='black')
ax = fig.add_subplot(111, polar=True, facecolor='#002a2b')
ax.set_position([0.02, 0.1, 0.96, 0.85])

r_max = 100.0
ax.set_ylim(0, r_max)
ax.set_xlim(0, np.pi)
ax.tick_params(colors='#AAAAAA', labelsize=8)
ax.grid(color='#AAAAAA', alpha=0.3, linewidth=0.6)
ax.set_rticks(np.linspace(0, r_max, 4))
ax.set_thetagrids(np.linspace(0, 180, 7))

# Data Storage
angles = np.arange(0, 181, 1)
theta = np.radians(angles)
dists = np.ones_like(angles, dtype=float) * r_max

# Artists
# Fading sweep (store last N sweeps)
SWEEP_TRAIL_COUNT = 6
trail_lines = [
    ax.plot([], [], color=(1, 1, 1, 0.25 * (1 - i / SWEEP_TRAIL_COUNT)), linewidth=1.5)[0]
    for i in range(SWEEP_TRAIL_COUNT)
]

# Main data points
dots, = ax.plot(theta, dists, 'o', markersize=5,
                markerfacecolor='#00ffcc', markeredgecolor='none', alpha=0.85)

# Active sweep line
sweep_line, = ax.plot([], [], color='#00ffcc', linewidth=2.5, alpha=0.9)

# Toggles (Not working)
stop_bool = False
close_bool = False

def stop_event(event):
    global stop_bool
    stop_bool = True

def close_event(event):
    global stop_bool, close_bool
    stop_bool = True
    close_bool = True

def style_button(ax, label, callback):
    b = Button(ax, label, color='#222', hovercolor='#444')
    b.label.set_color('white')
    b.on_clicked(callback)
    for spine in ax.spines.values():
        spine.set_edgecolor('#555')
    return b

close_ax = fig.add_axes([0.03, 0.02, 0.2, 0.05])
stop_ax = fig.add_axes([0.77, 0.02, 0.2, 0.05])
style_button(close_ax, 'Close Plot', close_event)
style_button(stop_ax, 'Stop Program', stop_event)

fig.set_size_inches(8, 6)
fig.tight_layout(pad=2.0)
fig.canvas.draw()
axbackground = fig.canvas.copy_from_bbox(ax.bbox)

# Serial Settings
try:
    ser.timeout = 0.05
except Exception:
    pass

# Runtime State
start_word = False
current_angle = 0
last_update_time = time.time()
previous_sweep = np.copy(dists)
sweep_history = [np.copy(dists) for _ in range(SWEEP_TRAIL_COUNT)]

# Resize Handling
def on_resize(event):
    global axbackground
    fig.canvas.draw()
    axbackground = fig.canvas.copy_from_bbox(ax.bbox)

fig.canvas.mpl_connect('resize_event', on_resize)

#  Read Serial Lines
def read_serial_lines_once():
    lines = []
    try:
        if hasattr(ser, 'in_waiting'):
            n = ser.in_waiting
            if n > 0:
                raw = ser.read(n)
                s = raw.decode('utf-8', errors='replace')
                lines = [l.strip() for l in s.splitlines() if l.strip()]
        else:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                lines.append(line)
    except Exception:
        pass
    return lines

#Update GUI
UPDATE_MS = 50
timer = fig.canvas.new_timer(interval=UPDATE_MS)

def update_gui():
    global start_word, dists, current_angle, previous_sweep, sweep_history, axbackground

    if stop_bool:
        timer.stop()
        if close_bool:
            plt.close('all')
        return

    lines = read_serial_lines_once()
    for raw_line in lines:
        if not raw_line:
            continue
        if not start_word:
            if "Ultrasonic Radar Initialized" in raw_line:
                start_word = True
                print("Radar Initialized — Starting data stream...")
            continue

        if "No echo" in raw_line:
            continue

        parts = raw_line.replace(' ', '').split(',')
        if len(parts) != 2:
            continue

        try:
            dist, angle = float(parts[0]), int(float(parts[1]))
        except Exception:
            continue

        if 0 <= angle <= 180:
            dists[angle] = min(dist, r_max)
            current_angle = angle

    # Smooth sweep interpolation
    step = 2
    interpolated = np.linspace(previous_sweep, dists, step)
    previous_sweep = dists.copy()

    # Update trail
    sweep_history = [previous_sweep.copy()] + sweep_history[:-1]

    fig.canvas.restore_region(axbackground)

    # Draw trails
    for i, line in enumerate(trail_lines):
        line.set_data(theta, sweep_history[i])
        ax.draw_artist(line)

    # Update points and sweep
    dots.set_data(theta, dists)
    ang_rad = np.radians(current_angle)
    sweep_line.set_data([ang_rad, ang_rad], [0, r_max])

    ax.draw_artist(dots)
    ax.draw_artist(sweep_line)

    try:
        fig.canvas.blit(ax.bbox)
    except Exception:
        fig.canvas.draw()

    fig.canvas.flush_events()

timer.add_callback(update_gui)
timer.start()

print("Waiting for Arduino...")
try:
    plt.show()
except KeyboardInterrupt:
    timer.stop()
    plt.close('all')
    print("Keyboard Interrupt - exiting")
