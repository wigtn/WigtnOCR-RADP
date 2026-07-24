Table 3: Classification accuracy (top 1) on the JFT development set.   

     System  Conditional TestAccuracy  Test Accuracy    Baseline  43.1%  25.0%    + 61 Specialist models  45.9%  26.1%     

Table 4: Top 1 accuracy improvement by $\#$ of specialist models covering correct class on the JFT test set.   

     #of specialists covering  #of test examples  deltaintoplcorrect  relative accuracychange    0  350037  0  0.0%    1  141993  +1421  +3.4%    2  67161  +1572  +7.4%    3  38801  +1124  +8.8%    4  26298  +835  +10.5%    5  16474  +561  +11.1%    6  10682  +362  +11.3%    7  7376  +232  +12.8%    8  4703  +182  +13.6%    9  4706  +208  +16.6%    10 or more  9082  +324  +14.1%     

Eq.5 does not have a general closed form solution,though when all the models produce a single probability for each class the solution is either the arithmetic or geometric mean,depending on whether we use $K L ( \mathbf { p } , \mathbf { q } )$ or $K L ( \mathbf { q } , \mathbf { p } )$ ).Weparameterize $\mathbf { q } = s o f t m a x ( \mathbf { z } )$ (with $T = 1$ )andwe use gradient descent to optimize the logits $\mathbf { z }$ W.r.t. eq.5.Note that this optimization must be carried out for each image.

# 5.5 Results

Starting from the trained baseline full network,the specialists train extremely fast (a few days instead of many weeks for JFT).Also,all the specialists are trained completely independently.Table 3 shows the absolute test accuracy for the baseline system and the baseline system combined with the specialist models.With 61 specialist models,there is a $4 . 4 \%$ relative improvement in test accuracy overall.We also report conditional test accuracy,which is the accuracy by only considering examples belonging to the specialist classes,and restricting our predictions to that subset of classes.

For our JFT specialist experiments,we trained 6l specialist models,each with 3OO classes (plus the dustbin class.Because the sets of classes for the specialists are not disjoint,we often had multiple specialists covering a particular image class.Table 4 shows the number of test set examples,the change in the number of examples correct at position 1 when using the specialist(s),and the relative percentage improvement in topl accuracy for the JFT dataset broken down by the number of specialists covering the class.We are encouraged by the general trend that accuracy improvements are larger when we have more specialists covering a particular class,since training independent specialist models is very easy to parallelize.

# 6Soft Targets as Regularizers

One of our main claims about using soft targets instead of hard targets is that a lotof helpful information can be carried in soft targets that could not possibly be encoded with a single hard target.In this section we demonstrate that this is a very large effectbyusing far less data to fit the 85M parameters of the baseline speech model described earlier.Table 5 shows that with only $3 \%$ of the data (about 2OM examples),training the baseline model with hard targets leads to severe overfitting(we did early stopping,as the accuracy drops sharply after reaching $4 4 . 5 \%$ ),whereas the samemodel trained with soft targets is able to recover almost all the information in the full training set (about $2 \%$ shy).It is even more remarkable to note that we did not have to do early stopping:the system with soft targets simply"converged"to $57 \%$ .Thisshows that soft targets are a very effective way of communicating the regularities discovered by a model trained on allof the data to another model.