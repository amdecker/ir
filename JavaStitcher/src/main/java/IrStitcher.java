import org.bytedeco.javacpp.IntPointer;
import org.bytedeco.opencv.opencv_core.Mat;
import org.bytedeco.opencv.opencv_core.MatVector;
import org.bytedeco.opencv.opencv_core.UMat;
import org.bytedeco.opencv.opencv_stitching.ImageFeatures;
import org.bytedeco.opencv.opencv_stitching.MatchesInfo;
import org.bytedeco.opencv.opencv_stitching.Stitcher;

import java.util.Arrays;

import static org.bytedeco.opencv.global.opencv_imgcodecs.imread;
import static org.bytedeco.opencv.global.opencv_imgcodecs.imwrite;
import static org.bytedeco.opencv.global.opencv_stitching.computeImageFeatures;
import static org.bytedeco.opencv.global.opencv_stitching.leaveBiggestComponent;


/**
 * Given visible light and corresponding ir or mixed images, it uses the keypoints and other internal characteristics
 * from the visible light images to stitch ir or mixed images together
 *
 */
public class IrStitcher
{
    private MatVector vlImages, irImages, mxImages;
    private Stitcher stitcher;

    public int OK = 0;

    public IrStitcher(MatVector vlImages, MatVector irImages, MatVector mxImages)
    {
        this.vlImages = vlImages;
        this.irImages = irImages;
        this.mxImages = mxImages;
        this.stitcher = Stitcher.create();
    }

    /**
     * this is sort of useful, but it takes a long time to run (maybe ~90 secs) but those 90 seconds are still faster
     * than calculating the internals and trying to compose. That being said, it is probably faster to just use try/catch
     * and not use this because the majority of images will probably stitch
     * @return if the composition will work
     */
    public boolean stitchWillWork()
    {
        // get features
        ImageFeatures features = new ImageFeatures(this.vlImages.size());
        MatVector feature_find_masks = new MatVector(this.vlImages.size());
        computeImageFeatures(stitcher.featuresFinder(), this.vlImages, features, feature_find_masks);

        // get matches
        MatchesInfo matchesInfo = new MatchesInfo(this.vlImages.size());
        stitcher.featuresMatcher().apply2(features, matchesInfo, new UMat());
        stitcher.featuresMatcher().collectGarbage();

        // figure out if all the images should be in pano
        IntPointer indices = leaveBiggestComponent(features, matchesInfo, (float) stitcher.panoConfidenceThresh());
//        int[] ints = indices.getStringCodePoints();
//        System.out.println(indices.capacity());
//        System.out.println("len: " + ints.length);
//        System.out.println(Arrays.toString(ints));

        // composePanorama relies on the fact that you will provide the same number of images as it determined the panorama should contain
        return indices.capacity() == this.vlImages.size();
    }

    /**
     * compose the panoramas
     * @return array of stitched panoramas
     */
    public Mat[] stitch()
    {
        // initalize empty Mats for panoramas
        Mat[] panos = new Mat[3];
        for(int i = 0; i < panos.length; i++)
        {
            panos[i] = new Mat();
        }

        // calculate keypoints, matches, homography and all that stuff from the visible light image
        System.out.println("calculating internals...");
        int response = this.stitcher.estimateTransform(vlImages);

        if(response == OK)
        {
            // if some images are determined to not be a part of the pano by the internal opencv code, this will not work
            try
            {
                System.out.println("Composing vl...");
                this.stitcher.composePanorama(this.vlImages, panos[0]);

                System.out.println("Composing ir...");
                this.stitcher.composePanorama(this.irImages, panos[1]);

                System.out.println("Composing mx...");
                this.stitcher.composePanorama(this.mxImages, panos[2]);
            }

            catch(java.lang.RuntimeException e)
            {
                System.out.println("CANNOT STITCH IMAGES");
                System.out.println(e.getLocalizedMessage());
                return new Mat[0];
            }
        }
        else
        {
            System.out.println("response code: " + response);
            return new Mat[0];
        }
        return panos;
    }

    public static void main(String[] args)
    {
        long start = System.currentTimeMillis();
        System.out.println("start: " + start / 1000);
        MatVector vlImages = new MatVector();
        MatVector irImages = new MatVector();
        MatVector mxImages = new MatVector();

        int num = 12;
        System.out.println("NUM: " + num);
        for (int i = 0; i < 45; i++)
        {
            if (i < 10)
            {
                vlImages.push_back(imread("/Users/ccuser/Desktop/ir_video/pano" + num + "/vl0" + i + ".png"));
                irImages.push_back(imread("/Users/ccuser/Desktop/ir_video/pano" + num + "/ir0" + i + ".png"));
                mxImages.push_back(imread("/Users/ccuser/Desktop/ir_video/pano" + num + "/mx0" + i + ".png"));

            }
            else
            {
                vlImages.push_back(imread("/Users/ccuser/Desktop/ir_video/pano" + num + "/vl" + i + ".png"));
                irImages.push_back(imread("/Users/ccuser/Desktop/ir_video/pano" + num + "/ir" + i + ".png"));
                mxImages.push_back(imread("/Users/ccuser/Desktop/ir_video/pano" + num + "/mx" + i + ".png"));
            }
        }

        IrStitcher stitcher = new IrStitcher(vlImages, irImages, mxImages);
        Mat[] panos = stitcher.stitch();

        System.out.println("Saving...");
        for(int i = 0; i < panos.length; i++)
        {
            imwrite("/Users/ccuser/Desktop/ir_video/panos/javaStitched-" + i + ".png", panos[i]);
        }

        System.out.println("total time: " + (System.currentTimeMillis() - start) / 1000);

    }
}
