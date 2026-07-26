Test Accuracy
System
Conditional Test Accuracy
Baseline
43.1%
25.0%
45.9%
26.1%
+ 61 Specialist models
Table 3: Classification accuracy (top 1) on the JFT development set.
# of test examples
relative accuracy change
# of specialists covering
delta in topl correct
350037
0.0%
141993
+1421
+3.4%
67161
+1572
+7.4%
38801
+8.8%
+1124
26298
+835
+10.5%
16474
+561
+11.1%
10682
+362
+11.3%
7376
+232
+12.8%
+13.6%
+182
4703
4706
+208
+16.6%
10 or more
9082
+14.1%
+324
Table 4: Top 1 accuracy improvement by # of specialist models covering correct class on the JFT
test set.
Eq. 5 does not have a general closed form solution, though when all the models produce a single
probability for each class the solution is either the arithmetic or geometric mean, depending on
whether we use KL(p, q) or KL(q, p)). We parameterize q = softmac(z) (with T = 1) and we
use gradient descent to optimize the logits z w.r.t. eq. 5. Note that this optimization must be carried
out for each image.
5.5 Results
Starting from the trained baseline full network, the specialists train extremely fast (a few days in-
stead of many weeks for JFT). Also, all the specialists are trained completely independently. Table
3 shows the absolute test accuracy for the baseline system and the baseline system combined with
the specialist models. With 61 specialist models, there is a 4.4% relative improvement in test ac-
curacy overall. We also report conditional test accuracy, which is the accuracy by only considering
examples belonging to the specialist classes, and restricting our predictions to that subset of classes.
For our JFT specialist experiments, we trained 61 specialist models, each with 300 classes (plus the
dustbin class). Because the sets of classes for the specialists are not disjoint, we often had multiple
specialists covering a particular image class. Table 4 shows the number of test set examples, the
change in the number of examples correct at position 1 when using the specialist(s), and the rela-
tive percentage improvement in topl accuracy for the JFT dataset broken down by the number of
specialists covering the class. We are encouraged by the general trend that accuracy improvements
are larger when we have more specialists covering a particular class, since training independent
specialist models is very easy to parallelize.
6Soft Targets as Regularizers
One of our main claims about using soft targets instead of hard targets is that a lot of helpful infor-
mation can be carried in soft targets that could not possibly be encoded with a single hard target. In
this section we demonstrate that this is a very large effect by using far less data to fit the 85M pa-
rameters of the baseline speech model described earlier. Table 5 shows that with only 3% of the data
(about 2OM examples), training the baseline model with hard targets leads to severe overfitting (we
did early stopping, as the accuracy drops sharply after reaching 44.5%), whereas the same model
trained with soft targets is able to recover almost all the information in the full training set (about
2% shy). It is even more remarkable to note that we did not have to do early stopping: the system
with soft targets simply converged"' to 57%. This shows that soft targets are a very effective way of
communicating the regularities discovered by a model trained on all of the data to another model.