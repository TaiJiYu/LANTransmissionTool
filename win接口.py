import time

import win32comext.shell.shell
import win32ui
import tkinter as tk
from tkinter import filedialog


def get_filename(default_dir='C://'):
    dlg = win32ui.CreateFileDialog(1)

    dlg.SetOFNInitialDir(default_dir)

    dlg.DoModal()

    filename = dlg.GetPathName()
    return filename


def get_dir():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory()



if __name__ == '__main__':
    print("{}{}".format("+"*5,"4"*9))
