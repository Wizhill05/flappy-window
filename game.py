import tkinter as tk
from PIL import Image, ImageTk
import wx

app = wx.App(False)

screenRes = wx.GetDisplaySize()
cords = [int(screenRes[0] / 10), int(screenRes[0] / 10)]
gravity = (screenRes[1] / 1080) * 1.5
velocity = 0
refresh_rate = int(1000 / 30)


def update_bird():
    global cords, velocity
    velocity += gravity

    if bird.winfo_y() > screenRes[1]:
        bird.quit()
        bird.destroy()

    if bird.winfo_y() < 0:
        velocity = 5

    cords[1] += int(velocity)
    bird.geometry(f"+{cords[0]}+{cords[1]}")
    bird.after(refresh_rate, update_bird)


def jump(event=None):
    global cords, velocity, gravity
    velocity = -20


if __name__ == "__main__":
    bird = tk.Tk()
    bird.geometry(f"100x100+{cords[0]}+{cords[1]}")
    bird.resizable(width=False, height=False)
    bird.title("Bird")
    bird.bind("<space>", jump)

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
