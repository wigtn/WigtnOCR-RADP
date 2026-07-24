3.One can approximately model all conditionals $p ( \pmb { x } _ { S } \ | \ \pmb { x } _ { \mathcal { S } } )$ where $S$ is a subset of the indices of $_ x$ by training a family of conditional models that share parameters.Essentially,one can use adversarial nets to implement a stochastic extension of the deterministic MP-DBM[11].   
4.Semi-supervised learning: features from the discriminator or inference netcould improve performance of classifiers when limited labeled data is available.   
5.Efficency improvements:training could be accelerated greatly by divising better methods for coordinating $G$ and $D$ or determining beter distributions to sample $\mathbf { z }$ from during training.

This paper has demonstrated the viability of the adversarial modeling framework,suggesting that these research directions could prove useful.

# Acknowledgments

We would like to acknowledge Patrice Marcotte,Olivier Delalleau,Kyunghyun Cho,Guillaume Alain and Jason Yosinski for helpful discussions.Yann Dauphin shared his Parzen window evaluation code with us.We would like to thank the developers of Pylearn2[12]and Theano [7,1], particularly Frédéric Bastien who rushed a Theano feature specifically to benefit this project.Arnaud Bergeron provided much-needed support with $\mathrm { I A T _ { E } X }$ typesetting.We would also like to thank CIFAR,and Canada Research Chairs for funding,and Compute Canada,and Calcul Quebec for providing computational resources.Ian Goodfellow is supported by the 2Ol3 Google Fellowship in Deep Learning.Finally,we Would like to thank Les Trois Brasseurs for stimulating our creativity.

# References

[1] Bastien,F.,Lamblin,P.,Pascanu,R.,Bergstra,J.,Goodfellow,I.J.,Bergeron,A.,Bouchard,N.,and Bengio,Y.(2Ol2).Theano: new features and speed improvements.Deep Learning and Unsupervised Feature Learning NIPS 2012 Workshop.   
[2] Bengio,Y.(2Oo9). Learning deep architectures forAI.Now Publishers.   
[3] Bengio,Y.,Mesnil,G.,Dauphin,Y.,and Rifai,S.(2Ol3a).Better mixing via deep representations.In ICML'13.   
[4] Bengio,Y.,Yao,L.,Alain,G.,and Vincent,P.(2O13b).Generalized denoising auto-encoders as generative models.In NIPS26.NipsFoundation.   
[5] Bengio,Y.,Thibodeau-Laufer,E.,and Yosinski,J.(2Ol4a).Deep generative stochastic networks trainable by backprop.In ICML'14.   
[6] Bengio,Y.,Thibodeau-Laufer,E.,Alain,G.,and Yosinski,J.(2Ol4b).Deep generative stochastic networks trainable by backprop.In Proceedings of the 3Oth International Conference on Machine Learning (ICML'14).   
[7]_Bergstra,J.,Breuleux,O.,Bastien,F.,Lamblin,P.,Pascanu,R.,Desjardins,G.,Turian,J.,Warde-Farley D.,and Bengio,Y.(2O1O).Theano: a CPU and GPU math expression compiler. In Proceedings of the Python for Scientific Computing Conference(SciPy).Oral Presentation.   
[8]_Breuleux,O.,Bengio,Y.,and Vincent,P.(2Ol1).Quickly generating representative samples from an RBM-derived process.Neural Computation,23(8),2053-2073.   
[9] Glorot,X.,Bordes,A.,and Bengio,Y.(2O11).Deep sparse rectifier neural networks.In AISTATS'2011.   
[10] Goodfelow,I.J.,Warde-Farley,D.,Mirza,M.,Courville,A.,and Bengio,Y.(2O13a).Maxout networks. In ICML'2013.   
[11] Goodfellow,I.J.,Mirza,M.,Courville,A.,and Bengio,Y. (2O13b).Multi-prediction deep Boltzmann machines.In NIPS'2013.   
[12] Goodfellow,I.J.,Warde-Farley,D.,Lamblin,P.,Dumoulin,V.,Mirza,M.,Pascanu,R.,Bergstra, J.,Bastien,F.,and Bengio,Y.(O13c).Pylearn2:a machine learning research library.arXiv preprint arXiv:1308.4214.   
[13] Gutmann,M.and Hyvarinen,A.(2Olo).Noise-contrastive estimation:A new estimation principle for unnormalized statistical models.In AISTATS'2010.   
[14] Hinton,G.,Deng,L.,Dahl,G.E.,Mohamed,A.,Jaitly,N.,Senior,A.,Vanhoucke,V.,Nguyen,P., Sainath,T.,and Kingsbury,B.(2Ol2a).Deep neural networks foracoustic modeling in speech recognition. IEEE Signal Processing Magazine,29(6),82-97.   
[15] Hinton,G.E.,Dayan,P.,Frey,B.J.,and Neal,R.M.(1995).The wake-sleep algorithm for unsupervised neural networks. Science,268,1558-1161.