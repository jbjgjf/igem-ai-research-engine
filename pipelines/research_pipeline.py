from integrations.paper_sources import fetch_recent_papers
from integrations.notion_client import NotionIntegration
from agents.literature_agent import LiteratureAgent
from agents.hypothesis_agent import HypothesisAgent
from agents.circuit_agent import CircuitAgent
from agents.judge_agent import JudgeAgent
from config import settings

class ResearchPipeline:
    def __init__(self):
        self.notion = NotionIntegration()
        self.lit_agent = LiteratureAgent()
        self.hyp_agent = HypothesisAgent()
        self.circ_agent = CircuitAgent()
        self.judge_agent = JudgeAgent()

    def run(self):
        print(f"Fetching papers for query: {settings.SEARCH_QUERY}")
        papers = fetch_recent_papers(settings.SEARCH_QUERY, settings.PAPERS_TO_FETCH)
        
        for paper in papers:
            print(f"\nAnalyzing paper: {paper['title']}")
            
            # 1. Literature Analysis
            lit_analysis = self.lit_agent.analyze(paper['title'], paper['abstract'])
            print(f"  - Key Finding: {lit_analysis.get('key_finding', 'N/A')[:100]}...")
            
            # Save to Notion
            try:
                self.notion.create_literature_entry(lit_analysis)
                print("  - Saved literature entry to Notion.")
            except Exception as e:
                print(f"  - Error saving literature to Notion: {e}")

            # 2. Hypothesis Generation
            open_question = lit_analysis.get('open_question')
            if open_question:
                print(f"  - Generating hypothesis for: {open_question[:100]}...")
                hypothesis_data = self.hyp_agent.generate(open_question)
                
                # Save to Notion
                try:
                    self.notion.create_hypothesis_entry(hypothesis_data, paper['title'])
                    print("  - Saved hypothesis to Notion.")
                except Exception as e:
                    print(f"  - Error saving hypothesis to Notion: {e}")

                # 3. Circuit Design
                hyp = hypothesis_data.get('hypothesis')
                mech = hypothesis_data.get('mechanism')
                if hyp and mech:
                    print(f"  - Designing genetic circuit...")
                    circuit_data = self.circ_agent.design(hyp, mech)
                    
                    # Save to Notion
                    try:
                        self.notion.create_experiment_entry(circuit_data, hyp)
                        print("  - Saved experiment entry to Notion.")
                    except Exception as e:
                        print(f"  - Error saving experiment to Notion: {e}")

                    # 4. Judging (Optional, can be stored in Idea DB or as a comment)
                    # For now, let's just print the evaluation
                    evaluation = self.judge_agent.evaluate(hyp, str(circuit_data))
                    print(f"  - Evaluation: Score {evaluation.get('impact_score')}/10, Feasibility {evaluation.get('feasibility_score')}/10")

            print(f"Finished processing: {paper['title']}")

        print("\nResearch pipeline completed.")
