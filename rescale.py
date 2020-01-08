"""
author: Amos Decker

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


class Rescaler:
    def __init__(self, directory_path):
        self.directory_path = directory_path

        # convert palette to bgr. originally in YCbCr
        with open("iron.pal") as f:
            self.palette = [tuple([int(y) for y in x.split(",")]) for x in f.read().split()]
            for i in range(len(self.palette)):
                c = self.palette[i]
                r = int(c[0] + 1.40200 * (c[1] - 128))
                g = int(c[0] - 0.34414 * (c[2] - 128) - 0.71414 * (c[1] - 128))
                b = int(c[0] + 1.77200 * (c[2] - 128))
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))

                self.palette[i] = (b, g, r)  # need to save palette in bgr format, not rgb

        # grab temperature extremes
        with open(directory_path + "/info.json") as f:
            info = json.loads(f.read())
            self.highest = info["highestTemperatures"]
            self.lowest = info["lowestTemperatures"]

        self.global_color_map = self.get_global_temp_color_map()

    def rescale_image(self, img_num):
        """
        scales the colors in all images based on the lowest and highest temperature among all the pictures
        :param img_num: 0, 1, 2, ..., n the image number is used to grab the image file and the temperature data
        :param global_color_map: dictionary {temperature: color}. Has the full range of temps among all images
        :return: the rescaled image
        """
        img_num_str = str(img_num) if img_num > 9 else "0" + str(img_num)
        img = cv2.imread(self.directory_path + "/ir{0}.png".format(img_num_str))

        # get colors and temperatures separately
        color_map = self.get_temp_color_map(self.lowest[img_num],
                                            self.highest[img_num])  # gets temperature to color
        local_temps = list(color_map.keys())

        rescaled_image = np.zeros(img.shape)

        # the color map temps and the global temps will not match perfectly...so find closest and match them up
        global_temps = list(self.global_color_map.keys())
        adjusted_local_temps = []
        for n in range(len(local_temps)):
            loc_temp = local_temps[n]
            temp_diff = 100000000000000000000000000000000
            idx_lowest_temp_diff = 0
            for i in range(len(global_temps)):
                diff = abs(global_temps[i] - loc_temp)
                if diff < temp_diff:
                    temp_diff = diff
                    idx_lowest_temp_diff = i
            adjusted_local_temps.append(global_temps[idx_lowest_temp_diff])

        # remakes the color map so that the temperatures now match up with the global temperatures
        color_map = dict(zip(self.palette, adjusted_local_temps))  # color to temperature

        image_to_map_temp = {}  # the rgb values don't match up perfectly for some reason,
                            # this stores the correspondence with the temperature of the closest color in the map
                            # key is bgr of img, value is temperature of color map
        for y in range(img.shape[0]):
            for x in range(img.shape[1]):
                if tuple(img[y, x]) not in image_to_map_temp:
                    # the rgb values don't match up perfectly for some reason. finds the closest set of rgb
                    color_diff = 100000000000000000000000000000000
                    idx_lowest_color_diff = 0
                    for i in range(len(self.palette)):
                        rgb = self.palette[i]
                        diff = abs(rgb[0] - img[y, x][0]) + abs(rgb[1] - img[y, x][1]) + abs(rgb[2] - img[y, x][2])
                        if diff < color_diff:
                            color_diff = diff
                            idx_lowest_color_diff = i

                    palette_color = self.palette[idx_lowest_color_diff]
                    temperature = color_map[palette_color]

                    image_to_map_temp[tuple(img[y, x])] = temperature
                else:
                    temperature = image_to_map_temp[tuple(img[y, x])]

                rescaled_image[y, x] = self.global_color_map[temperature]

        return rescaled_image

    def get_global_temp_color_map(self):
        """
        uses lowest temperature among all images and highest temperature among all images to get a global temperature
        color map
        :return: dictionary {temperature: [b, g, r], ...}
        """
        return self.get_temp_color_map(min(self.lowest), max(self.highest))

    def get_temp_color_map(self, low, high):
        """
        uses lowest temperature and highest temperature to get a temperature color map
        :param low: lowest temperature
        :param high: highest temperature
        :return: dictionary {temperature: [r, g, b], ...}
        """
        step_size = (high - low) / (len(self.palette) - 1)
        return dict(zip([low + i * step_size for i in range(len(self.palette))], self.palette))


def swap_dict(d):
    """switches keys with values in a dictionary"""
    return dict((v, k) for k, v in d.items())


if __name__ == "__main__":
    num_imgs = 45
    print("*** SELECT folder containing all images ***")
    directory = open_directory_chooser()  # pop-up file chooser
    pano_num = directory[-14:]

    start = time.time()

    r = Rescaler("pano-" + pano_num)
    all_rescaled = []
    for i in range(num_imgs):
        print(str(i + 1) + "/" + str(num_imgs))
        img_num_str = str(i) if i > 9 else "0" + str(i)
        all_rescaled.append(r.rescale_image(i))

    print("total time:", time.time() - start)

    print("*** CHOOSE save location ***")
    save_location = open_directory_chooser()
    if not os.path.isdir(save_location + "/rescaled-" + pano_num):
        os.makedirs(save_location + "/rescaled-" + pano_num)
    for i in range(num_imgs):
        img_num_str = str(i) if i > 9 else "0" + str(i)
        cv2.imwrite(save_location + "/rescaled-{0}/ir{1}.png".format(pano_num, img_num_str), all_rescaled[i])


