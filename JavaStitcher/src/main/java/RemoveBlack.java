import org.bytedeco.javacpp.indexer.DoubleRawIndexer;
import org.bytedeco.javacpp.indexer.FloatIndexer;
import org.bytedeco.javacpp.indexer.FloatRawIndexer;
import org.bytedeco.javacpp.indexer.UByteRawIndexer;
import org.bytedeco.opencv.opencv_core.*;


import java.io.File;
import java.io.FilenameFilter;
import java.util.ArrayList;
import java.util.Arrays;

import static org.bytedeco.opencv.global.opencv_core.*;
import static org.bytedeco.opencv.global.opencv_imgcodecs.imread;


import static org.bytedeco.opencv.global.opencv_imgcodecs.imwrite;


/**
 * @author amos decker
 * removes the black top and bottom from the stitched panoramas
 */
public class RemoveBlack
{
    /**
     * creates a 2d Mat from an array. Array can't be jagged
     * @param m the array the Mat should be created from
     * @return
     */
    public static Mat arrayToMat(double[][][] m, int type)
    {
        //CV_32F
        //CV_8UC1
        // CV_8U
        Mat mat = new Mat(m.length, m[0].length, CV_8UC3);

        if(mat.createIndexer() instanceof FloatRawIndexer)
        {
            FloatIndexer indexer = mat.createIndexer();

            for (int i =  0; i < mat.size().height(); i++)
            {
                for (int j = 0; j < mat.size().width(); j++)
                {
                    indexer.put(i, j, 0, (byte)m[i][j][0]);
                    indexer.put(i, j, 1, (byte)m[i][j][1]);
                    indexer.put(i, j, 2, (byte)m[i][j][2]);
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
                    indexer.put(i, j, 0, (byte)m[i][j][0]);
                    indexer.put(i, j, 1, (byte)m[i][j][1]);
                    indexer.put(i, j, 2, (byte)m[i][j][2]);
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
    public static double[][][] matToArray(Mat mat)
    {
        if(mat.createIndexer() instanceof UByteRawIndexer)
        {
            double[][][] m = new double[mat.size().height()][mat.size().width()][3];
            UByteRawIndexer indexer = mat.createIndexer();
            for (int i =  0; i < m.length; i++)
            {
                for (int j = 0; j < m[0].length; j++)
                {
                    m[i][j][0] = indexer.get(i, j, 0);
                    m[i][j][1] = indexer.get(i, j, 1);
                    m[i][j][2] = indexer.get(i, j, 2);                }
            }
            return m;
        }
        else
        {
            double[][][] m = new double[mat.size().height()][mat.size().width()][3];
            DoubleRawIndexer indexer = mat.createIndexer();
            for (int i =  0; i < m.length; i++)
            {
                for (int j = 0; j < m[0].length; j++)
                {
                    m[i][j][0] = indexer.get(i, j, 0);
                    m[i][j][1] = indexer.get(i, j, 1);
                    m[i][j][2] = indexer.get(i, j, 2);

                }
            }
            return m;
        }

    }


    /**
     * given the bounds of the section of pano to keep, it returns a new image subsection
     * @param toKeep
     * @param pano
     * @return
     */
    public static Mat removeBlack(int[] toKeep, Mat pano)
    {
        ArrayList<double[][]> noBlack = new ArrayList<double[][]>();
        double[][][] pano_arr = matToArray(pano);

        for(int i = toKeep[0]; i < toKeep[1]; i++)
        {
            noBlack.add(Arrays.copyOfRange(pano_arr[i], toKeep[2], toKeep[3]));
        }

        double[][][] noBlackArr = new double[noBlack.size()][][];
        for(int row = 0; row < noBlackArr.length; row++)
        {
            noBlackArr[row] = noBlack.get(row);
        }
        return arrayToMat(noBlackArr, CV_8U);
    }

    /**
     * gets the indices of the rows in the pano that don't have any black. But only looks at top and bottom edges
     * @param pano
     * @return
     */
    public static int[] rowsNoBlack(Mat pano)
    {
        int top = 0;
        int bottom = pano.size().height();
        int left = 0;
        int right = pano.size().width();
        double[][][] pano_arr = matToArray(pano);
        for(int row = 0; row < pano.size().height(); row++)
        {
            boolean hasBlack = false;
            for(int col = 0; col < pano.size().width(); col++) // ignore the left and right-most columns, bc sometimes they are just all black
            {
                if(pano_arr[row][col][0] == 0 && pano_arr[row][col][1] == 0 && pano_arr[row][col][2] == 0)
                {
                    if(col == 0)
                    {
                        left = col + 1;
                    }
                    else if(col == pano.size().width() - 1)
                    {
                        right = col;
                    }
                    else
                    {
                        hasBlack = true;
                    }
                }
            }
            if(!hasBlack)
            {
                top = row;
                break;
            }
        }

        for(int row = pano.size().height() - 1; row > -1; row--)
        {
            boolean hasBlack = false;
            for(int col = 1; col < pano.size().width() - 1; col++)
            {
                if(pano_arr[row][col][0] == 0 && pano_arr[row][col][1] == 0 && pano_arr[row][col][2] == 0)
                {
                    hasBlack = true;
                }
            }
            if(!hasBlack)
            {
                bottom = row;
                break;
            }
        }
        return new int[]{top, bottom, left, right};

    }

    public static void main(String[] args)
    {
        String dir = "/Users/ccuser/Desktop/bostonPanos/1/output/to upload";
        File file = new File(dir);
        String[] paths = file.list(new FilenameFilter() {
            @Override
            public boolean accept(File current, String name) {
                return name.startsWith("pano-");
            }
        });

        Arrays.sort(paths);
        System.out.println(Arrays.toString(paths));
        for(int i = 0; i < paths.length; i += 3)
        {
            System.out.println(paths[i]);
            Mat ir = imread(dir + "/" + paths[i]);
            Mat mx = imread(dir + "/" + paths[i + 1]);
            Mat vl = imread(dir + "/" + paths[i + 2]);

            int[] rowsToKeep = rowsNoBlack(ir);
            imwrite(dir + "/" + paths[i], removeBlack(rowsToKeep, ir));
            imwrite(dir + "/" + paths[i + 1], removeBlack(rowsToKeep, mx));
            imwrite(dir + "/" + paths[i + 2], removeBlack(rowsToKeep, vl));
        }
    }
}
