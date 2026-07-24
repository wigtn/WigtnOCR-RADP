# A Why Wasserstein is indeed weak

We now introduce our notation. Let $\mathcal { X } \subseteq \mathbb { R } ^ { d }$ be a compact set (such as $[ 0 , 1 ] ^ { d }$ the space of images).We define $\operatorname { P r o b } ( \mathcal { X } )$ to be the space of probability measures over $\mathcal { X }$ .Wenote

$$
C _ { b } ( \mathcal { X } ) = \{ f : \mathcal { X } \to \mathbb { R } , f \mathrm { ~ i s ~ c o n t i n u o u s ~ a n d ~ b o u n d e d } \}
$$

Note that if $f \in C _ { b } ( \mathcal { X } )$ ,we can define $\| f \| _ { \infty } = \operatorname* { m a x } _ { x \in \mathcal { X } } | f ( x ) |$ ，since $f$ is bounded. With this norm, the space $( C _ { b } ( \mathcal { X } ) , \| \cdot \| _ { \infty } )$ is a normed vector space.As for any normed vector space,we can define its dual

and give it the dual norm $\begin{array} { r } { \| \phi \| = \operatorname* { s u p } _ { f \in C _ { b } ( \mathcal { X } ) , \| f \| _ { \infty } \leq 1 } | \phi ( f ) | } \end{array}$

With this definitions, $( C _ { b } ( \mathcal { X } ) ^ { * } , \| \cdot \| )$ is another normed space.Now let $\mu$ bea signed measure over $\mathcal { X }$ ,andlet us define the total variation distance

$$
\| \mu \| _ { T V } = \operatorname* { s u p } _ { A \subseteq \mathcal { X } } | \mu ( A ) |
$$

where the supremum is taken all Borel sets in $\mathcal { X }$ ．Since the total variation is a norm,then if we have $\mathbb { P } _ { r }$ and $\mathbb { P } _ { \theta }$ two probability distributions over $\mathcal { X }$

$$
\delta ( \mathbb { P } _ { r } , \mathbb { P } _ { \theta } ) : = \| \mathbb { P } _ { r } - \mathbb { P } _ { \theta } \| _ { T V }
$$

is a distance in $\operatorname { P r o b } ( \mathcal { X } )$ (called the total variation distance). We can consider

$$
\Phi : ( \mathrm { P r o b } ( { \mathcal X } ) , \delta ) \to ( C _ { b } ( { \mathcal X } ) ^ { * } , \| \cdot \| )
$$

where $\Phi ( \mathbb { P } ) ( f ) : = \mathbb { E } _ { x \sim \mathbb { P } } [ f ( x ) ]$ is a linear function over $C _ { b } ( \mathcal { X } )$ .The Riesz Representation theorem ([7],Theorem 1O) tells us that $\Phi$ is an isometric immersion.This tells us that we can effectively consider $\operatorname { P r o b } ( \mathcal { X } )$ with the total variation distance as a subset of $C _ { b } ( \mathcal { X } ) ^ { * }$ with the norm distance.Thus, just to accentuate it one more time,the total variation over $\mathrm { P r o b } ( \mathcal X )$ is exactly the norm distance over $C _ { b } ( \mathcal { X } ) ^ { * }$ ：

Let us stop for a second and analyze what all this technicality meant.The main thing to carry is that we introduced a distance $\delta$ over probability distributions. When looked as a distance over a subset of $C _ { b } ( \mathcal { X } ) ^ { * }$ ,this distance gives the norm topology. The norm topology is very strong.Therefore,we can expect that not many functions $\theta \mapsto \mathbb { P } _ { \theta }$ will be continuous when measuring distances between distributions with $\delta$ .As we will show later in Theorem 2, $\delta$ gives the same topology as the Jensen-Shannon divergence,pointing to the fact that the JS is a very strong distance,and is thus more propense to give a discontinuous loss function.

Now,all dual spaces (such as $C _ { b } ( \mathcal { X } ) ^ { * }$ and thus $\operatorname { P r o b } ( \mathcal { X } )$ )have a strong topology (induced by the norm),and a weak $^ *$ topology. As the name suggests,the weak\* topology is much weaker than the strong topology. In the case of $\operatorname { P r o b } ( \mathcal { X } )$ ，the strong topology is given by the total variation distance,and the weak\* topology is given by the Wasserstein distance (among others） [22].