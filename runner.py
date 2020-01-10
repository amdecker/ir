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
        img = cv2.imread("/Users/ccuser/Desktop/AmosDecker/ir/images/20200108143302-ir.png")
        new_img = util.change_palette(img, pal)
        cv2.imwrite("images/20200108142729-{0}.png".format(pal[:-4]), new_img)


def main():
    NUM_IMGS = 45
    REMOVE_BLACK = True
    INIT_PALETTE = "iron.pal"  # the palette that the original individual pano pictures are in (if unknown, can always use util.identify_palette()

    directory = util.open_directory_chooser()
    pano_num = directory[-14:]

    start = time.time()

    #######
    # RESCALE individual images
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
    # get rid of black border
    if REMOVE_BLACK:
        for p in range(len(panos)):
            panos[p] = util.remove_black(panos[p])

    #######
    # CHANGE ir pano to match colors in the palette (the stitching process changes pixel data slightly, this corrects that)
    #######
    print("\nMATCH PALETTE...")
    panos[-1] = util.set_colors_to_palette(panos[-1], util.palette_to_bgr("palettes/" + INIT_PALETTE))


    #######
    # CHANGE PALETTE (optional)
    ######
    if False:
        print("\nCHANGE PALETTE...")
        panos[-1] = util.change_palette(panos[-1], "lava.pal")

    print("total time:", time.time() - start)
    ######
    # SAVE panos
    ######
    print("\nSAVING...")
    save_directory = "images"  # util.open_directory_chooser()
    cv2.imwrite(save_directory + "/" + pano_num + "-vl.png", panos[0])
    cv2.imwrite(save_directory + "/" + pano_num + "-mx.png", panos[1])
    cv2.imwrite(save_directory + "/" + pano_num + "-ir.png", panos[2])



if __name__ == "__main__":
    #main()
    make_all_palettes()