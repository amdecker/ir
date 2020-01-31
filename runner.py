__author__ = "Amos Decker"
__date__ = "January 2020"

import time
from rescale import Rescaler
import util
import cv2
import StitcherEasy
import Image
import numpy as np
from typing import List


def get_images(directory: str, type_img: str, NUM_IMGS: int):
    """

    :param directory: path to directory
    :param type_img: "vl", "ir", or "mx"
    :param NUM_IMGS: number of images to grab
    :return: list of images
    """
    return [cv2.imread(directory + "/{0}{1}.png".format(type_img, i)) if i > 9 else
            cv2.imread(directory + "/{0}0{1}.png".format(type_img, i)) for i in range(NUM_IMGS)]


def make_all_palettes(path_to_file: str, save_path: str):
    """
    take one image and apply all the different palettes to it
    """
    for pal in util.PALETTES:
        print(pal)
        img = cv2.imread(path_to_file)
        cv2.imwrite(save_path, Image.Image(img).change_palette(pal).img)


def main():
    """
    order of events...
    1 rescale
    2 stitch
        2.1 remove black border
    3 set_colors_to_palette
    4 (optional) change palette
    5 (optional) create mixed ir/vl image -- not relying on flir
    6 save!
    """
    start: float = time.time()

    ########
    # CONSTANTS
    ########
    NUM_IMGS: int = 45
    REMOVE_BLACK: bool = True
    INIT_PALETTE: str = "iron.pal"  # the palette that the original individual pano pictures are in (if unknown, can always use util.identify_palette()
    USE_FLIR_MX: bool = True
    CREATE_MY_MX: bool = True
    CHANGE_PALETTE: bool = False
    REPLACE_HIGH_TEMPS: bool = True  # when rescaling images change data to get rid of strangely high temperatures (like from reflections from the sun)
    if REPLACE_HIGH_TEMPS:
        OVERWRITE_FILE: bool = True  # whether or not to change the info.json file itself when replacing high temps
        THRESHOLD: float = 70

    directory: str = util.open_directory_chooser()
    pano_num: str = directory[-14:]


    #######
    # RESCALE images -- makes the colors that you see represent the same temperatures across all images
    #######
    print("\nRESCALE...")
    r: Rescaler = Rescaler(directory)
    if REPLACE_HIGH_TEMPS:
        r.replace_extreme_high_temps(thresh=THRESHOLD, overwrite_file=OVERWRITE_FILE)
    all_rescaled: List[np.ndarray] = []
    for i in range(NUM_IMGS):
        print(str(i + 1) + "/" + str(NUM_IMGS))
        all_rescaled.append(r.rescale_image(i))


    #######
    # STITCH images
    ######
    print("\nSTITCH...")
    if USE_FLIR_MX:
        types = ["vl", "mx"]
        images_to_stitch: List[List[np.ndarray], List[np.ndarray], List[np.ndarray]] = []
    else:
        types = ["vl"]
        images_to_stitch: List[List[np.ndarray], List[np.ndarray]] = []
    for t in types:
        images_to_stitch.append(get_images(directory, t, NUM_IMGS))
    images_to_stitch.append(all_rescaled)

    panos: List[np.ndarray] = StitcherEasy.stitch(images_to_stitch, use_kaze=True)  # if the stitch fails try changing kaze to False/True

    for i in range(len(panos)):
        panos[i] = panos[i].astype(np.uint8)  # uint8 is same type as when you read img from a file

    # get rid of black border
    if REMOVE_BLACK:
        # the ir image wont ever have black pixels other than the border so just get limits for that one
        im: Image.Image = Image.Image(panos[-1])
        upper_limit, lower_limit, removed_left, removed_right = im.remove_black()
        panos[-1] = im.img
        for i in range(len(panos) - 1):
            panos[i] = panos[i][upper_limit:lower_limit, :]
            if removed_left:
                panos[i] = panos[i][:, 1:]
            if removed_right:
                panos[i] = panos[i][:, :-1]

    ir_pano: Image.Image = Image.Image(panos[-1])

    #######
    # CHANGE ir pano to match colors in the palette (the stitching process changes pixel data slightly, this corrects that)
    #######
    print("\nMATCH PALETTE...")
    ir_pano.set_colors_to_palette(util.palette_to_bgr("palettes/" + INIT_PALETTE))

    #######
    # CHANGE PALETTE (optional)
    ######
    if CHANGE_PALETTE:
        print("\nCHANGE PALETTE...")
        ir_pano.change_palette("lava.pal")

    #######
    # Create mixed ir/vl using my program, not FLIR's (optional)
    #######
    if CREATE_MY_MX:
        my_mx: np.ndarray = Image.create_mx(panos[0], ir_pano.img)

    print("total time:", time.time() - start)
    ######
    # SAVE panos
    ######
    print("\nSAVING...")
    panos[-1] = ir_pano.img
    save_directory = util.open_directory_chooser()
    cv2.imwrite(save_directory + "/" + pano_num + "-vl.png", panos[0])
    cv2.imwrite(save_directory + "/" + pano_num + "-mx.png", panos[1])
    cv2.imwrite(save_directory + "/" + pano_num + "-ir.png", panos[2])
    cv2.imwrite(save_directory + "/" + pano_num + "-mymx.png", my_mx)


if __name__ == "__main__":
    main()
