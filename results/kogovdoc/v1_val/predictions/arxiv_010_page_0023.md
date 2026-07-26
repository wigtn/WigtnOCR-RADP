meaning that $\mathbb{P}_m(\{g_n > 3\}) = 0$ and therefore $g_n$ is bounded by 3 almost everywhere for $\mathbb{P}_n, \mathbb{P}_m$ and $\mathbb{P}$. With the same calculation, $B_n = \{g_n > 1 + \epsilon\}$ and

$$
\mathbb{P}(B_n) = \int_{B_n} g_n \, d\mathbb{P}_m \geq (1 + \epsilon) \mathbb{P}_m(B_n)
$$

so $\mathbb{P}_m(B_n) \leq \frac{1}{\epsilon} \delta(\mathbb{P}, \mathbb{P}_m) \to 0$, and therefore $\mathbb{P}(B_n) \to 0$. We can now show

$$
KL(\mathbb{P} \|\mathbb{P}_m) = \int \log(g_n) \, d\mathbb{P}
$$

$$
\leq \log(1 + \epsilon) + \int_{B_n} \log(g_n) \, d\mathbb{P}
$$

$$
\leq \log(1 + \epsilon) + \log(3) \mathbb{P}(B_n)
$$

so we achieve $0 \leq \limsup KL(\mathbb{P} \|\mathbb{P}_m) \leq \log(1 + \epsilon)$ and then $KL(\mathbb{P} \|\mathbb{P}_m) \to 0$. Finally, we conclude

$$
JS(\mathbb{P}_n, \mathbb{P}) = \frac{1}{2} KL(\mathbb{P}_n \|\mathbb{P}_m) + \frac{1}{2} KL(\mathbb{P} \|\mathbb{P}_m) \to 0
$$

- $(JS(\mathbb{P}_n, \mathbb{P}) \to 0 \Rightarrow \delta(\mathbb{P}_n, \mathbb{P}) \to 0)$ — by a simple application of the triangular and Pinsker’s inequalities we get

$$
\delta(\mathbb{P}_n, \mathbb{P}) \leq \delta(\mathbb{P}_n, \mathbb{P}_m) + \delta(\mathbb{P}, \mathbb{P}_m)
$$

$$
\leq \sqrt{\frac{1}{2} KL(\mathbb{P}_n \|\mathbb{P}_m)} + \sqrt{\frac{1}{2} KL(\mathbb{P} \|\mathbb{P}_m)}
$$

$$
\leq 2 \sqrt{JS(\mathbb{P}_n, \mathbb{P})} \to 0
$$

2. This is a long known fact that $W$ metrizes the weak* topology of $(C(\mathcal{X}), \|\cdot\|_\infty)$ on $\text{Prob}(\mathcal{X})$, and by definition this is the topology of convergence in distribution. A proof of this can be found (for example) in [22].

3. This is a straightforward application of Pinsker’s inequality

$$
\delta(\mathbb{P}_n, \mathbb{P}) \leq \sqrt{\frac{1}{2} KL(\mathbb{P}_n \|\mathbb{P})} \to 0
$$

$$
\delta(\mathbb{P}, \mathbb{P}_n) \leq \sqrt{\frac{1}{2} KL(\mathbb{P} \|\mathbb{P}_n)} \to 0
$$

4. This is trivial by recalling the fact that $\delta$ and $W$ give the strong and weak* topologies on the dual of $(C(\mathcal{X}), \|\cdot\|_\infty)$ when restricted to $\text{Prob}(\mathcal{X})$.

□

23