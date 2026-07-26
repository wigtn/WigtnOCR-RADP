Published as a conference paper at ICLR 2015
Russakovsky, O., Deng, J., Su, H., Krause, J., Satheesh, S., Ma, S., Huang, Z., Karpathy, A., Khosla, A.,
abs/1409.0575,2014.
Sermanet, P., Eigen, D., Zhang, X., Mathieu, M., Fergus, R., and LeCun, Y. OverFeat: Integrated Recognition,
Localization and Detection using Convolutional Networks. In Proc. ICLR, 2014.
Simonyan, K. and Zisserman, A. Two-stream convolutional networks for action recognition in videos. CoRR,
abs/1406.2199, 2014. Published in Proc. NIPS, 2014.
Szegedy, C., Liu, W., Jia, Y., Sermanet, P., Reed, S., Anguelov, D., Erhan, D., Vanhoucke, V., and Rabinovich,
A. Going deeper with convolutions. CoRR, abs/1409.4842, 2014.
Wei, Y., Xia, W., Huang, J., Ni, B., Dong, J., Zhao, Y., and Yan, S. CNN: Single-label to multi-label. CoRR,
abs/1406.5726, 2014.
Zeiler, M. D. and Fergus, R. Visualizing and understanding convolutional networks. CoRR, abs/1311.2901,
2013. Published in Proc. ECCV, 2014.
ALOCALISATION
In the main body of the paper we have considered the classification task of the ILSVRC challenge,
and performed a thorough evaluation of ConvNet architectures of different depth. In this section,
we turn to the localisation task of the challenge, which we have won in 2014 with 25.3% error. It
can be seen as a special case of object detection, where a single object bounding box should be
predicted for each of the top-5 classes, irrespective of the actual number of objects of the class. For
this we adopt the approach of Sermanet et al. (2014), the winners of the ILSVRC-2013 localisation
challenge, with a few modifications. Our method is described in Sect. A.1 and evaluated in Sect. A.2.
A.1 LOCALISATION CONVNET
To perform object localisation, we use a very deep ConvNet, where the last fully connected layer
predicts the bounding box location instead of the class scores. A bounding box is represented by
a 4-D vector storing its center coordinates, width, and height. There is a choice of whether the
bounding box prediction is shared across all classes (single-class regression, SCR (Sermanet et al.,
2014)) or is class-specific (per-class regression, PCR). In the former case, the last layer is 4-D, while
in the latter it is 4000-D (since there are 1000 classes in the dataset). Apart from the last bounding
box prediction layer, we use the ConvNet architecture D (Table 1), which contains 16 weight layers
and was found to be the best-performing in the classification task (Sect. 4).
Training. Training of localisation ConvNets is similar to that of the classification ConvNets
(Sect. 3.1). The main difference is that we replace the logistic regression objective with a Euclidean
loss, which penalises the deviation of the predicted bounding box parameters from the ground-truth.
We trained two localisation models, each on a single scale: S = 256 and S = 384 (due to the time
constraints, we did not use training scale jittering for our ILSVRC-2014 submission). Training was
initialised with the corresponding classification models (trained on the same scales), and the initial
learning rate was set to 10-3. We explored both fine-tuning all layers and fine-tuning only the first
two fully-connected layers, as done in (Sermanet et al., 2014). The last fully-connected layer was
initialised randomly and trained from scratch.
Testing. We consider two testing protocols. The first is used for comparing different network
modifications on the validation set, and considers only the bounding box prediction for the ground
truth class (to factor out the classification errors). The bounding box is obtained by applying the
network only to the central crop of the image.
The second, fully-fledged, testing procedure is based on the dense application of the localisation
ConvNet to the whole image, similarly to the classification task (Sect. 3.2). The difference is that
instead of the class score map, the output of the last fully-connected layer is a set of bounding
box predictions. To come up with the final prediction, we utilise the greedy merging procedure
of Sermanet et al. (2014), which first merges spatially close predictions (by averaging their coor-
dinates), and then rates them based on the class scores, obtained from the classification ConvNet.
When several localisation ConvNets are used, we first take the union of their sets of bounding box
predictions, and then run the merging procedure on the union. We did not use the multiple pooling
10