## A Why Wasserstein is indeed weak

We now introduce our notation. Let $\mathcal{X} \subseteq \mathbb{R}^d$ be a compact set (such as $[0,1]^d$ the space of images). We define $\text{Prob}(\mathcal{X})$ to be the space of probability measures over $\mathcal{X}$. We note

$$
C_b(\mathcal{X}) = \{ f : \mathcal{X} \to \mathbb{R}, f \text{ is continuous and bounded} \}
$$

Note that if $f \in C_b(\mathcal{X})$, we can define $\|f\|_\infty = \max_{x \in \mathcal{X}} |f(x)|$, since $f$ is bounded. With this norm, the space $(C_b(\mathcal{X}), \|\cdot\|_\infty)$ is a normed vector space. As for any normed vector space, we can define its dual

$$
C_b(\mathcal{X})^* = \{\phi : C_b(\mathcal{X}) \to \mathbb{R}, \phi \text{ is linear and continuous}\}
$$

and give it the dual norm $\|\phi\| = \sup_{f \in C_b(\mathcal{X}), \|f\|_\infty \leq 1} |\phi(f)|$.

With this definitions, $(C_b(\mathcal{X})^*, \|\cdot\|)$ is another normed space. Now let $\mu$ be a signed measure over $\mathcal{X}$, and let us define the total variation distance

$$
\|\mu\|_{TV} = \sup_{A \subseteq \mathcal{X}} |\mu(A)|
$$

where the supremum is taken all Borel sets in $\mathcal{X}$. Since the total variation is a norm, then if we have $\mathbb{P}_r$ and $\mathbb{P}_\theta$ two probability distributions over $\mathcal{X}$,

$$
\delta(\mathbb{P}_r, \mathbb{P}_\theta) := \|\mathbb{P}_r - \mathbb{P}_\theta\|_{TV}
$$

is a distance in $\text{Prob}(\mathcal{X})$ (called the total variation distance).

We can consider

$$
\Phi : (\text{Prob}(\mathcal{X}), \delta) \to (C_b(\mathcal{X})^*, \|\cdot\|)
$$

where $\Phi(\mathbb{P})(f) := \mathbb{E}_{x \sim \mathbb{P}}[f(x)]$ is a linear function over $C_b(\mathcal{X})$. The Riesz Representation theorem ([7], Theorem 10) tells us that $\Phi$ is an isometric immersion. This tells us that we can effectively consider $\text{Prob}(\mathcal{X})$ with the total variation distance as a subset of $C_b(\mathcal{X})^*$ with the norm distance. Thus, just to accentuate it one more time, the total variation over $\text{Prob}(\mathcal{X})$ is exactly the norm distance over $C_b(\mathcal{X})^*$.

Let us stop for a second and analyze what all this technicality meant. The main thing to carry is that we introduced a distance $\delta$ over probability distributions. When looked as a distance over a subset of $C_b(\mathcal{X})^*$, this distance gives the norm topology. The norm topology is very strong. Therefore, we can expect that not many functions $\theta \mapsto \mathbb{P}_\theta$ will be continuous when measuring distances between distributions with $\delta$. As we will show later in Theorem 2, $\delta$ gives the same topology as the Jensen-Shannon divergence, pointing to the fact that the JS is a very strong distance, and is thus more propense to give a discontinuous loss function.

Now, all dual spaces (such as $C_b(\mathcal{X})^*$ and thus $\text{Prob}(\mathcal{X})$) have a strong topology (induced by the norm), and a weak* topology. As the name suggests, the weak* topology is much weaker than the strong topology. In the case of $\text{Prob}(\mathcal{X})$, the strong topology is given by the total variation distance, and the weak* topology is given by the Wasserstein distance (among others) [22].

19