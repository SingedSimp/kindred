from contextlib import contextmanager
import tkinter as tk
from PIL import Image, ImageTk
import requests
import win32con
import win32gui
import win32api
import functools
from urllib3.exceptions import InsecureRequestWarning
# FIXME Add original image into a backup before i fuck something up
# TODO Add error catching to the ending of the game.

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Overlay:
    def __init__(self, width: int, height: int, positions: dict):
        self.width = width
        self.height = height
        self.positions = positions
        self.frame, self.canvas = createOverlayWindow(self.width, self.height)
        self.ucount = 0
        self.api = InGameData()
        self.api.update()
        
    
    def setClickthrough(self):
        try: 
            hwnd = self.canvas.winfo_id()
            styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            styles = win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            #win32gui.SetWindowLang(hwnd, win32con.GWL_EXSTYLE, styles)
            #win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
        except Exception as e:
            print(e) 
    
    def displayImage(self, pos: Position, image: str, name: str, tag: str):
        checkRGBA(image) # Dangerous, writes image as RGBA. Have backups.
        photoimage = ImageTk.PhotoImage(file=image)
        self.canvas.create_image(pos.x, pos.y, image=photoimage, tags=(name, tag))

    def update(self):
        self.ucount += 1
        if self.ucount % 10 == 0:
            try: 
                self.api.update()
            except:
                self.canvas.destroy()
                self.canvas.update()
                self.frame.destroy()
                self.frame.update()
                raise requests.exceptions.ConnectionError("API Failed to connect")
            try:
                alevel = self.api.data["activePlayer"]["abilities"]["Q"]["abilityLevel"]
            except:
                self.canvas.destroy()
                self.canvas.update()
                self.frame.destroy()
                self.frame.update()
                raise requests.exceptions.ConnectionError("API Failed to connect")
        image = "highlight_level.png"
        alevel = self.api.data["activePlayer"]["abilities"]["Q"]["abilityLevel"]
        alevel += self.api.data["activePlayer"]["abilities"]["W"]["abilityLevel"]
        alevel += self.api.data["activePlayer"]["abilities"]["E"]["abilityLevel"]
        alevel += self.api.data["activePlayer"]["abilities"]["R"]["abilityLevel"]
        level = self.api.data["activePlayer"]["level"]
        dlevel = level - alevel
        qmax = [2, 4,  5,  7,  9 ]
        wmax = [1, 8,  10, 12, 13]
        emax = [3, 14, 15, 17, 18]
        rmax = [6, 11, 16]
        if dlevel != 0:
            if not self.canvas.find_withtag("highlight"): 
                # This returns a tuple, so if not checks if it is empty.
                # This prevents from acidentally creating many of these tuples
                if level in qmax:
                    self.displayImage(self.positions["qlevel"], image, "q", "highlight")
                elif level in wmax: 
                    self.displayImage(self.positions["wlevel"], image, "w", "highlight")
                elif level in emax: 
                    self.displayImage(self.positions["elevel"], image, "e", "highlight")
                elif level in rmax: 
                    self.displayImage(self.positions["rlevel"], image, "r", "highlight")
        else: 
            self.canvas.delete("highlight")
        self.frame.after(100, self.update)

    def render(self):
        self.canvas.pack()
        self.update()
        self.frame.mainloop()
        print("heheheha")
        return "Done"

class InGameData:
    def __init__(self):
        self.url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
        self.data = []
    def update(self):
        # We use verify false as the api has no certificate.
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        response = requests.get(self.url, verify=False)
        self.data = response.json()

class Window:
    def __init__(self, width: int, height: int, name: int, icon: str):
        self.width = width
        self.height = height
        self.name = name
        self.icon = icon
        self.frame, self.canvas = createWindow(self.width, self.height, self.name)
        self.frame.iconbitmap(self.icon)
        self.text = tk.Text(
                self.canvas,
        )
        self.image = ImageTk.PhotoImage(file=self.icon)
    def makeoverlay(self):
        txt = ""
        try:
            positions = {
                "qlevel": Position(826, 974),
                "wlevel": Position(870, 974),
                "elevel": Position(914, 974),
                "rlevel": Position(957, 974),
            }
            overlay = Overlay(win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1), positions)
            overlay.setClickthrough()
            txt = "Success! Wolf is out for a hunt!\n"
        except:
            txt = "Wolf got lost on the way there. Are you sure you are in game?\n"
        self.text.insert(tk.INSERT, txt)
        if "success" in txt.lower():
            try:
                overlay.render()
            except:
                pass
        
                
    def widget(self):
        start = tk.Button(
            self.canvas,
            image=self.image,
            command=self.makeoverlay,
        )
        start.pack()

    def update(self):
        self.frame.after(100, self.update)
    def render(self):
        self.widget()
        self.text.pack()
        self.text.insert(tk.INSERT, "Output goes here...\n")
        self.canvas.pack()
        self.update()
        self.frame.mainloop()

# Images must be in an RGBA format so they display transparent to the window
def checkRGBA(image: str):
    im = Image.open(image)
    im = im.convert("RGBA")
    im.save(image)

# This creates a clear window with Tkinter, but must be set to clickthrough seperatley.
def createOverlayWindow(width: int, height: int):
    frame = tk.Toplevel()
    frame.overrideredirect(1)
    frame.geometry(f"{width}x{height}")
    frame.title("Overlay Window")
    frame.attributes("-transparentcolor", "white", "-topmost", "1")
    frame.config(bg="white")
    frame.attributes("-alpha", 1)
    frame.wm_attributes("-topmost", 1)
    canvas = tk.Canvas(frame, width=width, height=height, bg="white", highlightthickness=0)
    return frame, canvas

def createWindow(width: int, height: int, name: str):
    frame = tk.Tk()
    frame.geometry(f"{width}x{height}")
    frame.title(name)
    canvas = tk.Canvas(frame, width=width, height=height, bg="white", highlightthickness=0)
    return frame, canvas


def main():
    
    maxwidth = win32api.GetSystemMetrics(0)
    maxheight = win32api.GetSystemMetrics(1)
    #overlay = Overlay(width, height, positions)
    startWindow = Window(580, 580, "Kindred", "./kindred250x250.ico")
    #overlay.setClickthrough()
    startWindow.render()
    #overlay.render()

    
if __name__ == "__main__":
    main()