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