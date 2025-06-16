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

app = wx.App(False)
screenRes = wx.GetDisplaySize()
cords = [int(screenRes[0] / 10), int(screenRes[0] / 10)]
gravity = (screenRes[1] / 1080) * 1.5
velocity = 0
refresh_rate = int(1000 / 30)


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
    """
    Gets the current master volume on Linux using amixer.
    Returns the volume as an integer between 0 and 100.
    """
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


def update_bird():
    global cords, velocity
    velocity += gravity

    if bird.winfo_y() > screenRes[1]:
        vol = int(get_volume())
        pyvolume.custom(100)
        playsound("death.mp3")
        pyvolume.custom(vol)
        exit()

    if bird.winfo_y() < 0:
        velocity = 4

    cords[1] += int(velocity)
    bird.geometry(f"+{cords[0]}+{cords[1]}")
    bird.after(refresh_rate, update_bird)


def jump(event=None):
    global cords, velocity, gravity
    velocity = -20


if __name__ == "__main__":
    # Bird
    bird = tk.Tk()
    bird.geometry(f"100x100+{cords[0]}+{cords[1]}")
    bird.resizable(width=False, height=False)
    bird.title("Bird")
    bird.bind("<space>", jump)

    # Pipe

    try:
        img = Image.open("red.png")
        img = img.resize(size=(100, 100))
        photo = ImageTk.PhotoImage(img)

        image_label = tk.Label(bird, image=photo)
        image_label.pack()
    except Exception as e:
        error_label = tk.Label(bird, text=f"An error occurred: {e}")
        error_label.pack()

    update_bird()
    bird.mainloop()
