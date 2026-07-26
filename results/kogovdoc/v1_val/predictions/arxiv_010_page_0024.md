Proof of Theorem 3. Let us define

$$
V(\tilde{f}, \theta) = \mathbb{E}_{x \sim \mathbb{P}_r}[\tilde{f}(x)] - \mathbb{E}_{x \sim \mathbb{P}_\theta}[\tilde{f}(x)]
$$
$$
= \mathbb{E}_{x \sim \mathbb{P}_r}[\tilde{f}(x)] - \mathbb{E}_{z \sim p(z)}[\tilde{f}(g_\theta(z))]
$$

where $\tilde{f}$ lies in $\mathcal{F} = \{\tilde{f} : \mathcal{X} \to \mathbb{R} \mid \tilde{f} \in C_b(\mathcal{X}), \|\tilde{f}\|_L \leq 1\}$ and $\theta \in \mathbb{R}^d$.

Since $\mathcal{X}$ is compact, we know by the Kantorovich-Rubenstein duality [22] that there is an $f \in \mathcal{F}$ that attains the value

$$
W(\mathbb{P}_r, \mathbb{P}_\theta) = \sup_{\tilde{f} \in \mathcal{F}} V(\tilde{f}, \theta) = V(f, \theta)
$$

Let us define $X^*(\theta) = \{f \in \mathcal{F} : V(f, \theta) = W(\mathbb{P}_r, \mathbb{P}_\theta)\}$. By the above point we know then that $X^*(\theta)$ is non-empty. We know that by a simple envelope theorem ([12], Theorem 1) that

$$
\nabla_\theta W(\mathbb{P}_r, \mathbb{P}_\theta) = \nabla_\theta V(f, \theta)
$$

for any $f \in X^*(\theta)$ when both terms are well-defined.

Let $f \in X^*(\theta)$, which we knows exists since $X^*(\theta)$ is non-empty for all $\theta$. Then, we get

$$
\nabla_\theta W(\mathbb{P}_r, \mathbb{P}_\theta) = \nabla_\theta V(f, \theta)
$$
$$
= \nabla_\theta [\mathbb{E}_{x \sim \mathbb{P}_r}[f(x)] - \mathbb{E}_{z \sim p(z)}[f(g_\theta(z))]
$$
$$
= -\nabla_\theta \mathbb{E}_{z \sim p(z)}[f(g_\theta(z))]
$$

under the condition that the first and last terms are well-defined. The rest of the proof will be dedicated to show that

$$
-\nabla_\theta \mathbb{E}_{z \sim p(z)}[f(g_\theta(z))] = -\mathbb{E}_{z \sim p(z)}[\nabla_\theta f(g_\theta(z))] \tag{5}
$$

when the right hand side is defined. For the reader who is not interested in such technicalities, he or she can skip the rest of the proof.

Since $f \in \mathcal{F}$, we know that it is 1-Lipschitz. Furthermore, $g_\theta(z)$ is locally Lipschitz as a function of $(\theta, z)$. Therefore, $f(g_\theta(z))$ is locally Lipschitz on $(\theta, z)$ with constants $L(\theta, z)$ (the same ones as $g$). By Radamacher’s Theorem, $f(g_\theta(z))$ has to be differentiable almost everywhere for $(\theta, z)$ jointly. Rewriting this, the set $A = \{(\theta, z) : f \circ g \text{ is not differentiable}\}$ has measure 0. By Fubini’s Theorem, this implies that for almost every $\theta$ the section $A_\theta = \{z : (\theta, z) \in A\}$ has measure 0. Let’s now fix a $\theta_0$ such that the measure of $A_{\theta_0}$ is null (such as when the right hand side of equation (5) is well defined). For this $\theta_0$ we have $\nabla_\theta f(g_\theta(z))|_{\theta_0}$ is well-defined for almost any $z$, and since $p(z)$ has a density, it is defined $p(z)$-a.e. By assumption 1 we know that

$$
\mathbb{E}_{z \sim p(z)}[||\nabla_\theta f(g_\theta(z))||_{\theta_0}] \leq \mathbb{E}_{z \sim p(z)}[L(\theta_0, z)] < +\infty
$$

so $\mathbb{E}_{z \sim p(z)}[\nabla_\theta f(g_\theta(z))|_{\theta_0}]$ is well-defined for almost every $\theta_0$. Now, we can see

$$
\frac{\mathbb{E}_{z \sim p(z)}[f(g_\theta(z))] - \mathbb{E}_{z \sim p(z)}[f(g_{\theta_0}(z))] - \langle (\theta - \theta_0), \mathbb{E}_{z \sim p(z)}[\nabla_\theta f(g_\theta(z))|_{\theta_0}] \rangle}{||\theta - \theta_0||} \tag{6}
$$

24