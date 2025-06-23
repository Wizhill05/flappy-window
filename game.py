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

# vol = int(get_volume())
# pyvolume.custom(100)
# playsound("death.mp3")
# pyvolume.custom(vol)

app = wx.App(False)
screenRes = wx.GetDisplaySize()
coords = [int(screenRes[0] / 10), int(screenRes[0] / 10)]
gravity = (screenRes[1] / 1080) * 1.5
velocity = 0
refresh_rate = int(1000 / 40)
score = 0
pipe_width = 80
pipe_gap = 300
pipe_color = "green"
pipe_move_speed = 5
pipe_horizontal_spacing = 450
sound = False
mute_button = None
pipes = []
game_over = False


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

    score_label.config(text=f"Score: {score}")


def sq_distance(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def check_collision():
    center = (coords[0] + 60, coords[1] + 56)

    if center[0] < pipes[0]["x"]:
        tl = (pipes[0]["x"], pipes[0]["bottom_window"].winfo_y() - pipe_gap)
        bl = (pipes[0]["x"], pipes[0]["bottom_window"].winfo_y())
        min_tlbl = min(sq_distance(center, tl), sq_distance(center, bl))
        return min_tlbl < 40

    elif center[0] < pipes[0]["x"] + pipe_width:
        return not (
            pipes[0]["bottom_window"].winfo_y() - pipe_gap
            < coords[1]
            < pipes[0]["bottom_window"].winfo_y()
        )

    else:
        tr = (
            pipes[0]["x"] + pipe_width,
            pipes[0]["bottom_window"].winfo_y() - pipe_gap,
        )
        br = (pipes[0]["x"] + pipe_width, pipes[0]["bottom_window"].winfo_y())
        min_trbr = min(sq_distance(center, tr), sq_distance(center, br))
        return min_trbr < 40


def show_game_over_popup():
    global game_over_popup

    game_over_popup = tk.Toplevel(bird)
    game_over_popup.title("Game Over!")
    game_over_popup.geometry(
        f"300x150+{int(screenRes[0] / 2 - 150)}+{int(screenRes[1] / 2 - 75)}"
    )
    game_over_popup.overrideredirect(True)
    game_over_popup.attributes("-topmost", True)
    game_over_popup.grab_set()

    game_over_label = tk.Label(
        game_over_popup,
        text="Game Over!",
        font=("Consolas", 24, "bold"),
        fg="red",
        bg="black",
    )
    game_over_label.pack(pady=5)

    final_score_label = tk.Label(
        game_over_popup,
        text=f"Final Score: {score}",
        font=("Consolas", 18),
        fg="white",
        bg="black",
    )
    final_score_label.pack(pady=5)

    button_frame = tk.Frame(game_over_popup, bg="black")
    button_frame.pack(pady=10)

    replay_button = tk.Button(
        button_frame, text="Replay", font=("Consolas", 14), command=reset_game
    )
    replay_button.pack(side=tk.LEFT, padx=10)

    global mute_button
    mute_button = tk.Button(
        button_frame,
        text="🔇" if not sound else "🔊",
        font=("Consolas", 14),
        command=toggle_mute_sound,
    )
    mute_button.pack(side=tk.LEFT, padx=10)

    quit_button = tk.Button(
        button_frame, text="Quit", font=("Consolas", 14), command=bird.destroy
    )
    quit_button.pack(side=tk.RIGHT, padx=10)

    game_over_popup.configure(bg="black")


def toggle_mute_sound():
    global sound, mute_button
    sound = not sound
    if sound:
        mute_button.config(text="🔊")
    else:
        mute_button.config(text="🔇")


def reset_game():
    global score, coords, velocity, pipes, game_over

    for pipe_pair in pipes:
        pipe_pair["top_window"].destroy()
        pipe_pair["bottom_window"].destroy()
    pipes.clear()

    score = 0
    coords[0] = int(screenRes[0] / 10)
    coords[1] = int(screenRes[0] / 10)
    velocity = 0
    game_over = False

    game_over_popup.destroy()
    bird.geometry(f"+{coords[0]}+{coords[1]}")
    bird.update_idletasks()
    update_bird()


def update_bird():
    global coords, velocity, score, game_over
    velocity += gravity

    if not game_over:
        if bird.winfo_y() > screenRes[1] or bird.winfo_y() < -100:
            game_over = True
            if sound:
                vol = int(get_volume())
                pyvolume.custom(100)
                playsound("death.mp3")
                pyvolume.custom(vol)
            show_game_over_popup()
            return

        if bird.winfo_y() < 0:
            velocity = 4

        coords[1] += int(velocity)
        bird.geometry(f"+{coords[0]}+{coords[1]}")
        try:
            if check_collision():
                game_over = True
                if sound:
                    vol = int(get_volume())
                    pyvolume.custom(100)
                    playsound("death.mp3")
                    pyvolume.custom(vol)
                show_game_over_popup()
                return
        except Exception:
            pass

        if pipes and pipes[0]["x"] + pipe_width < coords[0] and not pipes[0]["scored"]:
            score += 1
            pipes[0]["scored"] = True

        update_pipes()
        bird.focus_force()
        score_label.config(text=f"Score: {score}")
        bird.after(refresh_rate, update_bird)


def jump(event=None):
    global coords, velocity, gravity
    velocity = -20


if __name__ == "__main__":
    # Bird
    bird = tk.Tk()
    transparent_color = "#010101"

    bird.geometry(f"100x100+{coords[0]}+{coords[1]}")
    bird.overrideredirect(True)
    bird.configure(bg=transparent_color)
    bird.wm_attributes("-transparentcolor", transparent_color)
    bird.attributes("-topmost", True)

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

    bird.lift()
    bird.focus_force()

    score_window = tk.Toplevel(bird)
    score_window.title("Score")
    score_window.geometry("160x40+0+0")
    score_window.overrideredirect(True)
    score_window.configure(bg="black")
    score_window.attributes("-topmost", True)
    score_label = tk.Label(
        score_window,
        text=f"Score: {score}",
        font=("Consolas", 16),
        fg="white",
        bg="black",
    )
    score_label.pack(expand=True, fill="both")

    update_bird()
    bird.mainloop()
