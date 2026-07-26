1 #include <stdio.h>
1 #include <stdio.h>
2int main()
int main()(
int a[i]!
int i;
scanf("%d",&n);
scanf("%d",&n);
scanf("%d"，&a[i]);
for (i= o; i<n; i++)
int count = o;
scanf("%d"，&a[i]);
for (i = o; i< n; i++)(
for (i = o; i< n; i++)(
for (j = o; j< n; j++) (
for（int j=o;j<n;j++)(
if (a[i] == a[j])
if (a[i] == a[j])
10
10
11
count = count + 1;
count = count + 1;
12
11
13
12
if (count == a[i])
14
13
if (count == n)
15
printf("Yes");
printf("Yes");
14
else
16
15
else
17
printf("No");
16
printf("No");
return o;
return o;
18
17
19
18
Figure 13: An example DeepFix problem with the original broken code on the left and the PaLM-Coder 540B
model's prediction on the right. The predicted code contains fixes for all of the compilation errors (undeclared
variables), as well as other stylistic improvements (declaring variables together) and logic improvements
(reading numbers into array a in a loop and not using index i outside the loop).
1 #include <stdio.h>
1 #include<stdio.h>
int main(){
2int main()
int n;
int n, i, min = 400;
int num[400];
scanf("%d",&n);
scanf("%d", &n);
int i, num[400];
for (i = o; i<2 * n; i++)
for (i = o; i< 2 * n; i++)
scanf("%d"，&num[i]);
scanf("%d"，&num[i]);
int min= 400;
for(i=o; i< n; i++)(
for(i=o;i<n;i++)(
for (int j= o; j<(2 * n -1);j++){
for (int j= o; j<(2  n - 1); j++){
10
if (num[i] == num[j])
if(num[i]== num[j])(
11
10
int t = (j - i);
12
11
int t;
t= (j - i);
12
if (t <= min)
13
min = t;
if (t <= min)
13
14
min = t;
14
15
to;
16
15
17
18
16
printf("%d", min);
printf("%d",min);
19
17
return o;
return o;
20
18
21
19
Figure 14: Another example DeepFix problem. The predicted code fixes the compilation error (missing braces
for the if block, causing a scope error for variable t) and makes other improvements (declaring variables
together and removing the line t = O; which has no effect).
DeepFix Code Repair The PaLM-Coder 54oB model demonstrates impressive performance on the
DeepFix code repair task, reaching a compile rate of 82.1%, compared to 71.7% achieved by prior work
(Yasunaga & Liang, 2021). Figures 13 and 14 show example DeepFix problems with PaLM-Coder's successful
predictions. For prompting, we wrote by hand two pairs of broken and fixed C programs containing a variety
of common errors, and did not iterate further on the prompt examples. We pass the broken code through a
code formatter before giving the formatted result to the model, which then predicts the entire fixed code.
For code repair, it is important to assess the amount of code changed by the modelideally we only want
to modify a small portion of the broken code. We provide an analysis in Table 13, where we break down
the results using various metrics for defining “small" edits.13 Interestingly, PaLM produces the smallest
edits, while PaLM-Coder has the highest success rate when only considering edits with small normalized edit
distances, and Davinci Codex has the highest success rate when only considering edits with few lines changed.
In other words, PaLM-Coder tends to change fewer characters spread across more lines compared to Codex.
We observe this behavior qualitatively in the predictions, where PaLM-Coder is more likely than Codex to
13Prior approaches to DeepFix change at most 5 lines of code (Yasunaga & Liang, 2020, 2021). However, this metric does not
exactly carry over to our setting because we first pass the broken code through a code formatter that generally increases the
number of lines. Additionally, there are programs that require more than 5 lines of change to fix. The DeepFix dataset does not
contain any ground truth fixes or input-output examples to assess the quality of fixes beyond compilation.