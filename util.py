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


def remove_black(img):
    """
    removes the black border on the tops and bottoms of images

    :param img: get this by doing cv2.imread(filepath)
    :return: cropped image
    """
    BLACK = np.zeros((1, 3))

    # looks at the top half of each column and finds the place where the image stops being black
    upper_limit = 0
    for x in range(img.shape[1]):
        for y in range(img.shape[0] // 2):
            if img[y, x] in BLACK:
                if y > upper_limit:
                    upper_limit = y
            else:
                break

    # looks at the bottom half of each column and finds the place where the image stops being black
    lower_limit = img.shape[0] - 1
    for x in range(img.shape[1]):
        for y in range(img.shape[0] - 1, img.shape[0] // 2, -1):
            if img[y, x] in BLACK:
                if y < lower_limit:
                    lower_limit = y
            else:
                break

    return img[upper_limit:lower_limit, :]


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
    gets list of tuple of (b, g, r) values for each color in palette
    :param filename: path to .pal file
    :return: list of tuple of (b, g, r)
    """
    with open(filename) as f:
        palette = [tuple([int(y) for y in x.split(",")]) for x in f.read().split("\n")]
        for i in range(len(palette)):
            palette[i] = YCbCr_to_bgr(palette[i])
    return palette


def identify_palette(img):
    #TODO WIP figure out which palette is used by the image
    # convert palette to bgr. originally in YCbCr
    bgr_palettes = []  # list of all palettes in bgr format
    for p in PALETTES:
        bgr_palettes.append(palette_to_bgr("palettes/" + p))

    bgr_pal_copy = bgr_palettes.copy()
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            to_pop = []
            print(tuple(img[y, x]))
            exit()
            for pal in bgr_palettes:
                if tuple(img[y, x]) not in pal:
                    to_pop.append(pal)
            for pal in to_pop:
                bgr_palettes.pop(bgr_palettes.index(pal))

            found_match = len(bgr_palettes) == 1
            if found_match:
                return PALETTES[bgr_pal_copy.index(bgr_palettes[0])]


def match_pixel_with_palette(pxl, palette):
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


def set_colors_to_palette(img, palette):
    """
    takes in an image and changes the colors so they match exactly with the given palette
    :param img:
    :param palette: output of palette_to_bgr()
    :return:
    """
    alt_img = np.zeros(img.shape)
    px_to_px = {}  # keeps track of the mapping between original color and new color
    unique_values = np.unique(np.concatenate([np.unique(img[i], axis=0) for i in range(img.shape[0])], axis=0), axis=0)

    # maps original value to closest palette value
    for y in range(unique_values.shape[0]):
        if y % 1000 == 0:
            print(str(y) + "/" + str(unique_values.shape[0]))
        px_to_px[tuple(unique_values[y])] = match_pixel_with_palette(unique_values[y], palette)

    # creates new image using only colors in the palette
    for y in range(img.shape[0]):
        print(y)
        for x in range(img.shape[1]):
            alt_img[y, x] = px_to_px[tuple(img[y, x])]

    return alt_img