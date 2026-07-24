![](images/abb3d004aa27bcad24286f136a432854d69bbd19330b0b422ddacab6fb0bf96f.jpg)  
Figure14.Onlandscapes,convolutionalsamplingwithunconditionalmodelscanleadtohomogeneousandincoherentglobalstructure (see column 2). $L _ { 2 }$ -guiding with alow resolution image can help to reestablish coherent global structures.

Anintriguing featureof diffusion models is that unconditional modelscanbeconditionedat test-time[15,8285].In particular,[15]presentedanalgorithmtoguidebothunconditionalandconditional models trainedontheImageNetdataset with a classifier $\log p _ { \Phi } ( y | x _ { t } )$ ,trained on each $x _ { t }$ of the diffusion process.We directly build on this formulation and introduce post-hocimage-guiding:

Foran epsilon-parameterized model with fixed variance,the guiding algorithmas introduced in[15]reads:

$$
\hat { \epsilon }  \epsilon _ { \theta } ( z _ { t } , t ) + \sqrt { 1 - \alpha _ { t } ^ { 2 } } \nabla _ { z _ { t } } \log p _ { \Phi } ( y | z _ { t } ) .
$$

This can be interpreted as an update correcting the“score” $\epsilon \theta$ with a conditional distribution $\log p _ { \Phi } ( \boldsymbol { y } | \boldsymbol { z } _ { t } )$ #

Sofar,this scenario hasonly beenapplied to single-classclasification models.Were-interpret the guiding distribution （204号 $p _ { \Phi } ( y | T ( \mathcal { D } ( z _ { 0 } ( z _ { t } ) ) ) )$ as a general purpose image-to-image translation task given a target image $_ y$ ，where $T$ can be any diferentiable transformationadoptedtotheimage-to-imagetranslationtaskathand,suchastheidentity,adownsampling operation or similar.