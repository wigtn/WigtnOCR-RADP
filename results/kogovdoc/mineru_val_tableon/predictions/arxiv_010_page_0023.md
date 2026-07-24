meaning that ${ \mathbb P } _ { m } ( \{ g _ { n } > 3 \} ) = 0$ and therefore $g _ { n }$ is bounded by 3 almost everywhere for $\mathbb { P } _ { n } , \mathbb { P } _ { m }$ and $\mathbb { P }$ .With the same calculation, $B _ { n } = \{ g _ { n } >$ $\displaystyle 1 + \epsilon \}$ and

$$
\mathbb { P } ( B _ { n } ) = \int _ { B _ { n } } g _ { n } \mathrm { d } \mathbb { P } _ { m } \geq ( 1 + \epsilon ) \mathbb { P } _ { m } ( B _ { n } )
$$

So $\begin{array} { r } { \mathbb { P } _ { m } ( B _ { n } ) \le \frac { 1 } { \epsilon } \delta ( \mathbb { P } , \mathbb { P } _ { m } ) \to 0 } \end{array}$ ，and therefore $\mathbb { P } ( B _ { n } ) \to 0$ .We can now show

$$
\begin{array} { r l r } {  { K L ( \mathbb { P } \| \mathbb { P } _ { m } ) = \int \log ( g _ { n } ) \mathrm { d } \mathbb { P } } } \\ & { } & \\ & { } & { \qquad \le \log ( 1 + \epsilon ) + \int _ { B _ { n } } \log ( g _ { n } ) \mathrm { d } \mathbb { P } } \\ & { } & { \qquad \le \log ( 1 + \epsilon ) + \log ( 3 ) \mathbb { P } ( B _ { n } ) } \end{array}
$$

so we achieve $0 \leq \operatorname* { l i m } \operatorname* { s u p } K L ( \mathbb { P } | | \mathbb { P } _ { m } ) \leq \log ( 1 { + } \epsilon )$ and then $K L ( \mathbb { P } | | \mathbb { P } _ { m } ) $ $0$ .Finally,we conclude

$$
J S ( \mathbb { P } _ { n } , \mathbb { P } ) = { \frac { 1 } { 2 } } K L ( \mathbb { P } _ { n } \| \mathbb { P } _ { m } ) + { \frac { 1 } { 2 } } K L ( \mathbb { P } \| \mathbb { P } _ { m } ) \to 0
$$

· $( J S ( \mathbb { P } _ { n } , \mathbb { P } ) \to 0 \Rightarrow \delta ( \mathbb { P } _ { n } , \mathbb { P } ) \to 0 ,$ ）—by a simple application of the triangular and Pinsker's inequalities we get

$$
\begin{array} { r l r } { \left. { \delta ( \mathbb { P } _ { n } , \mathbb { P } ) \leq \delta ( \mathbb { P } _ { n } , \mathbb { P } _ { m } ) + \delta ( \mathbb { P } , \mathbb { P } _ { m } ) } } \\ & { } & { \leq \sqrt { \frac { 1 } { 2 } K L ( \mathbb { P } _ { n } \| \mathbb { P } _ { m } ) } + \sqrt { \frac { 1 } { 2 } K L ( \mathbb { P } \| \mathbb { P } _ { m } ) } } \\ & { } & { \leq 2 \sqrt { J S ( \mathbb { P } _ { n } , \mathbb { P } ) } \right. 0 } \end{array}
$$

2.This is a long known fact that $W$ metrizes the weak $^ *$ topology of $( C ( \mathcal X ) , \| \cdot$ $\| _ { \infty } )$ on $\operatorname { P r o b } ( \mathcal { X } )$ ，and by definition this is the topology of convergence in distribution.A proof of this can be found (for example) in [22].

3.This is a straightforward application ofPinsker's inequality

$$
\begin{array} { l l l } { \displaystyle \delta ( \mathbb { P } _ { n } , \mathbb { P } ) \leq \sqrt { \frac 1 2 K L ( \mathbb { P } _ { n } \| \mathbb { P } ) } \to 0 } \\ { \displaystyle \delta ( \mathbb { P } , \mathbb { P } _ { n } ) \leq \sqrt { \frac 1 2 K L ( \mathbb { P } \| \mathbb { P } _ { n } ) } \to 0 } \end{array}
$$

4.This is trivial by recalling the fact that $\delta$ and $W$ give the strong and weak\* topologies on the dual of $( C ( \mathcal { X } ) , \| \cdot \| _ { \infty } )$ when restricted to $\operatorname { P r o b } ( \mathcal { X } )$ #