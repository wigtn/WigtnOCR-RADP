## 5 Related Work

There’s been a number of works on the so called Integral Probability Metrics (IPMs) [15]. Given $\mathcal{F}$ a set of functions from $\mathcal{X}$ to $\mathbb{R}$, we can define

$$
d_{\mathcal{F}}(\mathbb{P}_r, \mathbb{P}_\theta) = \sup_{f \in \mathcal{F}} \mathbb{E}_{x \sim \mathbb{P}_r}[f(x)] - \mathbb{E}_{x \sim \mathbb{P}_\theta}[f(x)] \tag{4}
$$

as an integral probability metric associated with the function class $\mathcal{F}$. It is easily verified that if for every $f \in \mathcal{F}$ we have $-f \in \mathcal{F}$ (such as all examples we’ll consider), then $d_{\mathcal{F}}$ is nonnegative, satisfies the triangular inequality, and is symmetric. Thus, $d_{\mathcal{F}}$ is a pseudometric over $\text{Prob}(\mathcal{X})$.

While IPMs might seem to share a similar formula, as we will see different classes of functions can yeald to radically different metrics.

- By the Kantorovich-Rubinstein duality [22], we know that $W(\mathbb{P}_r, \mathbb{P}_\theta) = d_{\mathcal{F}}(\mathbb{P}_r, \mathbb{P}_\theta)$

13