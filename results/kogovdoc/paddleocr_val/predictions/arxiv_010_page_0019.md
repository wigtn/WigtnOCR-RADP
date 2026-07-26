A Why Wasserstein is indeed weak
We now introduce our notation. Let X  Rd be a compact set (such as [0, 1]d the
X. We note
Cb(x) = {f : X → R, f is continuous and bounded)
Note that if f E Cb(x), we can define llflloo = maxxex lf(α)l, since f is bounded.
With this norm, the space (Cb(x), ll · llo) is a normed vector space. As for any
normed vector space, we can define its dual
Cb(α)* = {Φ : Cb(x) → R, Φ is linear and continuous)
With this definitions, (Cb(x)*, Il : I) is another normed space. Now let μ be a
signed measure over X, and let us define the total variation distance
IlμTV = sup Iμ(A)I
ACX
where the supremum is taken all Borel sets in X. Since the total variation is a
norm, then if we have Pr and Pe two probability distributions over X,
8(Pr, Pe) := IPr - PellTV
is a distance in Prob(x) (called the total variation distance).
We can consider
 : (Prob(X),) → (Cb(α)*, l · Il)
where (P)(f) := E~p[f(α)) is a linear function over C(α). The Riesz Represen-
tation theorem ([7], Theorem 10) tells us that  is an isometric immersion. This
tells us that we can effectively consider Prob(x) with the total variation distance
as a subset of Cb(X)* with the norm distance. Thus, just to accentuate it one more
thing to carry is that we introduced a distance  over probability distributions.
When looked as a distance over a subset of Cb(x)*, this distance gives the norm
topology. The norm topology is very strong. Therefore, we can expect that not
many functions  → P will be continuous when measuring distances between dis-
tributions with 8. As we will show later in Theorem 2,  gives the same topology
as the Jensen-Shannon divergence, pointing to the fact that the JS is a very strong
distance, and is thus more propense to give a discontinuous loss function.
Now, all dual spaces (such as Cb(X)* and thus Prob()) have a strong topology
(induced by the norm), and a weak* topology. As the name suggests, the weak*
topology is much weaker than the strong topology. In the case of Prob(x), the
strong topology is given by the total variation distance, and the weak* topology is
given by the Wasserstein distance (among others) [22].
19