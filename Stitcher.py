"""
author: Amos Decker

A working python stitcher for ir images. Uses visible light images to find the keypoints and do all of the adjustments,
but then swaps out the visible light images for ir images.

Current implementation produces ir, vl, and mixed panoramas, but producing the final pano for any/all of them is not necessary.


modified version of these:
https://raw.githubusercontent.com/opencv/opencv/master/samples/python/stitching_detailed.py
https://raw.githubusercontent.com/opencv/opencv/master/samples/cpp/stitching_detailed.cpp
"""

import numpy as np
import cv2
import time

def stitch(data):

    start = time.time()
    use_gpu = False
    work_megapix = -1
    seam_megapix = 0.1
    compose_megapix = -1
    ba_refine_mask = "xxxxx"
    wave_correct = "horiz"  # "vert"
    warp_type = "cylindrical"  # "spherical"  #"mercator"
    match_conf = 0.3
    blend_type = "feather"  # feather  # multiband # for no blending at all put any other string, like "no"
    blend_strength = 5

    finder = cv2.ORB.create()

    seam_work_aspect = 1
    features = []
    images = []
    print("getting image features and scaling images...")
    work_scale = -1
    seam_scale = -1
    for i in range(len(vl_imgs)):
        full_img = vl_imgs[i]

        if work_megapix < 0:
            img = full_img
            work_scale = 1
        else:
            if work_scale == -1:  # if it hasn't been set yet
                work_scale = min(1.0, np.sqrt(work_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
            img = cv2.resize(src=full_img, dsize=None, fx=work_scale, fy=work_scale, interpolation=cv2.INTER_LINEAR_EXACT)
        if seam_scale == -1:  # if it hasn't been set yet
            seam_scale = min(1.0, np.sqrt(seam_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
            seam_work_aspect = seam_scale / work_scale
        features.append(cv2.detail.computeImageFeatures2(finder, img))  # gets image features
        images.append(cv2.resize(src=full_img, dsize=None, fx=seam_scale, fy=seam_scale, interpolation=cv2.INTER_LINEAR_EXACT))

    print("getting matches info...")
    matcher = cv2.detail.BestOf2NearestMatcher_create(use_gpu, match_conf)
    matches_info = matcher.apply2(features)
    matcher.collectGarbage()

    # gets the images that have enough matches and are part of the pano
    print("getting indices...")
    indices = cv2.detail.leaveBiggestComponent(features, matches_info, 0.3)
    img_subset = []
    for i in range(len(indices)):
        img_subset.append(images[indices[i, 0]])
    images = img_subset
    num_images = len(images)

    if num_images < 2:
        print("Need more images")
        exit()

    # get camera params
    print("finding camera params...")
    estimator = cv2.detail_HomographyBasedEstimator()
    b, cameras = estimator.apply(features, matches_info, None)
    if not b:
        print("Homography estimation failed.")
        exit()
    for cam in cameras:
        cam.R = cam.R.astype(np.float32)

    # adjust camera params
    print("adjusting camera params...")
    adjuster = cv2.detail_BundleAdjusterRay()
    adjuster.setConfThresh(1)
    refine_mask = np.zeros((3, 3), np.uint8)
    if ba_refine_mask[0] == 'x':
        refine_mask[0, 0] = 1
    if ba_refine_mask[1] == 'x':
        refine_mask[0, 1] = 1
    if ba_refine_mask[2] == 'x':
        refine_mask[0, 2] = 1
    if ba_refine_mask[3] == 'x':
        refine_mask[1, 1] = 1
    if ba_refine_mask[4] == 'x':
        refine_mask[1, 2] = 1
    adjuster.setRefinementMask(refine_mask)
    b, cameras = adjuster.apply(features, matches_info, cameras)
    if not b:
        print("Camera parameters adjusting failed.")
        exit()

    # get warped image scale
    print("getting warped image scale...")
    focals = []
    for cam in cameras:
        focals.append(cam.focal)
    sorted(focals)
    if len(focals) % 2 == 1:
        warped_image_scale = focals[len(focals) // 2]
    else:
        warped_image_scale = (focals[len(focals) // 2] + focals[len(focals) // 2 - 1]) / 2

    # wave correct. see section 5 of this paper: http://matthewalunbrown.com/papers/ijcv2007.pdf
    print("wave correction...")
    rmats = []
    for cam in cameras:
        rmats.append(np.copy(cam.R))
        
    if wave_correct == "horiz":
        rmats = cv2.detail.waveCorrect(rmats, cv2.detail.WAVE_CORRECT_HORIZ)
    elif wave_correct == "vert":
        rmats = cv2.detail.waveCorrect(rmats, cv2.detail.WAVE_CORRECT_VERT)
        
    for i in range(len(cameras)):
        cameras[i].R = rmats[i]

    masks_warped = []
    images_warped = []
    masks = []

    # create masks and fill with white pixels
    for i in range(num_images):
        um = cv2.UMat(255 * np.ones((images[i].shape[0], images[i].shape[1]), np.uint8))
        masks.append(um)

    # warp images and masks
    print("warping...")
    warper = cv2.PyRotationWarper(warp_type, warped_image_scale * seam_work_aspect)
    for i in range(num_images):
        K = cameras[i].K().astype(np.float32)
        K[0, 0] *= seam_work_aspect
        K[0, 2] *= seam_work_aspect
        K[1, 1] *= seam_work_aspect
        K[1, 2] *= seam_work_aspect

        corner, image_wp = warper.warp(images[i], K, cameras[i].R, cv2.INTER_LINEAR, cv2.BORDER_REFLECT)
        images_warped.append(image_wp)

        p, mask_wp = warper.warp(masks[i], K, cameras[i].R, cv2.INTER_NEAREST, cv2.BORDER_CONSTANT)
        masks_warped.append(mask_wp.get())

    # convert type
    images_warped_f = []
    for img in images_warped:
        imgf = img.astype(np.float32)
        images_warped_f.append(imgf)

    # blend images
    for res_name, imgs in data:
        corners = []
        sizes = []
        blender = None
        compose_scale = -1

        # compensate for exposure -- NOTE at the moment it doesn't do this,
        # but see https://docs.opencv.org/4.1.0/d2/d37/classcv_1_1detail_1_1ExposureCompensator.html for options
        compensator = cv2.detail.ExposureCompensator_createDefault(cv2.detail.ExposureCompensator_NO)
        compensator.feed(corners=corners, images=images_warped, masks=masks_warped)

        # find seams in the images -- NOTE just as with exposure this doesn't actually do anything
        # but there are other possibilities here: https://docs.opencv.org/4.1.0/d7/d09/classcv_1_1detail_1_1SeamFinder.html#aaefc003adf1ebec13867ad9203096f6fa55b2503305e94168c0b36c4531f288d7
        seam_finder = cv2.detail.SeamFinder_createDefault(cv2.detail.SeamFinder_NO)
        seam_finder.find(images_warped_f, corners, masks_warped)

        for i in range(len(vl_imgs)):
            full_img = imgs[i]

            if compose_scale == -1:  # if it hasn't been set yet
                if compose_megapix > 0:
                    compose_scale = min(1.0, np.sqrt(compose_megapix * 1e6 / (full_img.shape[0] * full_img.shape[1])))
                else:
                    compose_scale = 1
                compose_work_aspect = compose_scale / work_scale
                warped_image_scale *= compose_work_aspect

                warper = cv2.PyRotationWarper(warp_type, warped_image_scale)
                for c in range(len(vl_imgs)):
                    cameras[c].focal *= compose_work_aspect
                    cameras[c].ppx *= compose_work_aspect
                    cameras[c].ppy *= compose_work_aspect

                    sz = (vl_imgs[c].shape[1] * compose_scale, vl_imgs[c].shape[0] * compose_scale)
                    K = cameras[c].K().astype(np.float32)
                    roi = warper.warpRoi(sz, K, cameras[c].R)
                    corners.append(roi[0:2])
                    sizes.append(roi[2:4])

            if abs(compose_scale - 1) > 1e-1:
                img = cv2.resize(src=full_img, dsize=None, fx=compose_scale, fy=compose_scale, interpolation=cv2.INTER_LINEAR_EXACT)
            else:
                img = full_img

            K = cameras[i].K().astype(np.float32)
            corner, image_warped = warper.warp(img, K, cameras[i].R, cv2.INTER_LINEAR, cv2.BORDER_REFLECT)
            mask = 255 * np.ones((img.shape[0], img.shape[1]), np.uint8)
            p, mask_warped = warper.warp(mask, K, cameras[i].R, cv2.INTER_NEAREST, cv2.BORDER_CONSTANT)
            compensator.apply(i, corners[i], image_warped, mask_warped)
            image_warped_s = image_warped.astype(np.int16)

            dilated_mask = cv2.dilate(masks_warped[i], None)
            seam_mask = cv2.resize(dilated_mask, (mask_warped.shape[1], mask_warped.shape[0]), 0, 0, cv2.INTER_LINEAR_EXACT)
            mask_warped = cv2.bitwise_and(seam_mask, mask_warped)

            # setup blender -- this sets up the part that combines the images by laying them on top of each other
            if blender is None:
                blender = cv2.detail.Blender_createDefault(cv2.detail.Blender_NO)
                dst_sz = cv2.detail.resultRoi(corners=corners, sizes=sizes)
                blend_width = np.sqrt(dst_sz[2] * dst_sz[3]) * blend_strength / 100
                if blend_width < 1:
                    blender = cv2.detail.Blender_createDefault(cv2.detail.Blender_NO)
                elif blend_type == "multiband":
                    blender = cv2.detail_MultiBandBlender()
                    blender.setNumBands((np.log(blend_width)/np.log(2.) - 1.).astype(np.int))
                elif blend_type == "feather":  # mixes images at borders
                    blender = cv2.detail_FeatherBlender()
                    blender.setSharpness(1.0 / blend_width)
                blender.prepare(dst_sz)

            blender.feed(cv2.UMat(image_warped_s), mask_warped, corners[i])

        result = None
        result_mask = None
        print("blending..." + res_name)
        result, result_mask = blender.blend(result, result_mask)
        cv2.imwrite(res_name, result)

    print('Done!')
    print("total time: " + str(time.time() - start))

if __name__ == '__main__':
    ir_imgs = [cv2.imread("pano/ir{0}.png".format(i)) if i > 9 else cv2.imread("pano/ir0{0}.png".format(i)) for i in range(44, -1, -1)]
    vl_imgs = [cv2.imread("pano/vl{0}.png".format(i)) if i > 9 else cv2.imread("pano/vl0{0}.png".format(i)) for i in range(44, -1, -1)]
    mx_imgs = [cv2.imread("pano/mx{0}.png".format(i)) if i > 9 else cv2.imread("pano/mx0{0}.png".format(i)) for i in range(44, -1, -1)]
    stitch([("panos/result0_ir.png", ir_imgs), ("panos/result0_vl.png", vl_imgs), ("panos/result0_mx.png", mx_imgs)])


