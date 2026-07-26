A Simple Framework for Contrastive Learning of Visual Representations
2007, DTD, and Oxford 102 Flowers. For other datasets, we held out a subset of the training set for validation while
performing hyperparameter tuning. After selecting the optimal hyperparameters on the validation set, we retrained the
Transfer Learning via a Linear Classifier We trained an l2-regularized multinomial logistic regression classifier on
and we did not apply data augmentation. As preprocessing, all images were resized to 224 pixels along the shorter side
using bicubic resampling, after which we took a 224 × 224 center crop. We selected the l2 regularization parameter from a
range of 45 logarithmically spaced values between 10-6 and 105.
Transfer Learning via Fine-Tuning We fine-tuned the entire network using the weights of the pretrained network as
initialization. We trained for 20,000 steps at a batch size of 256 using SGD with Nesterov momentum with a momentum
parameter of 0.9. We set the momentum parameter for the batch normalization statistics to max(1 - 10/ s, 0.9) where s is
the number of steps per epoch. As data augmentation during fine-tuning, we performed only random crops with resize and
flips; in contrast to pretraining, we did not perform color augmentation or blurring. At test time, we resized images to 256
pixels along the shorter side and took a 224 × 224 center crop. (Additional accuracy improvements may be possible with
further optimization of data augmentation, particularly on the CIFAR-10 and CIFAR-100 datasets.) We selected the learning
rate and weight decay, with a grid of 7 logarithmically spaced learning rates between 0.0001 and 0.1 and 7 logarithmically
spaced values of weight decay between 10-6 and 10-3, as well as no weight decay. We divide these values of weight decay
by the learning rate.
Training from Random Initialization  We trained the network from random initialization using the same procedure
as for fine-tuning, but for longer, and with an altered hyperparameter grid. We chose hyperparameters from a grid of 7
logarithmically spaced learning rates between 0.001 and 1.0 and 8 logarithmically spaced values of weight decay between
10-5 and 10-i.5. Importantly, our random initialization baselines are trained for 40,000 steps, which is sufficiently long to
achieve near-maximal accuracy, as demonstrated in Figure 8 of Kornblith et al. (2019).
On Birdsnap, there are no statistically significant differences among methods, and on Food-1O1, Stanford Cars, and FGVC
Aircraft datasets, fine-tuning provides only a small advantage over training from random initialization. However, on the
remaining 8 datasets, pretraining has clear advantages.
Supervised Baselines We compare against architecturally identical ResNet models trained on ImageNet with standard
cross-entropy loss. These models are trained with the same data augmentation as our self-supervised models (crops, strong
color augmentation, and blur) and are also trained for 1oo0 epochs. We found that, although stronger data augmentation and
longer training time do not benefit accuracy on ImageNet, these models performed significantly better than a supervised
baseline trained for 90 epochs and ordinary data augmentation for linear evaluation on a subset of transfer datasets. The
while the ResNet-50 (4 ×) baseline achieves 78.3%, vs. 76.5% for the self-supervised model.
Statistical Significance Testing We test for the significance of differences between model with a permutation test. Given
predictions of two models, we generate 100,000 samples from the null distribution by randomly exchanging predictions
for each example and computing the difference in accuracy after performing this randomization. We then compute the
percentage of samples from the null distribution that are more extreme than the observed difference in predictions. For top-1
accuracy, this procedure yields the same result as the exact McNemar test. The assumption of exchangeability under the null
hypothesis is also valid for mean per-class accuracy, but not when computing average precision curves. Thus, we perform
significance testing for a difference in accuracy on VOC 2007 rather than a difference in mAP. A caveat of this procedure is
that it does not consider run-to-run variability when training the models, only variability arising from using a finite sample
of images for evaluation.
B.8.2. RESULTS WITH STANDARD RESNET
The ResNet-50 (4 x) results shown in Table 8 of the text show no clear advantage to the supervised or self-supervised models.
With the narrower ResNet-5O architecture, however, supervised learning maintains a clear advantage over self-supervised
learning. The supervised ResNet-50 model outperforms the self-supervised model on all datasets with linear evaluation,
and most (10 of 12) datasets with fine-tuning. The weaker performance of the ResNet model compared to the ResNet (4×)