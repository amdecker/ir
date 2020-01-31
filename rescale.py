__author__ = "Amos Decker"
__date__ = "January 2020"

"""
Each individual image when taken sets the colors based on the lowest and highest temperature in that frame.

This program standardizes the color/temperature relationship throughout the set of images based on the global low and
global high
"""

import json
import cv2
import numpy as np
import time
import os
from StitcherEasy import open_directory_chooser
from util import Color
import util
import Image
from typing import List, Dict


class Rescaler:
    def __init__(self, directory_path: str, palette: str = "palettes/iron.pal", ):
        self.directory_path: str = directory_path

        # convert palette to bgr. originally in YCbCr
        self.palette: List[Color] = util.palette_to_bgr(palette)

        # grab temperature extremes
        with open(directory_path + "/info.json") as f:
            info: Dict = json.loads(f.read())
            self.highest: List[float] = info["highestTemperatures"]
            self.lowest: List[float] = info["lowestTemperatures"]

        self.global_color_map: Dict[float, Color] = None

    def replace_extreme_high_temps(self, thresh: float = 150, overwrite_file: bool = False) -> None:
        """
        replaces values greater than thresh with the closest below the threshold
        example:
            given:
                image num   |   high temp
                        #8  |   2
                        #9  |   150.25
                        #10 |   150.25
                        #11 |   5
            the result would be:
                image num   |   high temp
                        #8  |   2
                        #9  |   2
                        #10 |   5
                        #11 |   5
        :param thresh: default is 150, the max temperature that the camera can get is 150.25 (often you get this as a
        result of pointing camera at the sun or from a reflection off of a car or window)
        :param overwrite_file: whether or not to replace the values in info.json with these new ones
        """
        idxs_to_replace = []
        for i in range(len(self.highest)):
            if self.highest[i] > thresh:
                idxs_to_replace.append(i)

        for i in range(len(idxs_to_replace)):
            look_lower_index = i < len(idxs_to_replace) / 2
            if look_lower_index:
                self.highest[idxs_to_replace[i]] = self.highest[idxs_to_replace[0] - 1]
            else:
                self.highest[idxs_to_replace[i]] = self.highest[idxs_to_replace[-1] + 1]

        if overwrite_file:
            with open(self.directory_path + "/info.json", "r+") as f:
                info: Dict = json.loads(f.read())
                info["highestTemperatures"] = self.highest
                f.truncate(0)
                f.write(json.dumps(info))

    def match_local_with_global_temps(self, local_temps: List[float]) -> List[float]:
        """
        the color map temps and the global temps will not match perfectly...so find closest and change local temp
        to same value as closest global temp
        :param local_temps: the temperatures from the temperature/color map
        :return adjusted_local_temps: list of temperatures
        """
        global_temps: np.ndarray = np.array(list(self.global_color_map.keys()))
        adjusted_local_temps: List[float] = []
        for n in range(len(local_temps)):
            loc_temp: float = local_temps[n]
            differences: np.ndarray = abs(global_temps - loc_temp)
            idx: int = np.where(differences == np.amin(differences))[0][0]
            adjusted_local_temps.append(global_temps[idx])
        return adjusted_local_temps

    def get_global_temp_color_map(self) -> Dict[float, Color]:
        """
        uses lowest temperature among all images and highest temperature among all images to get a global temperature
        color map
        :return: dictionary {temperature: [b, g, r], ...}
        """
        return self.get_temp_color_map(min(self.lowest), max(self.highest))

    def get_temp_color_map(self, low, high) -> Dict[float, Color]:
        """
        uses lowest temperature and highest temperature to get a temperature color map
        :param low: lowest temperature
        :param high: highest temperature
        :return: dictionary {temperature: [b, g, r], ...}
        """
        step_size: float = (high - low) / (len(self.palette) - 1)
        return dict(zip([low + i * step_size for i in range(len(self.palette))], self.palette))

    def rescale_image(self, img_num: int) -> np.ndarray:
        """
        scales the colors in all images based on the lowest and highest temperature among all the pictures
        :param img_num: 0, 1, 2, ..., n the image number is used to grab the image file and the temperature data
        :return: the rescaled image
        """
        self.global_color_map: Dict[float, Color] = self.get_global_temp_color_map()

        img_num_str: str = util.make_double_digit_str(img_num)
        img: np.ndarray = cv2.imread(self.directory_path + "/ir{0}.png".format(img_num_str))

        # get colors and temperatures separately
        color_map_orig: Dict[float, Color] = self.get_temp_color_map(self.lowest[img_num], self.highest[img_num])  # gets temperature to color
        local_temps: List[float] = list(color_map_orig.keys())
        adjusted_local_temps: List[float] = self.match_local_with_global_temps(local_temps)
        # remakes the color map so that the temperatures now match up with the global temperatures
        color_map: Dict[Color, float] = dict(zip(self.palette, adjusted_local_temps))  # color to temperature
        # map local color to the global color
        local_color_to_global: Dict[Color, Color] = {}
        for color in color_map:
            local_color_to_global[color] = self.global_color_map[color_map[color]]

        rescaled_image: np.ndarray = np.zeros(img.shape)

        # make sure colors in image match the palette exactly
        image_obj: Image.Image = Image.Image(img)
        image_obj.set_colors_to_palette(self.palette)

        # replace local colors with global colors row by row
        for x in range(img.shape[1]):
            rescaled_image[:, x] = util.replace(image_obj.img[:, x].astype(np.float64), local_color_to_global)

        return rescaled_image


def main():
    NUM_IMGS = 45

    print("*** SELECT folder containing all images ***")
    directory = open_directory_chooser()  # pop-up file chooser
    # directory = "/Users/ccuser/Desktop/AmosDecker/ir/images/pano-20200109115026"
    print(directory)
    pano_num = directory[-14:]

    start = time.time()

    r = Rescaler(directory)
    print(r.get_global_temp_color_map())
    all_rescaled = []
    for i in range(NUM_IMGS):
        print(str(i + 1) + "/" + str(NUM_IMGS))
        all_rescaled.append(r.rescale_image(i))

    print("total time:", time.time() - start)

    print("*** CHOOSE save location (a directory called rescaled-[pano num] will be created there) ***")
    save_location = open_directory_chooser()
    if not os.path.isdir(save_location + "/rescaled-" + pano_num):
        os.makedirs(save_location + "/rescaled-" + pano_num)
    for i in range(NUM_IMGS):
        img_num_str = util.make_double_digit_str(i)
        cv2.imwrite(save_location + "/rescaled-{0}/ir{1}.png".format(pano_num, img_num_str), all_rescaled[i])


if __name__ == "__main__":
    main()


