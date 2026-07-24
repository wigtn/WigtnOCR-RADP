Proofof Theorem 3.Letusdefine

$$
\begin{array} { r l } & { V ( \tilde { f } , \theta ) = \mathbb { E } _ { x \sim \mathbb { P } _ { r } } [ \tilde { f } ( x ) ] - \mathbb { E } _ { x \sim \mathbb { P } _ { \theta } } [ \tilde { f } ( x ) ] } \\ & { \qquad = \mathbb { E } _ { x \sim \mathbb { P } _ { r } } [ \tilde { f } ( x ) ] - \mathbb { E } _ { z \sim p ( z ) } [ \tilde { f } ( g _ { \theta } ( z ) ) ] } \end{array}
$$

where $\hat { f }$ lies in $\mathcal { F } = \{ \bar { f } : \mathcal { X }  \mathbb { R }$ ， $\hat { f } \in C _ { b } ( \mathcal { X } )$ ， $\| { \tilde { f } } \| _ { L } \leq 1 \}$ and $\boldsymbol { \theta } \in \mathbb { R } ^ { d }$ #

Since $\mathcal { X }$ is compact,we know by the Kantorovich-Rubenstein duality [22] that there is an $f \in { \mathcal { F } }$ that attains the value

$$
W ( \mathbb { P } _ { r } , \mathbb { P } _ { \theta } ) = \operatorname* { s u p } _ { \tilde { f } \in \mathcal { F } } V ( \tilde { f } , \theta ) = V ( f , \theta )
$$

Let us define $X ^ { \ast } ( \theta ) = \{ f \in \mathcal { F } : V ( f , \theta ) = W ( \mathbb { P } _ { r } , \mathbb { P } _ { \theta } ) \}$ .By the above point we know then that $X ^ { * } ( \theta )$ is non-empty.We know that by a simple envelope theorem ([12], Theorem 1) that

$$
\nabla _ { \boldsymbol { \theta } } W ( \mathbb { P } _ { r } , \mathbb { P } _ { \boldsymbol { \theta } } ) = \nabla _ { \boldsymbol { \theta } } V ( \boldsymbol { f } , \boldsymbol { \theta } )
$$

for any $f \in X ^ { * } ( \theta )$ when both terms are well-defined.

Let $f \in X ^ { * } ( \theta )$ ,which we knows exists since $X ^ { \ast } ( \theta )$ is non-empty for all $\theta$ .Then, weget

$$
\begin{array} { r l } & { \nabla _ { \theta } W ( \mathbb { P } _ { r } , \mathbb { P } _ { \theta } ) = \nabla _ { \theta } V ( f , \theta ) } \\ & { \qquad = \nabla _ { \theta } \bigl [ \mathbb { E } _ { x \sim \mathbb { P } _ { r } } [ f ( x ) ] - \mathbb { E } _ { z \sim p ( z ) } [ f ( g _ { \theta } ( z ) ) ] } \\ & { \qquad = - \nabla _ { \theta } \mathbb { E } _ { z \sim p ( z ) } [ f ( g _ { \theta } ( z ) ) ] } \end{array}
$$

under the condition that the first and last terms are well-defined.The rest of the proof will be dedicated to show that

$$
- \nabla _ { \boldsymbol { \theta } } \mathbb { E } _ { z \sim p ( z ) } [ f ( g _ { \boldsymbol { \theta } } ( z ) ) ] = - \mathbb { E } _ { z \sim p ( z ) } [ \nabla _ { \boldsymbol { \theta } } f ( g _ { \boldsymbol { \theta } } ( z ) ) ]
$$

when the right hand side is defined.For the reader who is not interested in such technicalities,he or she can skip the rest of the proof.

Since $f \in \mathcal F$ ，we know that it is 1-Lipschitz. Furthermore, $g _ { \boldsymbol { \theta } } ( z )$ is locally Lipschitz as a function of $( \theta , z )$ .Therefore, $f ( g _ { \boldsymbol { \theta } } ( z ) )$ is locally Lipschitz on $( \theta , z )$ with constants $L ( \theta , z )$ (the same ones as $g$ ).By Radamacher's Theorem, $f ( g _ { \boldsymbol { \theta } } ( z ) )$ （204号 has to be differentiable almost everywhere for $( \theta , z )$ jointly.Rewriting this,the set $A = \{ ( \theta , z ) : f \circ g$ is not differentiable} has measure $0$ .By Fubini's Theorem,this implies that for almost every $\theta$ the section $A _ { \theta } = \{ z : ( \theta , z ) \in A \}$ has measure $0$ Let's now fix a $\theta _ { 0 }$ such that the measure of $A _ { \theta _ { 0 } }$ is null (such as when the right hand side of equation (5) is well defined). For this $\theta _ { 0 }$ we have $\nabla _ { \theta } f ( g _ { \theta } ( z ) ) | _ { \theta _ { 0 } }$ （204号 is well-defined for almost any $z$ ,and since $p ( z )$ has a density,it is defined $p ( z )$ -a.e. By assumption $^ { 1 }$ we know that

$$
\begin{array} { r } { \mathbb { E } _ { z \sim p ( z ) } [ \| \nabla _ { \theta } f ( g _ { \theta } ( z ) ) | _ { \theta _ { 0 } } \| ] \le \mathbb { E } _ { z \sim p ( z ) } [ L ( \theta _ { 0 } , z ) ] < + \infty } \end{array}
$$

S0 $\mathbb { E } _ { z \sim p ( z ) } [ \nabla _ { \theta } f ( g _ { \theta } ( z ) ) | _ { \theta _ { 0 } } ]$ is well-defined for almost every $\theta _ { 0 }$ . Now, we can see

$$
\frac { \mathbb { E } _ { z \sim p ( z ) } [ f ( g _ { \theta } ( z ) ) ] - \mathbb { E } _ { z \sim p ( z ) } [ f ( g _ { \theta _ { 0 } } ( z ) ) ] - \langle ( \theta - \theta _ { 0 } ) , \mathbb { E } _ { z \sim p ( z ) } [ \nabla _ { \theta } f ( g _ { \theta } ( z ) ) | _ { \theta _ { 0 } } ] \rangle } { \| \theta - \theta _ { 0 } \| }
$$