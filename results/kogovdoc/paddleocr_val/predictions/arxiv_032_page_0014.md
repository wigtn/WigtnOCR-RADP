AExperimental Details
Many RL environments have termination conditions that depend on the behavior of the agent, such
as ending an episode when the agent dies or falls over. We found that such termination conditions
encode information about the task even when the reward function is not observable. To avoid this
subtle source of supervision, which could potentially confound our attempts to learn from human
preferences only, we removed all variable-length episodes:
: In the Gym versions of our robotics tasks, the episode ends when certain parameters go
outside of a prescribed range (for example when the robot falls over). We replaced these
termination conditions by a penalty which encourages the parameters to remain in the range
(and which the agent must learn).
: In Atari games, we do not send life loss or episode end signals to the agent (we do continue
to actually reset the environment), effectively converting the environment into a single
continuous episode. When providing synthetic oracle feedback we replace episode ends
with a penalty in all games except Pong; the agent must learn this penalty.
Removing variable length episodes leaves the agent with only the information encoded in the
environment itself; human feedback provides its only guidance about what it ought to do.
At the beginning of training we compare a number of trajectory segments drawn from rollouts of an
untrained (randomly initialized) policy. In the Atari domain we also pretrain the reward predictor
for 200 epochs before beginning RL training, to reduce the likelihood of irreversibly learning a bad
policy based on an untrained predictor. For the rest of training, labels are fed in at a rate decaying
inversely with the number of timesteps; after twice as many timesteps have elapsed, we answer about
half as many queries per unit time. The details of this schedule are described in each section. This
“label annealing"' allows us to balance the importance of having a good predictor from the start with
the need to adapt the predictor as the RL agent learns and encounters new states. When training
with real human feedback, we attempt to similarly anneal the label rate, although in practice this is
approximate because contractors give feedback at uneven rates.
Except where otherwise stated we use an ensemble of 3 predictors, and draw a factor 1O more clip
pair candidates than we ultimately present to the human, with the presented clips being selected via
maximum variance between the different predictors as described in Section 2.2.4.
A.1  Simulated Robotics Tasks
The OpenAI Gym continuous control tasks penalize large torques. Because torques are not di-
rectly visible to a human supervisor, these reward functions are not good representatives of human
preferences over trajectories and so we removed them.
For the simulated robotics tasks, we optimize policies using trust region policy optimization (TRPO,
Schulman et al., 2015) with discount rate  = 0.995 and ^ = 0.97. The reward predictor is a two-
layer neural network with 64 hidden units each, using leaky ReLUs (α = 0.01) as nonlinearities.7 We
compare trajectory segments that last 1.5 seconds, which varies from 15 to 60 timesteps depending
on the task.
We normalize the reward predictions to have standard deviation 1. When learning from the reward
predictor, we add an entropy bonus of 0.01 on all tasks except swimmer, where we use an entropy
bonus of 0.001. As noted in Section 2.2.1, this entropy bonus helps to incentivize the increased
exploration needed to deal with a changing reward function.
We collect 25% of our comparisons from a randomly initialized policy network at the beginning of
training, and our rate of labeling after T frames 2 * i06 /(T + 2 * 106).
7 All of these reward functions are second degree polynomials of the input features, and so if we were
concerned only with these tasks we could take a simpler approach to learning the reward function. However,
is not so simple, as described in Section 3.2.
14