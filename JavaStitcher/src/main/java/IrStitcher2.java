import org.bytedeco.javacpp.IntPointer;
import org.bytedeco.opencv.opencv_core.*;
import org.bytedeco.opencv.opencv_features2d.KAZE;
import org.bytedeco.opencv.opencv_features2d.ORB;
import org.bytedeco.opencv.opencv_stitching.*;

import java.util.Arrays;
import java.util.Date;

import static org.bytedeco.opencv.global.opencv_core.*;
import static org.bytedeco.opencv.global.opencv_imgcodecs.imread;


import static org.bytedeco.opencv.global.opencv_imgcodecs.imwrite;
import static org.bytedeco.opencv.global.opencv_imgproc.*;
import static org.bytedeco.opencv.global.opencv_stitching.*;

public class StitcherIR6
{
    public int OK = 0;
    public int ERR_NEED_MORE_IMGS = 1;
    public int ERR_HOMOGRAPHY_EST_FAIL = 2;
    public int ERR_CAMERA_PARAMS_ADJUST_FAIL = 3;
    public int ORIG_RESOL = -1;

    private MatVector imgs = new MatVector();


    public static Mat stitch(MatVector vlPhotos)
    {
        float workMegapix = -1;
        float seamMegapix = (float) 0.1;
        float composeMegapix = -1;
        String strRefineMask = "xxxxx";
//        String waveCorrect = "horiz"; // "vert"
        String warpType = "cylindrical"; //"spherical"
        float matchConf = (float) 0.3;
        String blendType = "feather"; // multiband, none

        int blendStrength = 5;
        float seamWorkAspect = 1;
        float confThresh = 1;

        float workScale = -1;
        double seamScale = -1;

        Stitcher stitcher = Stitcher.create();
        stitcher.setFeaturesFinder(ORB.create());
        for(int i = 0; i < vlPhotos.size(); i++) //TODO lots of unused stuff here
        {
            boolean seamScaleSet = seamScale < 0;
            boolean workScaleSet = workScale < 0;
            Mat img = new Mat();

            if (workMegapix < 0)
            {
                img = vlPhotos.get(i);
                workScale = 1;
            }
            else
            {
                if (!workScaleSet)
                {
                    workScale = (float) Math.min(1.0, Math.sqrt(workMegapix * 1e6 / vlPhotos.get(i).size().area()));
                }
                resize(vlPhotos.get(i).clone(), img, img.size(), workScale, workScale, INTER_LINEAR_EXACT);
            }
            if (!seamScaleSet)
            {
                seamScale = Math.min(1.0, Math.sqrt(seamMegapix * 1e6 / vlPhotos.get(i).size().area()));
                seamWorkAspect = (float) seamScale / workScale;
            }
        }
        System.out.println("getting features...");
        ImageFeatures features = new ImageFeatures(vlPhotos.size());

        computeImageFeatures(stitcher.featuresFinder(), vlPhotos, features);

        System.out.println("getting matches...");
        double[][] matchMask = new double[(int) vlPhotos.size()][(int) vlPhotos.size()];
        for(int row = 0; row < matchMask.length; row++)
        {
            for(int col = 0; col < matchMask[0].length; col++)
            {
                matchMask[row][col] = 255;
            }
        }
        for(int i = 0; i < matchMask.length - 1; i++)
        {
            matchMask[i][i + 1] = 1;
        }

        MatchesInfo matchesInfo = new MatchesInfo(vlPhotos.size());
        UMat mat = StitcherIR5.arrayToMat(matchMask, CV_8U).getUMat(ACCESS_READ);
        System.out.println("here");
//        stitcher.setFeaturesMatcher(new BestOf2NearestRangeMatcher());
//        stitcher.featuresMatcher().apply2(features, matchesInfo);
        stitcher.featuresMatcher().apply2(features, matchesInfo, mat);
        stitcher.featuresMatcher().collectGarbage();
//        System.exit(0);

        // retain images that are definitely part of the pano
        System.out.println("getting indices...");
        IntPointer indices = leaveBiggestComponent(features, matchesInfo, (float)stitcher.panoConfidenceThresh());
        System.out.println("indices:");
        int[] ints = indices.getStringCodePoints();
        System.out.println(Arrays.toString(ints));

        MatVector vlSubset = new MatVector();
//        MatVector irSubset = new MatVector();
//        MatVector mxSubset = new MatVector();

        for(int i = 0; i < indices.capacity(); i++)
        {
            vlSubset.push_back(vlPhotos.get(ints[i]));
//            irSubset.push_back(irPhotos.get(ints[i]));
//            mxSubset.push_back(mxPhotos.get(ints[i]));
        }
        vlPhotos = vlSubset;

        System.out.println("size vl: " + vlPhotos.size());
//        System.out.println("size ir: " + irSubset.size());
//        System.out.println("size mx: " + mxSubset.size());
        if(vlPhotos.size() < 2)
        {
            System.out.println("need more images");
            System.exit(0);
        }


        // get camera params
        System.out.println("getting camera parameters...");
        CameraParams cameraParams = new CameraParams(vlPhotos.size());
        features.position(0);
        matchesInfo.position(0);
        cameraParams.position(0);
        boolean success = stitcher.estimator().apply(features, matchesInfo, cameraParams);
        if(!success)
        {
            System.out.println("homography estimation failed :(");
            System.exit(0);
        }

        // convert R
        for(int i = 0; i < cameraParams.capacity(); i++)
        {
            Mat R = new Mat();
            cameraParams.position(i).R().convertTo(R, CV_32F);
            cameraParams.position(i).R(R);
        }
        cameraParams.position(0);

        System.out.println("bundle adjustment...");
//        stitcher.bundleAdjuster().setRefinementMask(StitcherIR5.arrayToMat(new double[][]{{1, 1, 1}, {0, 1, 1}, {0, 0, 0}}, CV_8U));
        System.out.println(stitcher.bundleAdjuster().confThresh());
//        stitcher.setPanoConfidenceThresh(0.3);
//        stitcher.bundleAdjuster().setConfThresh(0.3);
        System.out.println(stitcher.bundleAdjuster().confThresh());
//        System.out.println(stitcher.setBundleAdjuster(new BundleAdjusterRay());
        success = stitcher.bundleAdjuster().apply(features, matchesInfo, cameraParams);
//        BundleAdjusterReproj adjuster = new BundleAdjusterReproj();
//        NoBundleAdjuster adjuster = new NoBundleAdjuster();
//        BundleAdjusterRay adjuster = new BundleAdjusterRay();
//        adjuster.setConfThresh(0.);
//        success = adjuster.apply(features, matchesInfo, cameraParams);
        if(!success)
        {
            System.out.println("Bundle Adjustment failed :(");
            System.exit(0);
        }

        System.out.println("focal length...");
        // find median focal length
        double[] focals = new double[(int)cameraParams.capacity()];
        for(int i = 0; i < focals.length; i++)
        {
            focals[i] = cameraParams.position(i).focal();
        }
        cameraParams.position(0);
        Arrays.sort(focals);
        boolean oddLength = focals.length % 2 != 0;
        float warpedImageScale;
        if(oddLength)
        {
            warpedImageScale = (float)focals[focals.length / 2];
        }
        else
        {
            warpedImageScale = (float)(focals[focals.length / 2 - 1] + focals[focals.length / 2]) / 2;
        }

        MatVector rMats = new MatVector();
        System.out.println("CAM PARAM CAP: " + cameraParams.capacity());
        for(int i = 0; i < cameraParams.capacity(); i++)
        {
            rMats.push_back(cameraParams.position(i).R().clone());
        }
        cameraParams.position(0);
        rMats.position(0);
        waveCorrect(rMats, WAVE_CORRECT_HORIZ);
        for(int i = 0; i < cameraParams.capacity(); i++)
        {
            cameraParams.position(i).R(rMats.get(i));
        }
        cameraParams.position(0);


        // compose panorama
        System.out.println("compose panorama...");
        PointVector corners = new PointVector();
        UMatVector masksWarped = new UMatVector();
        UMatVector imagesWarped = new UMatVector();
        SizeVector sizes = new SizeVector();
        UMatVector masks = new UMatVector();

        // Prepare image masks
        for (int i = 0; i < vlPhotos.size(); i++)
        {
            masks.push_back(new Mat(new int[]{vlPhotos.get(i).size().height(), vlPhotos.get(i).size().width()}, CV_8U, Scalar.all(255)).getUMat(ACCESS_READ));
        }
        masks.position(0);
        // warp images and masks
        RotationWarper warper = new CylindricalWarper().create(warpedImageScale * seamWorkAspect);//new RotationWarper(warpedImageScale * seamWorkAspect);
        for(int i = 0; i < vlPhotos.size(); i++)
        {
            double[][] K_arr = StitcherIR5.matToArray(cameraParams.position(i).K().clone());
            K_arr[0][0] *= seamWorkAspect;
            K_arr[0][2] *= seamWorkAspect;
            K_arr[1][1] *= seamWorkAspect;
            K_arr[1][2] *= seamWorkAspect;
            Mat K = StitcherIR5.arrayToMat(K_arr, CV_32F);

            Mat imgWarped = new Mat();
            corners.push_back(warper.warp(vlPhotos.get(i), K, cameraParams.position(i).R(), INTER_LINEAR, BORDER_REFLECT, imgWarped));
            imagesWarped.push_back(imgWarped.getUMat(ACCESS_READ));

            sizes.push_back(imgWarped.size());

            Mat maskWarped = new Mat();
            warper.warp(masks.get(i).getMat(ACCESS_READ), K, cameraParams.position(i).R(), INTER_NEAREST, BORDER_CONSTANT, maskWarped);
            masksWarped.push_back(maskWarped.getUMat(ACCESS_READ));
        }
        corners.position(0);
        imagesWarped.position(0);
        sizes.position(0);
        masksWarped.position(0);

//        // Compensate exposure before finding seams
//        ExposureCompensator compensator = ExposureCompensator.createDefault(ExposureCompensator.GAIN_BLOCKS);
//        compensator.feed(corners, imagesWarped, masksWarped);
//        for(int i = 0; i < vlPhotos.size(); i++)
//        {
//            compensator.apply(i, corners.get(i), imagesWarped.get(i), masksWarped.get(i));
//        }
//
//        // Find seams
//        UMatVector imagesWarpedF = new UMatVector(vlPhotos.size());
//        for(int i = 0; i < vlPhotos.size(); i++)
//        {
//            UMat iwf = new UMat();
//            imagesWarped.get(i).convertTo(iwf, CV_32F);
//            imagesWarpedF.push_back(iwf);
//        }
//        SeamFinder seamFinder = SeamFinder.createDefault(GraphCutSeamFinderBase.COST_COLOR);
//        seamFinder.find(imagesWarpedF, corners, masksWarped);

        // Release unused memory
//        imagesWarped.clear();
////        imagesWarpedF.clear();
//        masks.clear();

        UMat imgWarped   = new UMat();
        UMat imgWarpedS  = new UMat();
        UMat dilatedMask = new UMat();
        UMat seamMask    = new UMat();
        UMat mask        = new UMat();
        UMat maskWarped  = new UMat();

        float composeWorkAspect = 1;
        float composeScale = 1;
        boolean blenderIsSetup = false;
        boolean composeScaleSet = false;

//        CameraParams cameraParamsScaled = new CameraParams();

        UMat fullImg = new UMat();
        UMat img = new UMat();
        System.out.println("starting loop");
        Blender blender = Blender.createDefault(Blender.MULTI_BAND);
        for(int imgIdx = 0; imgIdx < vlPhotos.size(); imgIdx++)
        {
            fullImg = vlPhotos.get(imgIdx).getUMat(ACCESS_READ);
            if(!composeScaleSet)
            {
                //TODO if(composeResol)
                composeScaleSet = true;

                composeWorkAspect = composeScale / workScale;
                warper = new CylindricalWarper().create(warpedImageScale * composeWorkAspect);
                corners.clear();
                sizes.clear();
                corners.position(0);
                sizes.position(0);
                System.out.println("before: " + sizes.get().length);

//                corners = new PointVector();
//                sizes =  new SizeVector();

//                PointVector corners2 = new PointVector();
//                SizeVector sizes2 = new SizeVector();
                // Update corners and sizes
                System.out.println("update corners and sizes");
                for (int i = 0; i < vlPhotos.size(); ++i)
                {
                    System.out.println(i); // TODO errro in here
                    // Update intrinsics

//                    cameraParamsScaled.position(i).ppx(
//                            cameraParamsScaled.position(i).ppx() * composeWorkAspect
//                    );
//                    cameraParamsScaled.position(i).ppy(
//                            cameraParamsScaled.position(i).ppy() * composeWorkAspect
//                    );
//                    cameraParamsScaled.position(i).focal(
//                            cameraParamsScaled.position(i).focal() * composeWorkAspect
//                    );
                    cameraParams.position(i).ppx(
                            cameraParams.position(i).ppx() * composeWorkAspect
                    );
                    cameraParams.position(i).ppy(
                            cameraParams.position(i).ppy() * composeWorkAspect
                    );
                    cameraParams.position(i).focal(
                            cameraParams.position(i).focal() * composeWorkAspect
                    );
                    // Update corner and size
                    Size sz = vlPhotos.get(i).size();
                    if (Math.abs(composeScale - 1) > 1e-1)
                    {
                        sz.width(cvRound(sz.width() * composeScale));
                        sz.height(cvRound(sz.height() * composeScale));
                    }

                    Mat K = new Mat();
                    cameraParams.position(i).K().convertTo(K, CV_32F);
                    Rect roi = warper.warpRoi(sz, K, cameraParams.position(i).R());

                    System.out.println(roi.tl().x() + ", " + roi.tl().y());
                    corners.push_back(roi.tl());
                    System.out.println(roi.size().area());

                    sizes.push_back(roi.size());
                }
            }
            corners.position(0);
            sizes.position(0);
            if(Math.abs(composeScale - 1) > 1e-1)
            {
                resize(vlPhotos.get(imgIdx).getUMat(ACCESS_READ), img, img.size(), composeScale, composeScale, INTER_LINEAR_EXACT);
            }
            else
            {
                img = vlPhotos.get(imgIdx).getUMat(ACCESS_READ);
            }
            Size img_size = img.size();
            Mat K = new Mat();
//            cameraParamsScaled.position(imgIdx).K().convertTo(K, CV_32F);
            cameraParams.position(imgIdx).K().convertTo(K, CV_32F);

            warper.warp(img, K.getUMat(ACCESS_READ), cameraParams.position(imgIdx).R().getUMat(ACCESS_READ), INTER_LINEAR, BORDER_REFLECT, imgWarped);

            // Warp the current image mask
            mask = new Mat(img.size(), CV_8U, Scalar.all(255)).getUMat(ACCESS_READ);
            warper.warp(mask, K.getUMat(ACCESS_READ), cameraParams.position(imgIdx).R().getUMat(ACCESS_READ), INTER_NEAREST, BORDER_CONSTANT, maskWarped);

//                compensator.apply(imgIdx, corners.get(imgIdx), imgWarped, maskWarped);

            imgWarped.convertTo(imgWarpedS, CV_16S);
            imgWarped.release();
            img.release();
            mask.release();

            // Make sure seam mask has proper size
            dilate(masksWarped.get(imgIdx), dilatedMask, new UMat());
            resize(dilatedMask, seamMask, maskWarped.size(), 0, 0, INTER_LINEAR_EXACT);
            bitwise_and(seamMask, maskWarped, maskWarped);

            if (!blenderIsSetup)
            {
                System.out.println("sizes: " + sizes.get().length);
                System.out.println("corners: " + corners.get().length);

                blender.prepare(corners, sizes);
                blenderIsSetup = true;
            }
            blender.feed(imgWarpedS, maskWarped, corners.get(imgIdx));
        }
        System.out.println("BLENDING...");
        UMat result = new UMat();
        UMat resultMask = new UMat();
        blender.blend(result, resultMask);
        Mat pano = new Mat();
        result.convertTo(pano, CV_8U);
        return pano;
//        blender_->blend(result, result_mask_);
//        LOGLN("blend time: " << ((getTickCount() - blend_t) / getTickFrequency()) << " sec");
//
//        LOGLN("Compositing, time: " << ((getTickCount() - t) / getTickFrequency()) << " sec");
//
//        // Preliminary result is in CV_16SC3 format, but all values are in [0,255] range,
//        // so convert it to avoid user confusing
//        result.convertTo(pano, CV_8U);
        }

    public static void main(String[] args)
    {
        long start = System.currentTimeMillis();
        System.out.println("start: " + new Date(start));
        MatVector vlPhotos = new MatVector();//readImages("/Users/ccuser/Desktop/ir_video/pano12/", ".png");
        MatVector irPhotos = new MatVector();
        MatVector mxPhotos = new MatVector();

//        String num = "17";
//        System.out.println("NUM: " + num);
        //"/Users/ccuser/Desktop/bostonPanos/7/pano-20190724114828"
//        String path = "/Users/ccuser/Desktop/bostonPano/3/pano-20190724155303"; //20190724153320, 20190724153638, 20190724153959, 20190724154251, 20190724155303
        String path = "/Users/ccuser/Desktop/old amos code/ir_video/pano"; // works with ORB
        for(int i = 0; i < 45; i++)
        {
            if(i < 10)
            {
                vlPhotos.push_back(imread(path + "/vl0" + i + ".png"));
                irPhotos.push_back(imread(path + "/ir0" + i + ".png"));
                mxPhotos.push_back(imread(path + "/mx0" + i + ".png"));
            }
            else
            {
                vlPhotos.push_back(imread(path + "/vl" + i + ".png"));
                irPhotos.push_back(imread(path + "/ir" + i + ".png"));
                mxPhotos.push_back(imread(path + "/mx" + i + ".png"));
            }
        }
        Mat pano = stitch(vlPhotos);
//        Mat pano = RunnerWorkingIThink.stitcher(photos);
        imwrite("_320.png", pano);

//        System.out.println("my pano...");
//        Mat myPano = stitch(photos);
//        imwrite("/Users/ccuser/Desktop/ir_video/panos/output/0mine.png", myPano);


//        IrStitcher stitcher = new IrStitcher(photos, irPhotos, mxPhotos);
//        Mat[] panos = stitcher.stitch();
//
//        System.out.println("Saving...");
//        String[] types = new String[]{"vl", "ir", "mx"};
//        for (int i = 0; i < panos.length; i++)
//        {
//            imwrite("/Users/ccuser/Desktop/ir_video/panos/output/" + num + "SIFT-" + types[i] + ".png", panos[i]);
//        }
//
//        System.out.println("total time: " + (System.currentTimeMillis() - start) / 1000);
        System.out.println("total time: " + (System.currentTimeMillis() - start) / 1000);

        //TODO use different feature detector like sift
    }

}
