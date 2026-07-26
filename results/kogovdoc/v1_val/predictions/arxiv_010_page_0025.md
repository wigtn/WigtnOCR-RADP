$$
= \mathbb{E}_{z \sim p(z)} \left[ \frac{f(g_\theta(z)) - f(g_{\theta_0}(z)) - \langle (\theta - \theta_0), \nabla_\theta f(g_\theta(z)) |_{\theta_0} \rangle}{\|\theta - \theta_0\|} \right]
$$

By differentiability, the term inside the integral converges $p(z)$-a.e. to 0 as $\theta \to \theta_0$. Furthermore,

$$
\left\| \frac{f(g_\theta(z)) - f(g_{\theta_0}(z)) - \langle (\theta - \theta_0), \nabla_\theta f(g_\theta(z)) |_{\theta_0} \rangle}{\|\theta - \theta_0\|} \right\|
$$

$$
\leq \frac{\|\theta - \theta_0\| L(\theta_0, z) + \|\theta - \theta_0\| \|\nabla_\theta f(g_\theta(z)) |_{\theta_0} \|}{\|\theta - \theta_0\|} \leq 2L(\theta_0, z)
$$

and since $\mathbb{E}_{z \sim p(z)} [2L(\theta_0, z)] < +\infty$ by assumption 1, we get by dominated convergence that Equation 6 converges to 0 as $\theta \to \theta_0$ so

$$
\nabla_\theta \mathbb{E}_{z \sim p(z)} [f(g_\theta(z))] = \mathbb{E}_{z \sim p(z)} [\nabla_\theta f(g_\theta(z))]
$$

for almost every $\theta$, and in particular when the right hand side is well defined. Note that the mere existence of the left hand side (meaning the differentiability a.e. of $\mathbb{E}_{z \sim p(z)} [f(g_\theta(z))]$) had to be proven, which we just did. $\square$

25