1 #include   1 #include     
2 int main(){ 2 int main(){   
3 int a[i]; 3 int a[100],i,n,count=0;   
4 inti;   
5 scanf("%d"，&n); 4 scanf("%d"，&n);   
6 scanf("%d"，&a[i])； 5 for $a = 0$ i  1 #include    
2 int main(){ 2 int main(）{   
3 int n; 3 int n,i,min= 400;   
4 int num[400];   
4 scanf("%d"，&n); 5 scanf("%d"，&n);   
5 int i，num[400];   
6 for $\mathbf { \partial } ( \mathbf { \dot { \ { 1 } } } \ \mathbf { \ { 1 } } ) = \mathbf { \ \Theta } \Theta$ i<2\*n;i++) 6 for (i=0;i<2\*n;i++)   
7 scanf("%d",&num[i]); 7 scanf("%d",&num[i]);   
8 int min $\mathbf { \Sigma } = \mathbf { \Sigma }$ 400;   
9 for ( $\dot { \textbf { 1 } } = \Theta _ { \mathrm { ~ } }$ i<n;i++）{ 8 for $\mathbf { \partial } \cdot \mathbf { i } \ = \ \Theta _ { }$ i<n;i++）{   
10 for(int $\begin{array} { r l r } { \mathrm { ~  ~ j ~ } = } & { { } \Theta _ { i } } \end{array}$ ：j<(2\*n-1)；j++){ 9 for(int $\begin{array} { r l r } { \mathrm { ~  ~ j ~ } = } & { { } \Theta ; } \end{array}$ j<(2\*n-1);j++){   
11 if (num[i] $\scriptstyle = =$ num[j]) 10 if (num[i] $\scriptstyle = =$ num[j]）{   
12 intt; 11 int $\mathrm { ~ t ~ } = \mathrm { ~ ( ~ j ~ - ~ } \mathrm { ~ i ~ ) ~ }$   
13 $\textrm { t } = \textrm { ( j ~ - ~ i ) }$ ： 12 if (t <= min)   
14 if $\ t < = \mathsf { m i n }$ 0 13 min =t;   
15 min=t; 14 高   
16 t=0；   
17 } 15 ）   
18 } 16 】   
19 printf("%d",min); 17 printf("%d",min);   
20 return 0; 18 return 0;   
21} 19}

DeepFix Code Repair The PaLM-Coder 540B model demonstrates impressive performance on the DeepFix code repair task,reaching a compile rate of $8 2 . 1 \%$ ,compared to $7 1 . 7 \%$ achieved by prior work (Yasunaga & Liang,2021).Figures 13 and 14 show example DeepFix problems with PaLM-Coder's successful predictions.For prompting,we wrote by hand two pairs of brokenand fixed C programs containing a variety of common erors,and did not iterate further on the prompt examples.We pass the broken code through a code formater before giving the formatted result to the model,which then predicts the entire fixed code.

For code repair,it is important to assss the amount of code changed by the model—ideally we only want to modify asmall portion of the broken code.We provide an analysis in Table l3,where we break down the results using various metrics for defining “small” edits.13 Interestingly,PaLM produces the smallest edits,while PaLM-Coder has the highest success rate whenonly considering edits with small normalized edit distances,and Davinci Codex has the highest success rate when onlyconsidering edits with few lines changed. In other words,PaLM-Coder tends to change fewer characters spread acros more lines compared to Codex. Weobserve this behavior qualitatively in the predictions,where PaLM-Coder is more likely than Codex to