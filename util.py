__author__ = "Amos Decker"
__date__ = "January 2020"

"""
various helpful tools used in StitcherEasy and rescale
- system file chooser
- remove black border from panoramas
- & others
"""

from tkinter import Tk
from tkinter.filedialog import askdirectory
import numpy as np

PALETTES = ["arctic.pal", "coldest.pal", "contrast.pal", "gray.pal", "hottest.pal", "iron.pal", "lava.pal", "rainbow.pal", "wheel.pal"]


def open_directory_chooser():
    """opens system file chooser and returns path to directory the user selects"""
    root = Tk()
    root.withdraw()
    root.update()
    directory_name = askdirectory()
    root.update()
    root.destroy()
    return directory_name


def swap_dict(d):
    """switches keys with values in a dictionary"""
    return dict((v, k) for k, v in d.items())


def make_double_digit_str(num):
    """
    useful for file names, turns 9 into "09" but keeps 15 as "15"
    :param num: one or two digit number
    :return: two digit number string
    """
    return str(num) if num > 9 else "0" + str(num)


def YCbCr_to_bgr(c):
    """
    converts from color space YCbCr to BGR
    :param c: tuple of three numbers
    :return: tuple of (b, g, r)
    """
    r = int(c[0] + 1.40200 * (c[1] - 128))
    g = int(c[0] - 0.34414 * (c[2] - 128) - 0.71414 * (c[1] - 128))
    b = int(c[0] + 1.77200 * (c[2] - 128))
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return (b, g, r)


def palette_to_bgr(filename):
    """
    creates list of tuple of (b, g, r) values for each color in palette
    :param filename: path to .pal palette file
    :return: list of tuple of (b, g, r)
    """
    with open(filename) as f:
        palette = [tuple([int(y) for y in x.split(",")]) for x in f.read().split("\n")]
        for i in range(len(palette)):
            palette[i] = YCbCr_to_bgr(palette[i])
    return palette


def get_palette_color_match(pxl, palette):
    """
    the bgr values of the images don't match up perfectly with the .pal file, so return the color in the palette
    closest to that of the pixel
    :param pxl: 1x3 array of b, g, r colors
    :param palette: output of palette_to_bgr()
    :return: tuple of bgr color in the palette
    """
    differences = np.sum(abs(palette - pxl), axis=1)  # how different the colors are
    idx = np.where(differences == np.amin(differences))[0][0]  # get index of closest color
    return palette[idx]


def stretch_list(orig, new_length):
    """
    stretches a list to be a certain length and tries to fill it in as evenly as possible

    so with orig as [0, 1, 2] and leng as 5 it would output [0, 0, 1, 1, 2]
    :param orig: list to be stretched
    :param new_length: length of final stretched list
    :return: list with length leng filled evenly with values from orig
    """
    new = [None] * new_length
    num_each = round(len(new) / len(orig))

    prev = 0
    i = 0
    while num_each * (i + 1) <= new_length and i < len(orig):
        new[prev:num_each * (i + 1)] = [orig[i]] * num_each
        prev = num_each * (i + 1)
        i += 1

    numNone = new.count(None)
    if numNone > 0:
        if i >= len(orig):
            i = len(orig) - 1
        new[-numNone:] = stretch_list([orig[i]], numNone)
    return new


def replace(arr, dict):
    """
    replaces values in 2d array according to dictionary

    example: arr = [[1, 2, 3], [1, 2, 3], [4, 5, 6]] and dict = {(1, 2, 3): (0, 0, 0), (4, 5, 6):(1, 1, 1)}
            gives [[0, 0, 0], [0, 0, 0], [1, 1, 1]]
    :param arr: a 2-D array
    :param dict: keys must contain all values in arr
    :return: new np array with same shape as arr
    """
    u, inv = np.unique(arr, return_inverse=True,
                       axis=0)  # inv gives back indices allowing reconstruction of original array from unique elements
    return np.array([dict[tuple(x)] for x in u])[inv].reshape(arr.shape)


