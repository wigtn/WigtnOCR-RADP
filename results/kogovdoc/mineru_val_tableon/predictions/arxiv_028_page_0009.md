# 5 CONCLUSIONANDFUTUREWORK

Following suggestions that adaptive gradient methods such as Adam might lead to worse generalization than SGD with momentum (Wilson et al.,2O17),we identified and exposed the inequivalence of $\mathrm { L _ { 2 } }$ regularization and weight decay for Adam.We empirically showed that our version of Adam with decoupled weight decay yields substantially beter generalization performance than the common implementation of Adam with $\mathrm { L } _ { 2 }$ regularization.We also proposed to use warm restarts for Adam to improve its anytime performance.

Our results obtained on image classification datasets must be verified on a wider range of tasks, especially ones where the use of regularization is expected to be important.It would be interesting to integrate our findings on weight decay into other methods which attempt to improve Adam, e.g, normalized direction-preserving Adam (Zhang et al.,2O17).While we focused our experimental analysis on Adam,we believe that similar results also hold for other adaptive gradient methods, such as AdaGrad (Duchi etal.,2O11) and AMSGrad (Reddi et al.,2018).

# 6 ACKNOWLEDGMENTS

We thank Patryk Chrabaszcz for help with running experiments with ImageNet32x32；Matthias Feurer and Robin Schirrmeister for providing valuable feedback on this paper in several iterations; and Martin Volker,Robin Schirrmeister,and Tonio Ball for providing us with a comparison of AdamW and Adam on their EEG data.We also thank the following members of the deep learning community for implementing decoupled weight decay in various deep learning libraries:

·Jingwei Zhang,Lei Tai,Robin Schirrmeister,and Kashif Rasul for their implementations inPyTorch(see https://github.com/pytorch/pytorch/pull/4429)   
· Phil Jund for his implementation in TensorFlow described at https://www.tensorflow.org/api_docs/python/tf/contrib/opt/ DecoupledWeightDecayExtension   
·Sylvain Gugger,Anand Saha,Jeremy Howard and other members of fast.ai for their implementationavailable athttps://github.com/sgugger/Adam-experiments   
·Guillaume Lambard for his implementation in Keras available at https://github. com/GLambard/AdamW_Keras   
· Yagami Lin for his implementation in Caffe available at https://github.com/ Yagami123/Caffe-AdamW-AdamWR

This Work was supported by the European Research Council (ERC)under the European Union's Horizon 2O2O research and innovation programme under grant no.716721,by the German Research Foundation (DFG)under the BrainLinksBrainTools Cluster of Excellnce (grant number EXC 1086) and through grant no.INST 37/935-1 FUGG,and by the German state of Baden-Wirtemberg through bwHPC.

# REFERENCES

Laurence Aitchison.A unified theory of adaptive stochastic gradient descent as Bayesian filtering. arXiv:1507.02030,2018.   
Patryk Chrabaszcz,Ilya Loshchilov,and Frank Hutter.A downsampled variant of ImageNet as an alternative to the CIFAR datasets.arXiv:1707.08819,2017.   
Ekin D Cubuk,Barret Zoph,Dandelion Mane,Vijay Vasudevan,and Quoc V Le.Autoaugment: Learning augmentation policies from data.arXiv preprint arXiv:18o5.09501,2018.   
Laurent Dinh,Razvan Pascanu, Samy Bengio,and Yoshua Bengio. Sharp minima can generalize for deep nets.arXiv:1703.04933,2017.   
John Duchi,Elad Hazan,and Yoram Singer.Adaptive subgradient methods for online learning and stochastic optimization. The Journal of Machine Learning Research,12:2121-2159,2011.