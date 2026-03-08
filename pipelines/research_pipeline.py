from integrations.paper_sources import fetch_recent_papers
from integrations.notion_client import NotionIntegration
from agents.literature_agent import LiteratureAgent
from agents.hypothesis_agent import HypothesisAgent
from agents.circuit_agent import CircuitAgent
from agents.judge_agent import JudgeAgent
from config import settings

class ResearchPipeline:
    def __init__(self, args=None):
        self.args = args
        self.notion = NotionIntegration()
        self.lit_agent = LiteratureAgent()
        self.hyp_agent = HypothesisAgent()
        self.circ_agent = CircuitAgent()
        self.judge_agent = JudgeAgent()

    def run(self):
        mode = self.args.mode if self.args else "full"
        limit = self.args.limit if self.args else settings.PAPERS_TO_FETCH
        skip_notion = self.args.skip_notion if self.args else False
        
        # Default limits for test modes
        if mode in ["smoke", "test-circuit", "test-idea"] and self.args.limit is None:
            limit = 1

        print(f"\n--- Starting {mode.upper()} Mode (Limit: {limit}) ---")

        try:
            # Special case for test-circuit if we want to bypass retrieval
            if mode == "test-circuit":
                return self._run_test_circuit(skip_notion)

            print(f"Fetching papers for query: {settings.SEARCH_QUERY}")
            papers = fetch_recent_papers(settings.SEARCH_QUERY, limit)
            
            processed_count = 0
            for paper in papers:
                if processed_count >= limit:
                    break
                
                print(f"\n[Paper {processed_count+1}/{len(papers)}] Analyzing: {paper['title']}")
                
                if not self._process_paper(paper, mode, skip_notion):
                    if mode != "full":
                        print(f"\nFAILED: {mode} mode failed on paper: {paper['title']}")
                        return False
                
                processed_count += 1

            print(f"\nSUCCESS: {mode} mode completed successfully.")
            return True

        except Exception as e:
            print(f"\nFATAL ERROR in pipeline: {type(e).__name__}: {e}")
            return False

    def _process_paper(self, paper, mode, skip_notion):
        try:
            # 1. Literature Analysis
            print(f"  > Stage: Literature Analysis")
            lit_analysis = self.lit_agent.analyze(paper['title'], paper['abstract'])
            print(f"    - Key Finding: {str(lit_analysis.get('key_finding') or 'N/A')[:100]}...")
            
            if not skip_notion and mode == "full":
                try:
                    self.notion.create_literature_entry(lit_analysis)
                    print("    - Saved literature entry to Notion.")
                except Exception as e:
                    print(f"    - Error saving literature to Notion: {e}")

            if mode == "smoke":
                return True

            # 2. Hypothesis Generation
            open_question = lit_analysis.get('open_question')
            if not open_question:
                print("    - No open question found. Skipping.")
                return True

            print(f"  > Stage: Hypothesis Generation")
            hypothesis_data = self.hyp_agent.generate(open_question)
            hyp = hypothesis_data.get('hypothesis')
            mech = hypothesis_data.get('mechanism')
            
            if not skip_notion and mode == "full":
                try:
                    self.notion.create_hypothesis_entry(hypothesis_data, paper['title'])
                    print("    - Saved hypothesis to Notion.")
                except Exception as e:
                    print(f"    - Error saving hypothesis to Notion: {e}")

            # 3. Circuit Design
            if hyp and mech:
                print(f"  > Stage: Circuit Design")
                circuit_data = self.circ_agent.design(hyp, mech)
                
                # Strict JSON validation for test-circuit mode is inherent in the agent
                # but we can add a check here if needed.
                if not circuit_data or not isinstance(circuit_data, dict):
                    print("    - FAILED: Circuit agent did not return a valid dict.")
                    return False
                
                if not skip_notion and mode == "full":
                    try:
                        self.notion.create_experiment_entry(circuit_data, hyp)
                        print("    - Saved experiment entry to Notion.")
                    except Exception as e:
                        print(f"    - Error saving experiment to Notion: {e}")

                if mode == "test-circuit":
                    print(f"    - Circuit Design validated: {str(circuit_data.get('circuit_design') or '')[:50]}...")
                    return True

                # 4. Judging
                print(f"  > Stage: Judging")
                evaluation = self.judge_agent.evaluate(hyp, str(circuit_data))
                print(f"    - Evaluation: Score {evaluation.get('impact_score')}/10, Feasibility {evaluation.get('feasibility_score')}/10")

                # 5. Populate Idea_DB
                print(f"  > Stage: Idea_DB Payload Creation")
                idea_data = {
                    "title": f"Project: {str(hyp or '')[:50]}...",
                    "biological_problem": lit_analysis.get("open_question"),
                    "core_mechanism": mech,
                    "circuit_hypothesis": (circuit_data.get("circuit_design") or ''),
                    "readout": (circuit_data.get("expected_signal") or ''),
                    "novelty_score": evaluation.get("novelty_score"),
                    "feasibility_score": evaluation.get("feasibility_score"),
                    "igem_score": evaluation.get("impact_score"),
                    "status": "Draft",
                    "observation": lit_analysis.get("observation"),
                    "hypothesis": hyp,
                    "prediction": hypothesis_data.get("prediction"),
                    "application": lit_analysis.get("possible_igem_mapping"),
                    "judge_comments": evaluation.get("justification"),
                    "measurement_feasibility": evaluation.get("feasibility_score"),
                }

                if mode == "test-idea":
                    if skip_notion:
                        print("\n--- DRY RUN: Idea_DB Payload ---")
                        import json
                        print(json.dumps(idea_data, indent=2))
                        print("------------------------------")
                    else:
                        try:
                            self.notion.create_idea_entry(idea_data)
                            print("    - Saved idea to Notion.")
                        except Exception as e:
                            print(f"    - Error saving idea to Notion: {e}")
                            return False
                    return True

                if not skip_notion:
                    try:
                        self.notion.create_idea_entry(idea_data)
                        print("    - Saved idea to Notion.")
                    except Exception as e:
                        print(f"    - Error saving idea to Notion: {e}")

            return True

        except Exception as e:
            print(f"    - Error processing paper: {e}")
            return False

    def _run_test_circuit(self, skip_notion):
        """Special mode to test circuit generation with a mock hypothesis if no papers are provided."""
        print("  > Running Circuit Test with sample input...")
        mock_hyp = "Targeting senescent cells via p16-promoter driven apoptosis"
        mock_mech = "p16 promoter activates Caspase-3 expression only in senescent cells"
        
        circuit_data = self.circ_agent.design(mock_hyp, mock_mech)
        if circuit_data and isinstance(circuit_data, dict):
            print(f"    - Success: Circuit generated correctly.")
            print(f"    - Design: {str(circuit_data.get('circuit_design') or '')[:100]}...")
            return True
        else:
            print("    - FAILED: Circuit generation failed or returned invalid JSON.")
            return False
