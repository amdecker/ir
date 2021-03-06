__author__ = "Amos Decker"
__date__ = "Jan 2020"

"""
provides a class for dealing with (mostly) infrared images and infrared panoramas
"""

import numpy as np
from util import Color
import util
import cv2
from typing import List, Dict, Optional, Tuple


class Image:
    def __init__(self, img):
        self.img: np.ndarray = img
        self.edges: np.ndarray = None
        self.contours: List[np.ndarray] = None

    def change_palette(self, new_palette_name: str) -> None:
        """
        given an image that only contains colors from one palette, change it to the colors of another palette
        :param new_palette_name: the palette you want to new image to follow like "lava.pal"
        :return: an image that follows the new palette
        """

        old_palette: List[Color] = util.palette_to_bgr("palettes/" + self.identify_palette())
        new_palette: List[Color] = util.palette_to_bgr("palettes/" + new_palette_name)

        # if the sizes don't match up stretch one of them
        if len(new_palette) != len(old_palette):
            if len(new_palette) > len(old_palette):
                old_palette = util.stretch_list(old_palette, len(new_palette))
            else:
                new_palette = util.stretch_list(new_palette, len(old_palette))

        old_to_new: Dict[Color, Color] = dict(zip(old_palette, new_palette))

        for i in range(self.img.shape[0]):
            row: np.ndarray = self.img[i]
            self.img[i] = util.replace(row, old_to_new)

    def set_colors_to_palette(self, palette: List[Color]) -> None:
        """
        takes in an image that is similar to colors of palette and changes the colors so they match exactly with the
        given palette. The stitching process changing pixels slightly and this function corrects that
        :param palette: output of util.palette_to_bgr()
        """
        # flatten image into 2d array then find unique values
        unique_values, inv = np.unique(
            self.img.reshape(self.img.shape[0] * self.img.shape[1], self.img.shape[2]),
            axis=0, return_inverse=True)

        # get pixel matches
        for y in range(unique_values.shape[0]):
            unique_values[y] = util.get_palette_color_match(unique_values[y], palette)

        self.img = unique_values[inv].reshape(self.img.shape)  # recreate original image shape with the changed colors

    def identify_palette(self) -> Optional[str]:
        """
        given an image it figures out which palette it uses. NOTE: the colors of the image must match exactly with
        those of the palette
        :return: filename of palette e.g. "iron.pal"
        """
        # convert palette to bgr. originally in YCbCr
        bgr_palettes: List[List[Color]] = []
        for p in util.PALETTES:
            bgr_palettes.append(util.palette_to_bgr("palettes/" + p))

        # get rid of all palettes that do not have those (b, g, r) values
        bgr_pal_copy: List[List[Color]] = bgr_palettes.copy()
        for y in range(self.img.shape[0]):
            for x in range(self.img.shape[1]):
                to_pop: List[List[Color]] = []
                for pal in bgr_palettes:
                    if tuple(self.img[y, x]) not in pal:
                        to_pop.append(pal)
                for pal in to_pop:
                    bgr_palettes.pop(bgr_palettes.index(pal))

                found_match: bool = len(bgr_palettes) == 1
                if found_match:
                    return util.PALETTES[bgr_pal_copy.index(bgr_palettes[0])]
        return None

    def remove_black(self) -> Tuple[int, int, bool, bool]:
        """
        removes the black border on the tops and bottoms of images and if there is black on the first column at the edges
        :return: rows of upper limit and lower limit of the image, whether the leftmost and rightmost columns were removed
        """
        BLACK: np.ndarray = np.zeros((1, 3))
        removed_left: bool = False
        removed_right: bool = False

        # get rid of black line at edge if it exists
        for y in range(self.img.shape[0]):
            if self.img[y, 0] in BLACK:
                self.img = self.img[:, 1:]
                removed_left = True
                break
        for y in range(self.img.shape[0] - 1, -1, -1):
            if self.img[y, -1] in BLACK:
                self.img = self.img[:, :-1]
                removed_right = True
                break

        # looks at the top half of each column and finds the place where the image stops being black
        upper_limit: int = 0
        for x in range(self.img.shape[1]):
            for y in range(self.img.shape[0] // 2):
                if self.img[y, x] in BLACK:
                    if y > upper_limit:
                        upper_limit = y
                else:
                    break

        # looks at the bottom half of each column and finds the place where the image stops being black
        lower_limit: int = self.img.shape[0] - 1
        for x in range(self.img.shape[1]):
            for y in range(self.img.shape[0] - 1, self.img.shape[0] // 2, -1):
                if self.img[y, x] in BLACK:
                    if y < lower_limit:
                        lower_limit = y
                else:
                    break
        self.img = self.img[upper_limit:lower_limit, :]
        return upper_limit, lower_limit, removed_left, removed_right

    def get_blurred(self) -> np.ndarray:
        """returns a blurred version of the image"""
        return cv2.bilateralFilter(self.img, 7, 50, 50)

    def calc_edges(self) -> None:
        """edge detection

        resources:
            https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_canny/py_canny.html#canny
            https://blog.sicara.com/opencv-edge-detection-tutorial-7c3303f10788
            https://www.pyimagesearch.com/2015/04/06/zero-parameter-automatic-canny-edge-detection-with-python-and-opencv/

        :return: edge data
        """

        # get threshold values
        sigma: float = 1.0
        v = np.median(self.img)
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))

        self.edges = cv2.Canny(self.get_blurred(), lower, upper)

    def find_contours(self) -> None:
        """finds contours in an image

        resources:
            https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_contours/py_contours_begin/py_contours_begin.html
            https://www.pythonforengineers.com/image-and-video-processing-in-python/
        """
        if self.edges is None:
            self.calc_edges()
        self.contours = cv2.findContours(self.edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]


def draw_contours(img: np.ndarray, contours: List[np.ndarray], color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
    """
    draws the contours on the image
    :param img: the image to draw the contours on
    :param contours: output from Image.find_contours()
    :param color: the color of the contours in (b, g, r)
    :return: image with the contours drawn on it
    """
    with_contours: np.ndarray = img.copy()
    cv2.drawContours(with_contours, contours, -1, color, 1)
    return with_contours


def create_mx(vl: np.ndarray, ir: np.ndarray) -> np.ndarray:
    """
    creates a mixed infrared-visible light image that preserves the colors of the infrared image while allowing you
    to see the edges and lines from the visible light image

    see https://github.com/amdecker/ir/blob/master/example_images/mx1.png for what it looks like


    :param vl: visible light image of same scene as ir
    :param ir: infrared image of same scene as vl
    :return: the mixed image
    """
    mask = cv2.adaptiveThreshold(cv2.cvtColor(Image(vl).get_blurred(), cv2.COLOR_BGR2GRAY), 255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 1)
    with_black = cv2.bitwise_and(ir, ir, mask=mask)
    return cv2.addWeighted(with_black, .4, ir, .6, 0)


def create_mx2(vl: np.ndarray, ir: np.ndarray) -> np.ndarray:
    """
    creates a mixed infrared-visible light image that DOES NOT preserve the colors of the infrared image. It layers the
    two types of images together with most of the detail coming from the ir image.

    see https://github.com/amdecker/ir/blob/master/example_images/mx2.png for what it looks like


    :param vl: visible light image of same scene as ir
    :param ir: infrared image of same scene as vl
    :return: the mixed image
    """
    return cv2.addWeighted(vl, .2, ir, .8, 0)


def create_mx3(vl: np.ndarray, ir: np.ndarray) -> np.ndarray:
    """
    creates mixed infrared-visible light image that combines edge detection with create_mx. This increases contrast on
    the "important" outlines. The lines from edge detection are white while the regular details are black.

    see https://github.com/amdecker/ir/blob/master/example_images/mx3.png for what it looks like

    :param vl:
    :param ir:
    :return:
    """
    vis = Image(vl)
    vis.find_contours()
    ir_with_contours = draw_contours(ir, vis.contours, (255, 255, 255))
    return create_mx(vis.img, ir_with_contours)








