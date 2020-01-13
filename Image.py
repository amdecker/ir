__author__ = "Amos Decker"
__date__ = "Jan 2020"

import numpy as np
import util
import cv2


class Image:
    def __init__(self, img):
        self.img = img
        self.edges = None
        self.contours = None

    def change_palette(self, new_palette_name):
        """
        given an image that only contains colors from one palette, change it to the colors of another palette
        :param new_palette_name: the palette you want to new image to follow
        :return: an image that follows the new palette
        """
        old_palette = util.palette_to_bgr("palettes/" + self.identify_palette())
        new_palette = util.palette_to_bgr("palettes/" + new_palette_name)

        # if the sizes don't match up stretch one of them
        if len(new_palette) != len(old_palette):
            if len(new_palette) > len(old_palette):
                old_palette = util.stretch_list(old_palette, len(new_palette))
            else:
                new_palette = util.stretch_list(new_palette, len(old_palette))

        old_to_new = dict(zip(old_palette, new_palette))

        new_img = np.zeros(self.img.shape)
        for y in range(self.img.shape[0]):
            for x in range(self.img.shape[1]):
                new_img[y, x] = old_to_new[tuple(self.img[y, x])]

        self.img = new_img

    def set_colors_to_palette(self, palette):
        """
        takes in an image and changes the colors so they match exactly with the given palette
        :param palette: output of palette_to_bgr()
        :return:
        """
        alt_img = np.zeros(self.img.shape)
        px_to_px = {}  # keeps track of the mapping between original color and new color
        unique_values = np.unique(np.concatenate([np.unique(self.img[i], axis=0) for i in range(self.img.shape[0])], axis=0),
                                  axis=0)

        # maps original value to closest palette value
        for y in range(unique_values.shape[0]):
            if y % 1000 == 0:
                print(str(y) + "/" + str(unique_values.shape[0]))
            px_to_px[tuple(unique_values[y])] = util.get_palette_color_match(unique_values[y], palette)

        # creates new image using only colors in the palette
        for y in range(self.img.shape[0]):
            if y % 100 == 0:
                print(str(y) + "/" + str(self.img.shape[0]))
            for x in range(self.img.shape[1]):
                alt_img[y, x] = px_to_px[tuple(self.img[y, x])]

        self.img = alt_img

    def identify_palette(self):
        """
        given an image it figures out which palette it uses. NOTE: the colors of the image must match exactly with
        those of the palette
        :return: filename of palette e.g. "iron.pal"
        """
        # convert palette to bgr. originally in YCbCr
        bgr_palettes = []
        for p in util.PALETTES:
            bgr_palettes.append(util.palette_to_bgr("palettes/" + p))

        # get rid of all palettes that do not have those (b, g, r) values
        bgr_pal_copy = bgr_palettes.copy()
        for y in range(self.img.shape[0]):
            for x in range(self.img.shape[1]):
                to_pop = []
                for pal in bgr_palettes:
                    if tuple(self.img[y, x]) not in pal:
                        to_pop.append(pal)
                for pal in to_pop:
                    bgr_palettes.pop(bgr_palettes.index(pal))

                found_match = len(bgr_palettes) == 1
                if found_match:
                    return util.PALETTES[bgr_pal_copy.index(bgr_palettes[0])]
        return False

    def remove_black(self):
        """
        removes the black border on the tops and bottoms of images
        :return: cropped image
        """
        BLACK = np.zeros((1, 3))

        # looks at the top half of each column and finds the place where the image stops being black
        upper_limit = 0
        for x in range(self.img.shape[1]):
            for y in range(self.img.shape[0] // 2):
                if self.img[y, x] in BLACK:
                    if y > upper_limit:
                        upper_limit = y
                else:
                    break

        # looks at the bottom half of each column and finds the place where the image stops being black
        lower_limit = self.img.shape[0] - 1
        for x in range(self.img.shape[1]):
            for y in range(self.img.shape[0] - 1, self.img.shape[0] // 2, -1):
                if self.img[y, x] in BLACK:
                    if y < lower_limit:
                        lower_limit = y
                else:
                    break
        self.img = self.img[upper_limit:lower_limit, :]

    def get_blurred(self):
        """returns a blurred version of the image"""
        return cv2.bilateralFilter(self.img, 7, 50, 50)

    def calc_edges(self):
        """edge detection

        resources:
            https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_canny/py_canny.html#canny
            https://blog.sicara.com/opencv-edge-detection-tutorial-7c3303f10788
            https://www.pyimagesearch.com/2015/04/06/zero-parameter-automatic-canny-edge-detection-with-python-and-opencv/

        :return: edge data
        """

        # get threshold values
        sigma = 1
        v = np.median(self.img)
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))

        self.edges = cv2.Canny(self.get_blurred(), lower, upper)

    def find_contours(self):
        """finds contours in an image

        resources:
            https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_contours/py_contours_begin/py_contours_begin.html
            https://www.pythonforengineers.com/image-and-video-processing-in-python/
        """
        if not self.edges:
            self.calc_edges()
        self.contours = cv2.findContours(self.edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]


def draw_contours(img, contours, color=(0, 255, 0)):
    """
    draws the contours on the image
    :param img: the image to draw the contours on
    :param contours: output from Image.find_contours()
    :param color: the color of the contours in (b, g, r)
    :return: image with the contours drawn on it
    """
    with_contours = img.copy()
    cv2.drawContours(with_contours, contours, -1, color, 1)
    return with_contours


def create_mx(vl, ir):
    """
    creates a mixed infrared-visible light image that preserves the colors of the infrared image while allowing you
    to see the edges and lines from the visible light image
    :param vl: visible light image of same scene as ir
    :param ir: infrared image of same scene as vl
    :return: the mixed image
    """
    mask = cv2.adaptiveThreshold(cv2.cvtColor(Image(vl).get_blurred(), cv2.COLOR_BGR2GRAY), 255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 1)
    with_black = cv2.bitwise_and(ir, ir, mask=mask)
    return cv2.addWeighted(with_black, .4, ir, .6, 0)









