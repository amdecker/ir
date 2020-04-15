# ir
<div>
  <h1>Image Stitching</h1>
  <div>Run main() in runner.py to have a pop-up file chooser. Select the folder that contains the images you want to stitch and it will: </div>
  <ul>
    <li>rescale the images so that the same colors mean the same temperatures in all the images</li>
    <li>stitch the images -- ir images and vl images are needed, but mixed images are optional (they can be created later on)</li>
    <li>(optional) change the color palette of the panorama</li>
    <li>(optional) create mixed visible light/infrared image that does not rely on the mixed images that flir creates</li>
    <li>save the panoramas -- it opens a pop-up file chooser where you can select the folder where you want the images to be saved</li>
  </ul>
  <div><i>NOTE: for Java stiching there are two options: #1 is to run main() in IrStitcher.java. This is pretty good, but if there are more than 20-30 images it won't work. Option #2 is main() in IrStitcher2.java this only seems to work using the ORB feature detector on macOS.</i></div>
  <br>
  <br>
  <div>If you are new to python make sure this entire project is downloaded onto your computer and then open up terminal and navigate to the directory containing runner.py and type (no quotes) "python3 runner.py". If you do not have python3 try just "python runner.py". On windows open command prompt and you might have to just type "py" instead of python.
  <br>
  <br>
  <h1>Other Files</h1>
  <ul>
    <li>palettes/ contains files for describing how to color an ir image. Each line is a color in YCbCr color space. First line describes the coldest color, last line the warmest</li>
    <li>everything in typescript-ir/ is a demo of changing the palette of an image and displaying temperature data where a user clicks. It 
  is the first thing I actually wrote using typescript and can be seen <a href="https://amdecker.github.io/ir/typescript-ir/">here</a></li>
    <li>Image.py provides a class for doing cool things with images like identifying & changing the palette of ir images, removing the black border that appears after stitching images together, edge detection, creating mixed infrared and visible light images, and more!</li>
        <ul>
            <li>There are three types of mixed images you can create. <a href="https://github.com/amdecker/ir/blob/master/example_images/mx1.png">mx1</a>, <a href="https://github.com/amdecker/ir/blob/master/example_images/mx2.png">mx2</a>, and <a href="https://github.com/amdecker/ir/blob/master/example_images/mx3.png">mx3</a></li>
        </ul>
    <li>rescale.py is used to change the colors of an ir image so that in a group of ir images the same colors mean the same temperatures in all the images</li>
    <li>util.py is useful.</li>
    <li>StitcherEasy.py is what runner.py uses to stitch images together into a panorama</li>
    <li>Stitcher.py is old and shouldn't be used</li>
   </ul>
  <br>
  <br>
  <a href="https://concord.org/">https://concord.org/</a>
  <br>
  <a href="http://energy.concord.org/isv/">Infrared Street View</a>
  <br>
  <a href="https://irstreetview-xi.now.sh/maps">IR Street View 2</a>
</div>
