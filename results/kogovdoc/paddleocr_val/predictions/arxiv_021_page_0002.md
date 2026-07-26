multiple filter sizes
multiple references
feature map
feature map
feature map
multiple scaled images
age
(a)
(b)
(c)
Figure 1: Different schemes for addressing multiple scales and sizes. (a) Pyramids of images and feature maps
are built, and the classifier is run at all scales. (b) Pyramids of filters with multiple scales/sizes are run on
the feature map. (c) We use pyramids of reference boxes in the regression functions.
pyramids of images (Figure 1, a) or pyramids of filters
mercial systems such as at Pinterests [17], with user
engagement improvements reported.
that serve as references at multiple scales and aspect
In ILSVRC and COCO 2015 competitions, Faster
ratios. Our scheme can be thought of as a pyramid
R-CNN and RPN are the basis of several 1st-place
of regression references (Figure 1, c), which avoids
entries [18] in the tracks of ImageNet detection, Ima-
geNet localization, COCO detection, and COCO seg-
enumerating images or filters of multiple scales or
aspect ratios. This model performs well when trained
mentation. RPNs completely learn to propose regions
and tested using single-scale images and thus benefits
from data, and thus can easily benefit from deeper
running speed.
and more expressive features (such as the 101-layer
To unify RPNs with Fast R-CNN [2] object detec-
residual nets adopted in [18]). Faster R-CNN and RPN
tion networks, we propose a training scheme that
are also used by several other leading entries in these
competitions2. These results suggest that our method
alternates between fine-tuning for the region proposal
task and then fine-tuning for object detection, while
is not only a cost-efficient solution for practical usage,
keeping the proposals fixed. This scheme converges
but also an effective way of improving object detec-
tion accuracy.
quickly and produces a unified network with convo-
lutional features that are shared between both tasks.1
We comprehensively evaluate our method on the
RELATED WORK
PASCAL VOC detection benchmarks [11] where RPNs
with Fast R-CNNs produce detection accuracy bet-
Object Proposals. There is a large literature on object
ter than the strong baseline of Selective Search with
proposal methods. Comprehensive surveys and com-
Fast R-CNNs. Meanwhile, our method waives nearly
parisons of object proposal methods can be found in
all computational burdens of Selective Search at
[19], [20], [21]. Widely used object proposal methods
test-timethe effective running time for proposals
include those based on grouping super-pixels (e.g,
is just 10 milliseconds. Using the expensive very
Selective Search [4], CPMC [22], MCG [23]) and those
deep models of [3], our detection method still has
based on sliding windows (e.g., objectness in windows
a frame rate of 5fps (including all steps) on a GPU,
[24], EdgeBoxes [6]). Object proposal methods were
and thus is a practical object detection system in
adopted as external modules independent of the de-
terms of both speed and accuracy. We also report
tectors (e.g., Selective Search [4] object detectors, R-
results on the MS COCO dataset [12] and investi-
CNN [5], and Fast R-CNN [2]).
gate the improvements on PASCAL VOC using the
Deep Networks for Object Detection. The R-CNN
COCO data. Code has been made publicly available
method [5] trains CNNs end-to-end to classify the
at https://github.com/shaoqingren/faster.
proposal regions into object categories or background.
rcnn (in MATLAB) and https://github.com/
R-CNN mainly plays as a classifier, and it does not
rbgirshick/py-faster-rcnn (in Python).
predict object bounds (except for refining by bounding
A preliminary version of this manuscript was pub-
box regression). Its accuracy depends on the perfor-
lished previously [10]. Since then, the frameworks of
mance of the region proposal module (see compar-
RPN and Faster R-CNN have been adopted and gen-
isons in [20l). Several papers have proposed ways of
eralized to other methods, such as 3D object detection
using deep networks for predicting object bounding
[13], part-based detection [14], instance segmentation
boxes [25], [9], [26], [27]. In the OverFeat method [9],
[15], and image captioning [16]. Our fast and effective
a fully-connected layer is trained to predict the box
object detection system has also been built in com-
coordinates for the localization task that assumes a
single object. The fully-connected layer is then turned
1. Since the publication of the conference version of this paper
[10], we have also found that RPNs can be trained jointly with Fast
R-CNN networks leading to less training time.
2. http:/ /image-net.org/challenges/LSVRC/2015/results