# Aging SynBio Scout – Current Status
- MLX local inference works
- multi-source retrieval works
- Literature_DB / Hypothesis_DB / Experiment_DB / Idea_DB writing works
- Semantic Scholar can be disabled
- fast validation modes exist

# Remaining Improvement Priorities
1. Retrieval quality
- keep improving aging + synbio query quality
- consider low-priority retention for strong aging papers with weak synbio scores
- continue improving source weighting and filtering

2. Biology Critic quality
- critic is currently too lenient
- suspicious or biologically awkward designs may still get PASS
- make critic stricter about host compatibility, real components, and experimental realism

3. Circuit / experiment output quality
- reduce raw / messy structured output
- improve Notion-friendly formatting
- reduce biologically dubious synthetic designs

4. Ranking quality
- improve ranking so weak but polished-looking ideas do not survive
- connect critic output more strongly to final selection

5. Hallucination control
- add stronger checks for fake genes, fake mechanisms, or unrealistic host/circuit combinations

# Recommended Next Steps
- refine Biology Critic strictness
- improve final idea ranking
- integrate Notion-side review workflow
- continue generating and comparing candidate ideas
