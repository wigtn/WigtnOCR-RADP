# 6.1Misuse of Language Models

Malicious uses of language models can be somewhat difcult to anticipate because theyoften involverepurposing language models inavery different environmentorforadiferent purpose thanresearchers intended.To help withthis, wecanthink in terms of traditional securityrisk assessment frameworks,which outline key steps such as identifying threats and potential impacts,ssessing likelihood,anddetermining riskasacombinationof likelihoodandimpact [Rosl2].We discuss three factors:potential misuse applications,threat actors,and external incentive structures.

# 6.1.1Potential Misuse Applications

Any sociallyharmfulactivity thatrelies ongenerating textcouldbeaugmentedby powerfullanguagemodels.Examples include misinformation,spam,phishing,abuseoflegaland governmentalprocesses,fraudulentacademicessywrting and social engineering pretexting.Manyof these applicationsbotteneck on human beings to write sufficiently high quality text.Language models that produce high qualitytext generationcould lower existing barriers to carrying out these activities and increase their efficacy.

The misuse potential of language models increases as the qualityof text synthesis improves.The abilityof GPT-3 to generate several paragraphs of syntheticcontentthat people find difficult to distinguish from human-writen text in 3.9.4 represents a concerning milestone in this regard.

# 6.1.2Threat Actor Analysis

Threatactors canbeorganizedbyskillandresource levels,ranging from lowormoderatelyskiledandresourcedactors who maybeable tobuildamalicious productto‘advanced persistentthreats'(APTs): highlyskiledandwel-resourced (e.g. state-sponsored) groups with long-term agendas $\left[ \mathrm { S B } \bar { \mathrm { C } } ^ { + } 1 9 \right]$ ：

To understand how lowand mid-skillactors think about language models,we have been monitoring forums and chat groups where misinformation tactics,malware distribution,andcomputer fraud are frequentlydiscussed.While we did findsignificant discussionof misuse following the initialreleaseofGPT-2 inspringof2O19,wefound fewer instances of experimentationand no successful deployments since then.Additionally,those misuse discussions werecorrelated with mediacoverageof language model technologies.Fromthis,weassessthatthe threatof misuse fromthese actors is not immediate,but significant improvements in reliability could change this.

Because APTs do nottypicallydisuss operationsin theopen,wehaveconsultedwith professonal threatanalysts about posible APTactivity involving theuseoflanguage models.Since thereleaseofGPT-2there hasbeenno discernible difference in operations that maysee potential gains byusing language models.The assessment was that language models may notbe worth investing significant resources in because there has been no convincing demonstrationthat current anguage models are significantly better than current methods for generating text,and because methods for “targeting”or“controlling”the content of language models are stillat a very early stage.

# 6.1.3External Incentive Structures

Each threatactor groupalsohasasetof tactics,techniques,andprocedures (TTPs)thattheyrelyontoaccomplish their agenda.TTPsare infuencedbyeconomicfactors likescalabilityandeaseofdeployment; phishingis extremely popular among all groupsbecause itoffersalow-cost,low-effort,high-yield methodofdeploying malwareand stealing login credentials.Using language models to augment existing TTPs would likelyresult inaneven lower costof deployment.

Ease of use is another significant incentive.Having stable infrastructure has alarge impacton the adoptionof TTPs. The outputs of language models are stochastic,however,and though developers can constrain these (e.g.using top- $\mathbf { \nabla } \cdot \mathbf { k }$ truncation)theyare notable to performconsistently without human feedback.Ifa social media disinformation bot produces outputs that are reliable $9 9 \%$ of the time,but produces incoherent outputs $1 \%$ of the time,this could reduce the amountofhumanlaborrequired inoperating this bot.Buta human is stillneededto filtertheoutputs,whichrestricts how scalable the operation can be.

Based onour analysis of this modeland analysis of threat actors and the landscape,we suspect AIresearchers wil eventuallydeveloplanguage models thataresufcientlyconsistentandsterable thattheywillbeof greaterinterestto malicious actors.Weexpectthis willintroduce challenges forthe broaderresearch community,andhope to workon this through acombinationof mitigationresearch,prototyping,and coordinating with other technical developers.