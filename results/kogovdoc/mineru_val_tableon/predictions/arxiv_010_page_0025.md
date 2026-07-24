$$
= \mathbb { E } _ { z \sim p ( z ) } \left[ { \frac { f ( g _ { \theta } ( z ) ) - f ( g _ { \theta _ { 0 } } ( z ) ) - \langle ( \theta - \theta _ { 0 } ) , \nabla _ { \theta } f ( g _ { \theta } ( z ) ) | _ { \theta _ { 0 } } \rangle } { \| \theta - \theta _ { 0 } \| } } \right]
$$

Bydifferentiability, the term inside the integral converges $p ( z )$ -a.e.to $0$ as $\theta  \theta _ { 0 }$ · Furthermore,

$$
\begin{array} { r l r } { \| \frac { f ( g _ { \theta } ( z ) ) - f ( g _ { \theta _ { 0 } } ( z ) ) - \langle ( \theta - \theta _ { 0 } ) , \nabla _ { \theta } f ( g _ { \theta } ( z ) ) | _ { \theta _ { 0 } } \rangle } { \| \theta - \theta _ { 0 } \| } \| } & { } & \\ { \leq \frac { \| \theta - \theta _ { 0 } \| L ( \theta _ { 0 } , z ) + \| \theta - \theta _ { 0 } \| \| \nabla _ { \theta } f ( g _ { \theta } ( z ) ) | _ { \theta _ { 0 } } \| } { \| \theta - \theta _ { 0 } \| } } & { } & \\ & { } & { \leq 2 L ( \theta _ { 0 } , z ) } \end{array}
$$

and since $\mathbb { E } _ { z \sim p ( z ) } [ 2 L ( \theta _ { 0 } , z ) ] < + \infty$ by assumption 1, we get by dominated convergence that Equation6 converges to $0$ as $\theta  \theta _ { 0 }$ So

$$
\nabla _ { \theta } \mathbb { E } _ { z \sim p ( z ) } [ f ( g _ { \theta } ( z ) ) ] = \mathbb { E } _ { z \sim p ( z ) } [ \nabla _ { \theta } f ( g _ { \theta } ( z ) ) ]
$$

foralmost every $\theta$ ,and in particular when the right hand side is well defined.Note that the mere existance of the left hand side (meaning the differentiability a.e.of $\mathbb { E } _ { z \sim p ( z ) } [ f ( g _ { \theta } ( z ) ) ] )$ had to be proven,which we just did. $\sqcup$ （20