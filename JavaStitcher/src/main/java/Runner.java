/*
Combines photos into one large photo using javacv, the opencv wrapper from https://github.com/bytedeco

@author Amos Decker

 */

import org.bytedeco.javacv.FFmpegFrameGrabber;
import org.bytedeco.opencv.opencv_core.Mat;
import org.bytedeco.opencv.opencv_core.MatVector;
import org.bytedeco.opencv.opencv_stitching.Stitcher;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.ArrayList;

import static org.bytedeco.opencv.global.opencv_imgcodecs.imread;
import static org.bytedeco.opencv.global.opencv_imgcodecs.imwrite;

public class Runner
{
    public static void videoToFrames(String videoPath, String folder) throws org.bytedeco.javacv.FrameGrabber.Exception, java.io.IOException
    {

        FFmpegFrameGrabber g = new FFmpegFrameGrabber(videoPath);
        g.start();

        BufferedImage frame = new org.bytedeco.javacv.Java2DFrameConverter().getBufferedImage(g.grab());
        int i = 0;
        while(frame != null)
        {
            ImageIO.write(frame, "png", new File(folder + i + ".png"));
            frame = new org.bytedeco.javacv.Java2DFrameConverter().getBufferedImage(g.grab());
            i++;
        }
        g.stop();
    }

    public static void stitcher(String path, String panoName)
    {
        MatVector photos = new MatVector();

        System.out.println("Reading files...");

        for (int i = 0; i < 28; i++)
        {
            photos.resize(photos.size() + 1);

            // the files do not need to be in any particular order or have a certain name, but naming them by a number
            // just made the process of reading them in easier
            photos.put(photos.size() - 1, imread(path + i + ".png"));
        }

            System.out.println("Number of photos to be stitched: " + photos.size());

            Stitcher stitcher = Stitcher.create();
            Mat pano = new Mat(); // creates an empty image that the new panorama will be created in

            System.out.println("Stitching photos...");
            int response = stitcher.stitch(photos, pano);

            System.out.println("Response Code: " + response);

            System.out.println("Saving...");
            imwrite("src/main/java/" + panoName + ".jpg", pano);

            System.out.println("DONE!");
    }

    public static void main(String[] args)
    {
//        try { videoToFrames("video.mp4", "src/main/java/drivewayFrames/"); }
//        catch(Exception e){System.out.println(e.toString());}

//        stitcher();


        
/*
    Response codes:
    (description from https://www.pyimagesearch.com/2018/12/17/image-stitching-with-opencv-and-python/)

    OK = 0 : The image stitching was a success.
    ERR_NEED_MORE_IMGS = 1 : In the event you receive this status code, you will need more input images to construct your panorama. Typically this error occurs if there are not enough keypoints detected in your input images.
    ERR_HOMOGRAPHY_EST_FAIL = 2 : This error occurs when the RANSAC homography estimation fails. Again, you may need more images or your images don’t have enough distinguishing, unique texture/objects for keypoints to be accurately matched.
    ERR_CAMERA_PARAMS_ADJUST_FAIL = 3 : I have never encountered this error before so I don’t have much knowledge about it, but the gist is that it is related to failing to properly estimate camera intrinsics/extrinsics from the input images. If you encounter this error you may need to refer to the OpenCV documentation or even dive into the OpenCV C++ code.
*/

    }

}
