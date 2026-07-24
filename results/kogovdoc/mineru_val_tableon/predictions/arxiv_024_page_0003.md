language models can generate chains of thought if demonstrations of chain-of-thought reasoning are provided in the exemplars for few-shot prompting.

Figure l shows an example of a model producing a chain of thought to solve a math word problem that it would have otherwise goten incorrect.The chain of thought in this case resembles a solution andcan interpreted as one,but we stillopt to callit a chain of tought to better capture the idea hat it mimics a step-by-step thought process for arriving at the answer(and also,solutions/explanations typically come after the final answer (Narang et al.,2O2O; Wiegreffe et al.,2O22;Lampinen et al., 2022,inter alia)).

Chain-of-thought prompting has several attractive properties as an approach for facilitating reasoning in language models.

1.First, chain of thought, in principle,allows models to decompose multi-step problems into intermediate steps,which means that additional computation can be allocated to problems that require more reasoning steps.   
2.Second,a chain of thought provides an interpretable window into the behavior of the model, suggesting how it might have arrived at a particular answer and providing opportunities to debug where the reasoning path went wrong (although fully characterizing a model's computations that support an answer remains an open question).   
3.Third,chain-of-thought reasoning can be used for tasks such as math word problems, commonsense reasoning,and symbolic manipulation,and is potentially applicable (at least in principle) to any task that humans can solve via language.   
4.Finally,chain-of-thought reasoning can be readily elicited in sufficiently large off-the-shelf language models simply by including examples of chain of thought sequences into the exemplars of few-shot prompting.

In empirical experiments,we will observe the utility of chain-of-thought prompting for arithmetic reasoning (Section 3),commonsense reasoning (Section 4),and symbolic reasoning (Section 5).

# 3Arithmetic Reasoning

We begin by considering math word problems of the form in Figure 1,which measure the arithmetic reasoning ability of language models.Though simple for humans,arithmetic reasoning is a task where language models often struggle (Hendrycks etal.,2O21;Patel etal.,2O21,inter alia).Strikingly,chainof-thought prompting when used with the 54OB parameter language model performs comparably with task-specific finetuned models on several tasks,even achieving new state of the art on the challnging GSM8Kbenchmark (Cobbe etal.,2021).

# 3.1Experimental Setup

We explore chain-of-thought prompting for various language models on multiple benchmarks.

Benchmarks.We consider the following five math word problem benchmarks:(1) the GSM8K benchmark of math word problems (Cobbe et al.,2O21),(2) the SVAMP dataset of math word problems with varying structures (Patel et al.,2O21),(3) the ASDiv dataset of diverse math word problems (Miao et al.,2O2O),(4) the AQuA dataset of algebraic word problems,and (5)the MAWPS benchmark (Koncel-Kedziorski et al.,2O16).Example problems are given in Appendix Table 12.

Standard prompting.For the baseline,we consider standard few-shot prompting,popularized by Brown et al. (2O2O),in which a language model is given in-context exemplars of input-output pairs before outputing a prediction for a test-time example.Exemplars are formatted as questions and answers.The model gives the answer directly,as shown in Figure 1 (left).

Chain-of-thought prompting. Our proposed approach is to augment each exemplar in few-shot prompting with a chain of thought for an associated answer,as ilustrated in Figure 1(right).As most of the datasets only have an evaluation split,we manuallycomposed a set of eight few-shot exemplars with chains of thought for prompting—Figure 1(right) shows one chain of thought exemplar,and the full setof exemplars is given in Appendix Table 2O.(These particular exemplars did not undergo prompt engineering; robustness is studied in Section 3.4 and Appendix A.2.) To investigate whether chain-of-thought prompting in this form can successfully elicit successful reasoning across a range of