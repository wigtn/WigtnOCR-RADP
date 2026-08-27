# A Why Wasserstein is indeed weak

We now introduce our notation. Let Rd be a compact set (such as [0, 1]d the space of images). We define Prob( ) to be the space of probability measures over X . We note

Note that if f ∈ Cb(X ), we can define ∥f∥ = maxx |f(x)|, since f is bounded. With this norm, the space (Cb(X ), ∥ · ∥ ) is a normed vector space. As for any normed vector space, we can define its dual

and give it the dual norm ∥φ∥ = supf∈Cb(X ),∥f∥∞≤1 |φ(f )|.

With this definitions, (Cb(X )∗, ∥ · ∥) is another normed space. Now let µ be a signed measure over X , and let us define the total variation distance

where the supremum is taken all Borel sets in . Since the total variation is a norm, then if we have Pr and Pθ two probability distributions over ,

is a distance in Prob( ) (called the total variation distance). We can consider

where Φ(P)(f ) := Ex P[f (x)] is a linear function over Cb( ). The Riesz Representation theorem ([7], Theorem 10) tells us that Φ is an isometric immersion. This tells us that we can effectively consider Prob( ) with the total variation distance as a subset of Cb( )∗ with the norm distance. Thus, just to accentuate it one more time, the total variation over Prob( ) is exactly the norm distance over Cb( )∗.

Let us stop for a second and analyze what all this technicality meant. The main thing to carry is that we introduced a distance δ over probability distributions. When looked as a distance over a subset of Cb(X )∗, this distance gives the norm topology. The norm topology is very strong. Therefore, we can expect that not many functions θ Pθ will be continuous when measuring distances between distributions with δ. As we will show later in Theorem 2, δ gives the same topology as the Jensen-Shannon divergence, pointing to the fact that the JS is a very strong distance, and is thus more propense to give a discontinuous loss function.

Now, all dual spaces (such as Cb(X )∗ and thus Prob(X )) have a strong topology (induced by the norm), and a weak\* topology. As the name suggests, the weak\* topology is much weaker than the strong topology. In the case of Prob( ), the strong topology is given by the total variation distance, and the weak\* topology is given by the Wasserstein distance (among others) [22].