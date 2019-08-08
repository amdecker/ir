import org.bytedeco.javacpp.IntPointer;
import org.bytedeco.javacpp.indexer.DoubleRawIndexer;
import org.bytedeco.javacpp.indexer.FloatIndexer;
import org.bytedeco.javacpp.indexer.FloatRawIndexer;
import org.bytedeco.javacpp.indexer.UByteRawIndexer;
import org.bytedeco.opencv.opencv_core.*;
import org.bytedeco.opencv.opencv_features2d.Feature2D;
import org.bytedeco.opencv.opencv_features2d.KAZE;
import org.bytedeco.opencv.opencv_features2d.ORB;
import org.bytedeco.opencv.opencv_stitching.*;
import org.bytedeco.opencv.opencv_xfeatures2d.SIFT;

import java.awt.*;
import java.util.Arrays;
import java.util.Date;

import static org.bytedeco.opencv.global.opencv_core.*;
import static org.bytedeco.opencv.global.opencv_imgcodecs.imread;
import static org.bytedeco.opencv.global.opencv_imgcodecs.imwrite;
import static org.bytedeco.opencv.global.opencv_imgproc.*;
import static org.bytedeco.opencv.global.opencv_stitching.*;

/**
 * @author Amos Decker
 * fast stitcher. Works on mac with ORB and that is about it. Doesn't work on windows.
 */
public class IrStitcher2
{
    public int OK = 0;
    public int ERR_NEED_MORE_IMGS = 1;
    public int ERR_HOMOGRAPHY_EST_FAIL = 2;
    public int ERR_CAMERA_PARAMS_ADJUST_FAIL = 3;
    public int ORIG_RESOL = -1;

    /**
     * creates a 2d Mat from an array. Array can't be jagged
     * @param m the array the Mat should be created from
     * @return
     */
    public static Mat arrayToMat(double[][] m, int type)
    {
        //CV_32F
        //CV_8UC1
        // CV_8U
        Mat mat = new Mat(m.length, m[0].length, type, Scalar.all(0));

        if(mat.createIndexer() instanceof FloatRawIndexer)
        {
            FloatIndexer indexer = mat.createIndexer();

            for (int i =  0; i < mat.size().height(); i++)
            {
                for (int j = 0; j < mat.size().width(); j++)
                {
                    indexer.putDouble(new long[]{(long) i, (long) j}, m[i][j]);
                }
            }
        }
        else if(mat.createIndexer() instanceof UByteRawIndexer)
        {
            UByteRawIndexer indexer = mat.createIndexer();

            for (int i =  0; i < mat.size().height(); i++)
            {
                for (int j = 0; j < mat.size().width(); j++)
                {
                    indexer.putDouble(new long[]{(long) i, (long) j}, m[i][j]);
                }
            }
        }

        return mat;
    }

    /**
     * takes in a 2d Mat and returns an array
     * @param mat
     * @return
     */
    public static double[][] matToArray(Mat mat)
    {
        if(mat.createIndexer() instanceof UByteRawIndexer)
        {
            double[][] m = new double[mat.size().height()][mat.size().width()];
            UByteRawIndexer indexer = mat.createIndexer();
            for (int i =  0; i < m.length; i++)
            {
                for (int j = 0; j < m[0].length; j++)
                {
                    m[i][j] = indexer.get(i, j);
                }
            }
            return m;
        }
        else
        {
            double[][] m = new double[mat.size().height()][mat.size().width()];
            DoubleRawIndexer indexer = mat.createIndexer();
            for (int i =  0; i < m.length; i++)
            {
                for (int j = 0; j < m[0].length; j++)
                {
                    m[i][j] = indexer.get(i, j);
                }
            }
            return m;
        }

    }

    public static Mat stitch(MatVector vlPhotos, Feature2D feature)
    {
        float seamMegapix = (float) 0.1;
        float seamWorkAspect = 1;

        float workScale = 1;
        double seamScale = -1;

        Stitcher stitcher = Stitcher.create();
        stitcher.setFeaturesFinder(feature);

        ImageFeatures features = new ImageFeatures(vlPhotos.size());
        ImageFeatures f = new ImageFeatures();

        for(int i = 0; i < vlPhotos.size(); i++)
        {
            boolean seamScaleSet = seamScale < 0;

            if (!seamScaleSet)
            {
                seamScale = Math.min(1.0, Math.sqrt(seamMegapix * 1e6 / vlPhotos.get(i).size().area()));
                seamWorkAspect = (float) seamScale / workScale;
            }
//            computeImageFeatures2(stitcher.featuresFinder(), vlPhotos.get(i), f);
//            features.position(i).put(new ImageFeatures(f));
        }
//        features.position(0);

        System.out.println("getting features...");
        computeImageFeatures(stitcher.featuresFinder(), vlPhotos, features);
//        for(int i = 0; i < vlPhotos.size(); i++)
//        {
//            System.out.println(i + ": " + features.position(i).getKeypoints().size());
//        }
//        features.position(0);

        System.out.println("getting matches...");
        MatchesInfo matchesInfo = new MatchesInfo(vlPhotos.size()); //
//        BestOf2NearestMatcher matcher = BestOf2NearestMatcher.create();
//        matcher.apply2(features, matchesInfo);
//        matcher.collectGarbage();
        stitcher.featuresMatcher().apply2(features, matchesInfo);
        stitcher.featuresMatcher().collectGarbage();

        // retain images that are definitely part of the pano
//        System.out.println("getting indices...");
//        IntPointer indices = leaveBiggestComponent(features, matchesInfo, (float)stitcher.panoConfidenceThresh());
//        int[] ints = indices.getStringCodePoints();
//        System.out.println("indices:");
//        System.out.println(Arrays.toString(ints));
//
//        MatVector vlSubset = new MatVector();
//
//        for(int i = 0; i < indices.capacity(); i++)
//        {
//            vlSubset.push_back(vlPhotos.get(ints[i]));
//        }
//        vlPhotos = vlSubset;
//
//        System.out.println("size vl: " + vlPhotos.size());
//        if(vlPhotos.size() < 2)
//        {
//            System.out.println("need more images");
//            System.exit(0);
//        }

        // get camera params
        System.out.println("getting camera parameters...");
        CameraParams cameraParams = new CameraParams(vlPhotos.size());
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
        success = stitcher.bundleAdjuster().apply(features, matchesInfo, cameraParams);

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
        for(int i = 0; i < cameraParams.capacity(); i++)
        {
            rMats.push_back(cameraParams.position(i).R().clone());
        }
        waveCorrect(rMats, WAVE_CORRECT_HORIZ);
        for(int i = 0; i < cameraParams.capacity(); i++)
        {
            cameraParams.position(i).R(rMats.get(i));
        }
        cameraParams.position(0);


        // compose panorama
        System.out.println("compose panorama...");
        PointVector corners0 = new PointVector();
        MatVector masksWarped = new MatVector();
        UMatVector imagesWarped = new UMatVector();
        SizeVector sizes0 = new SizeVector();
        UMatVector masks = new UMatVector();

        // Prepare image masks
        for (int i = 0; i < vlPhotos.size(); i++)
        {
            masks.push_back(new Mat(new int[]{vlPhotos.get(i).size().height(), vlPhotos.get(i).size().width()}, CV_8U, Scalar.all(255)).getUMat(ACCESS_READ));
        }
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
            corners0.push_back(warper.warp(vlPhotos.get(i), K, cameraParams.position(i).R(), INTER_LINEAR, BORDER_REFLECT, imgWarped));
            imagesWarped.push_back(imgWarped.getUMat(ACCESS_READ));

            sizes0.push_back(imgWarped.size());

            Mat maskWarped = new Mat();
            warper.warp(masks.get(i).getMat(ACCESS_READ), K, cameraParams.position(i).R(), INTER_NEAREST, BORDER_CONSTANT, maskWarped);
            masksWarped.push_back(maskWarped);
        }
        cameraParams.position(0);

        Mat imgWarped   = new Mat();
        Mat imgWarpedS  = new Mat();
        Mat dilatedMask = new Mat();
        Mat seamMask    = new Mat();
        Mat mask        = new Mat();
        Mat maskWarped  = new Mat();

        float composeWorkAspect = 1;
        float composeScale = 1;
        boolean blenderIsSetup = false;
        boolean composeScaleSet = false;


        Mat fullImg = new Mat();
        Mat img = new Mat();
        Blender blender = Blender.createDefault(Blender.MULTI_BAND);

        PointVector corners = new PointVector();
        SizeVector sizes = new SizeVector();

        for(int imgIdx = 0; imgIdx < vlPhotos.size(); imgIdx++)
        {
            fullImg = vlPhotos.get(imgIdx);
            if(!composeScaleSet)
            {
                composeScaleSet = true;

                composeWorkAspect = composeScale / workScale;
                warper = new CylindricalWarper().create(warpedImageScale * composeWorkAspect);
//                corners.clear();
//                sizes.clear();

//                corners.position(0);
//                sizes.position(0);

                // Update corners and sizes
                System.out.println("update corners and sizes");
                for (int i = 0; i < vlPhotos.size(); ++i)
                {
                    // Update intrinsics
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
                    Size sz = fullImg.size();
                    if (Math.abs(composeScale - 1) > 1e-1)
                    {
                        sz.width(cvRound(sz.width() * composeScale));
                        sz.height(cvRound(sz.height() * composeScale));
                    }

                    Mat K = new Mat();
                    cameraParams.position(i).K().convertTo(K, CV_32F);
                    Rect roi = warper.warpRoi(sz, K, cameraParams.position(i).R());

                    corners.push_back(roi.tl());
                    sizes.push_back(roi.size());
                }
                cameraParams.position(0);
            }
            if(Math.abs(composeScale - 1) > 1e-1)
            {
                resize(fullImg, img, img.size(), composeScale, composeScale, INTER_LINEAR_EXACT);
            }
            else
            {
                img = fullImg;
            }
            Mat K = new Mat();
            cameraParams.position(imgIdx).K().convertTo(K, CV_32F);

            warper.warp(img, K, cameraParams.position(imgIdx).R(), INTER_LINEAR, BORDER_REFLECT, imgWarped);
            // Warp the current image mask
            mask = new Mat(img.size(), CV_8U, Scalar.all(255));

            warper.warp(mask, K, cameraParams.position(imgIdx).R(), INTER_NEAREST, BORDER_CONSTANT, maskWarped);

            imgWarped.convertTo(imgWarpedS, CV_16S);
            imgWarped.release();
            img.release();
            mask.release();

            // Make sure seam mask has proper size
            dilate(masksWarped.get(imgIdx), dilatedMask, new Mat());
            resize(dilatedMask, seamMask, maskWarped.size(), 0, 0, INTER_LINEAR_EXACT);
            bitwise_and(seamMask, maskWarped, maskWarped);

            if (!blenderIsSetup)
            {
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
    }

    public static void main(String[] args)
    {
        Feature2D feature = ORB.create();
        if(feature instanceof ORB) {System.out.println("ORB");}
        else if (feature instanceof KAZE){System.out.println("KAZE");}
        else {System.out.println("other");}

        long start = System.currentTimeMillis();
        System.out.println("start: " + new Date(start));
        MatVector vlPhotos = new MatVector();

        String name = "pano-20190724120207";
        String path = "/Users/ccuser/Desktop/bostonPanos/0/" + name;//20190724144132 orb, 20190724155303
        System.out.println(name);

        //"/Users/ccuser/Desktop/bostonPano/3/pano-20190724155303"
        for(int i = 0; i < 45; i++)
        {
            if(i < 10)
            {
                vlPhotos.push_back(imread(path + "/vl0" + i + ".png"));
            }
            else
            {
                vlPhotos.push_back(imread(path + "/vl" + i + ".png"));
            }
        }
        Mat pano = stitch(vlPhotos, feature);
        imwrite("output/" + name + ".png", pano);

        System.out.println("total time: " + (System.currentTimeMillis() - start) / 1000);
    }

}
