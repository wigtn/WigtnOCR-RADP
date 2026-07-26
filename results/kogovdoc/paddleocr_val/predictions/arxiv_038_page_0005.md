Creative Writing
Game of 24
5x5 Crosswords
4 random sentences
Input
4 numbers (4 9 10 13)
10 clues (hl. presented;..)
Output
SHOWN;
An equation to reach 24
A passage of 4 paragraphs
5x5 letters:
(13-9)*(10-4)=24
WIRRA; AVAIL; .
ending in the 4 sentences
A short writing plan
Thoughts
Words to fill in for clues:
3 intermediate equations
(13-9=4 (left 4,4,10); 10-
(1. Introduce a book that
(hl. shown; v5. naled; ...)
4=6 (left 4,6); 4*6=24)
connects...)
#ToT steps
5-10 (variable)
Table l: Task overview. Input, output, thought examples are in blue.
deliberate search in trees of thoughts (ToT) produces better results, and more importantly, interesting
Unless otherwise stated, we perform experiments using a Chat Completion mode GPT-41 with a
sampling temperature of 0.7.
4.1 Game of 24
Game of 24 is a mathematical reasoning challenge, where the goal is to use 4 numbers and basic
arithmetic operations (+-*/) to obtain 24. For example, given input “4 9 10 13", a solution output
could be “(10 - 4) * (13 - 9) = 24"".
Input: 4 9 10 13
Thought Generation
(a) Propose Prompt
fone example)
4 + 9 = 13 (left: 10 13 13)
LM
Input: 4910 13
10 - 4 = 6 (left: 6 9 13)
10-4=6
4+9=13
Possible next steps:
(..more lines..
(Left: 10 13 13)
(left 6 9 13] 
(b) Value Prompt
Thought Evaluation
13-6=7
13-9=4
(6 239a1)
(left: 4 6)
Evaluate if given numbers can
(13 - 10) * 13 = 3 * 13 = 39
reach 24 (sure/likely/impossible)
LM
10 + 13 + 13 = 36 There is no way
10 14: 10 + 14 = 24. sure
to obtain 24 with these big
4+6=10
4*6=24
(more examples)
numbers.impossible
(left: 10) 
(left 24] 
10 13 13
Figure 2: ToT in a game of 24. The LM is prompted for (a) thought generation and (b) valuation.
Task Setup. We scrape data from 4nums.com, which has 1,362 games that are sorted from easy to
hard by human solving time, and use a subset of relatively hard games indexed 901-1,000 for testing.
For each task, we consider the output as success if it is a valid equation that equals 24 and uses the
input numbers each exactly once. We report the success rate across 1oO games as the metric.
Baselines. We use a standard input-output (IO) prompt with 5 in-context examples. For chain-of-
thought (CoT) prompting, we augment each input-output pair with 3 intermediate equations, each
operating on two remaining numbers. For example, given input “4 9 10 13", the thoughts could be
s  ( )  =9 '( ) 9=-  :   =6- ,
and CoT prompting for 100 times for average performance. We also consider a CoT self-consistency
baseline, which takes the majority output from 100 CoT samples, and an iterative-refine approach on
top of an IO sample for at most 10 iterations. At each iteration, the LM is conditioned on all previous
history to reflect on your mistakes and generate a refined answer"' if the output is incorrect. Note
that it uses groundtruth feedback signals about equation correctness.
ToT Setup. To frame Game of 24 into ToT, it is natural to decompose the thoughts into 3 steps,
each an intermediate equation. As shown in Figure 2(a), at each tree node, we exact the remaining
used for all 3 thought steps, though it only has one example with 4 input numbers. We perform a
breadth-first search (BFS) in ToT, where at each step we keep the best b = 5 candidates. To perform
deliberate BFS in ToT, as shown in Figure 2(b), we prompt LM to evaluate each thought candidate as
“"sure/maybe/impossible" with regard to reaching 24. The aim is to promote correct partial solutions
that can be verdicted within few lookahead trials, and eliminate impossible partial solutions based on
"too big/small"' commonsense, and keep the rest “maybe". We sample values 3 times for each thought.
'Experiments were done between May 5-16, 2023.