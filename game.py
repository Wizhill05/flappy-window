import tkinter as tk
from PIL import Image, ImageTk
import wx
from playsound import playsound
import pyvolume
import platform
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import subprocess
import re
import random

app = wx.App(False)
screenRes = wx.GetDisplaySize()
cords = [int(screenRes[0] / 10), int(screenRes[0] / 10)]
gravity = (screenRes[1] / 1080) * 1.5
velocity = 0
refresh_rate = int(1000 / 30)

pipe_width = 80
pipe_gap = 300
pipe_color = "green"
pipe_move_speed = 5
pipe_horizontal_spacing = 450

pipes = []


def get_windows_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume.GetMasterVolumeLevelScalar()


def get_macos_volume():
    result = subprocess.run(
        ["osascript", "-e", "output volume of (get volume settings)"],
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip())


def get_linux_volume():
    result = subprocess.run(
        ["amixer", "sget", "Master"], capture_output=True, text=True
    )
    output = result.stdout
    match = re.search(r"\[(\d+)%\]", output)
    if match:
        return int(match.group(1))
    return 0


def get_volume():
    global current_volume
    if platform.system() == "Windows":
        return get_windows_volume() * 100
    if platform.system() == "Darwin":
        return get_macos_volume()
    if platform.system() == "Linux":
        return get_linux_volume()


def create_pipe():
    global pipes, bird, screenRes, pipe_width, pipe_gap, pipe_color
    min_y_for_top_of_gap = 50
    max_y_for_top_of_gap = screenRes[1] - pipe_gap - 50

    if min_y_for_top_of_gap >= max_y_for_top_of_gap:
        gap_y = screenRes[1] // 2 - pipe_gap // 2
    else:
        gap_y = random.randint(min_y_for_top_of_gap, max_y_for_top_of_gap)

    top_pipe_height = gap_y
    bottom_pipe_y_start = gap_y + pipe_gap
    bottom_pipe_height = screenRes[1] - bottom_pipe_y_start

    initial_x = screenRes[0]

    # Top Pipe Window
    top_pipe = tk.Toplevel(bird)
    top_pipe.title("Pipe")
    top_pipe.geometry(f"{pipe_width}x{top_pipe_height}+{initial_x}+{0}")
    top_pipe.overrideredirect(True)
    top_pipe.resizable(width=False, height=False)
    top_pipe.configure(bg=pipe_color)
    top_pipe.attributes("-topmost", True)

    bottom_pipe = tk.Toplevel(bird)
    bottom_pipe.title("Pipe")
    bottom_pipe.geometry(
        f"{pipe_width}x{bottom_pipe_height}+{initial_x}+{bottom_pipe_y_start}"
    )
    bottom_pipe.overrideredirect(True)
    bottom_pipe.resizable(width=False, height=False)
    bottom_pipe.configure(bg=pipe_color)
    bottom_pipe.attributes("-topmost", True)

    pipes.append(
        {
            "top_window": top_pipe,
            "bottom_window": bottom_pipe,
            "x": initial_x,
            "scored": False,
        }
    )


def update_pipes():
    global pipes, screenRes, pipe_move_speed, pipe_width, pipe_horizontal_spacing

    spawn_new_pipe = False
    if not pipes:
        spawn_new_pipe = True
    else:
        if pipes[-1]["x"] < screenRes[0] - pipe_horizontal_spacing:
            spawn_new_pipe = True

    if spawn_new_pipe:
        create_pipe()

    pipes_to_remove = []
    for pipe_pair in pipes:
        pipe_pair["x"] -= pipe_move_speed

        pipe_pair["top_window"].geometry(f"+{int(pipe_pair['x'])}+{0}")
        bottom_y = pipe_pair["top_window"].winfo_height() + pipe_gap
        pipe_pair["bottom_window"].geometry(f"+{int(pipe_pair['x'])}+{bottom_y}")

        if pipe_pair["x"] + pipe_width < 0:
            pipes_to_remove.append(pipe_pair)
            pipe_pair["top_window"].destroy()
            pipe_pair["bottom_window"].destroy()

    for p in pipes_to_remove:
        if p in pipes:
            pipes.remove(p)


def update_bird():
    global cords, velocity
    velocity += gravity

    if bird.winfo_y() > screenRes[1]:
        # vol = int(get_volume())
        # pyvolume.custom(100)
        # playsound("death.mp3")
        # pyvolume.custom(vol)
        exit()

    if bird.winfo_y() < 0:
        velocity = 4

    cords[1] += int(velocity)
    bird.geometry(f"+{cords[0]}+{cords[1]}")

    update_pipes()

    bird.after(refresh_rate, update_bird)


def jump(event=None):
    global cords, velocity, gravity
    velocity = -20


if __name__ == "__main__":
    # Bird
    bird = tk.Tk()
    transparent_color = "#010101"

    bird.geometry(f"100x100+{cords[0]}+{cords[1]}")
    bird.overrideredirect(True)
    bird.configure(bg=transparent_color)
    bird.wm_attributes("-transparentcolor", transparent_color)
    bird.attributes("-topmost", True)  # Keep bird window on top

    bird.resizable(width=False, height=False)
    bird.bind("<space>", jump)

    try:
        img = Image.open("red.png")
        img = img.resize(size=(100, 100))
        photo = ImageTk.PhotoImage(img)

        image_label = tk.Label(bird, image=photo, bg=transparent_color)
        image_label.pack()
    except Exception as e:
        error_label = tk.Label(
            bird, text=f"An error occurred: {e}", bg=transparent_color
        )
        error_label.pack()

    # Focus the bird window when the game starts
    bird.lift()
    bird.focus_force()

    update_bird()
    bird.mainloop()
