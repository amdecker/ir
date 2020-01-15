__author__ = "Amos Decker"
__date__ = "January 2020"

"""
1 rescale
2 stitch
3 set_colors_to_palette
4 (optional) change palette)
"""

import time
from rescale import Rescaler
import util
import cv2
import StitcherEasy
import Image
import numpy as np

def get_images(directory, type, NUM_IMGS):
    """

    :param directory: path to directory
    :param type: "vl", "ir", or "mx"
    :param NUM_IMGS: number of images to grab
    :return: list of images
    """
    return [cv2.imread(directory + "/{0}{1}.png".format(type, i)) if i > 9 else
            cv2.imread(directory + "/{0}0{1}.png".format(type, i)) for i in range(NUM_IMGS)]


def make_all_palettes():
    """
    take one image and apply all the different palettes to it
    :return:
    """
    for pal in util.PALETTES:
        print(pal)
        img = cv2.imread("/Users/ccuser/Desktop/AmosDecker/ir/images/cool_messup.png")
        cv2.imwrite("images/20200108143302-{0}.png".format(pal[:-4]), Image.Image(img).change_palette(pal).img)


def main():
    NUM_IMGS = 45
    REMOVE_BLACK = True
    INIT_PALETTE = "iron.pal"  # the palette that the original individual pano pictures are in (if unknown, can always use util.identify_palette()

    directory = util.open_directory_chooser()
    pano_num = directory[-14:]

    start = time.time()

    #######
    # RESCALE images -- makes the colors that you see represent the same temperatures across all images
    #######
    print("\nRESCALE...")
    r = Rescaler(directory)
    all_rescaled = []
    for i in range(NUM_IMGS):
        print(str(i + 1) + "/" + str(NUM_IMGS))
        all_rescaled.append(r.rescale_image(i))


    #######
    # STITCH images
    ######
    print("\nSTITCH...")
    images_to_stitch = []
    for type in ["vl", "mx"]:
        images_to_stitch.append(get_images(directory, type, NUM_IMGS))
    images_to_stitch.append(all_rescaled)

    panos = StitcherEasy.stitch(images_to_stitch, use_kaze=True)  # if the stitch fails try changing kaze to False/True

    for i in range(len(panos)):
        panos[i] = panos[i].astype(np.uint8)  # uint8 is same type as when you read img from a file

    # get rid of black border
    if REMOVE_BLACK:
        # the ir image wont ever have black pixels other than the border to get rid of so just get limits for that one
        im = Image.Image(panos[-1])
        upper_limit, lower_limit = im.remove_black()
        panos[-1] = im.img
        for i in range(len(panos) - 1):
            panos[i] = panos[i][upper_limit:lower_limit, :]

    ir_pano = Image.Image(panos[-1])
    #######
    # CHANGE ir pano to match colors in the palette (the stitching process changes pixel data slightly, this corrects that)
    #######
    print("\nMATCH PALETTE...")
    ir_pano.set_colors_to_palette(util.palette_to_bgr("palettes/" + INIT_PALETTE))


    #######
    # CHANGE PALETTE (optional)
    ######
    if True:
        print("\nCHANGE PALETTE...")
        ir_pano.change_palette("lava.pal")


    #######
    # Create mixed ir/vl using my program, not FLIR's (optional)
    #######
    if True:
        print(panos[0])
        my_mx = Image.create_mx(panos[0], ir_pano.img)

    print("total time:", time.time() - start)
    ######
    # SAVE panos
    ######
    print("\nSAVING...")
    panos[-1] = ir_pano.img
    save_directory = "images"  # util.open_directory_chooser()
    cv2.imwrite(save_directory + "/" + pano_num + "-vl.png", panos[0])
    cv2.imwrite(save_directory + "/" + pano_num + "-mx.png", panos[1])
    cv2.imwrite(save_directory + "/" + pano_num + "-ir.png", panos[2])
    cv2.imwrite(save_directory + "/" + pano_num + "-mymx.png", my_mx)



if __name__ == "__main__":
    main()
    # make_all_palettes()