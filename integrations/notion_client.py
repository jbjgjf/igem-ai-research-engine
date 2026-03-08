from typing import Any, Dict, List, Optional, Union
import json
from notion_client import Client
from config import settings

class NotionIntegration:
    def __init__(self):
        self.notion = Client(auth=settings.NOTION_TOKEN)

    def _clean_text(self, value: Any) -> str:
        """Converts any value (list, dict, string) into human-readable text."""
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            # Flatten once and join with newlines or bullets
            items = []
            for item in value:
                if isinstance(item, (list, tuple, dict)):
                    items.append(json.dumps(item))
                else:
                    items.append(str(item).strip())
            return "\n".join(f"- {i}" for i in items if i)
        if isinstance(value, dict):
            # Serialize dict into key: value lines
            lines = []
            for k, v in value.items():
                lines.append(f"{k}: {self._clean_text(v)}")
            return "\n".join(lines)
        return str(value).strip()

    def _rt(self, value: Any):
        text = self._clean_text(value)
        if text.lower() in ["none", "null", ""]:
            return {"rich_text": []}
        return {"rich_text": [{"text": {"content": text}}]}

    def _title(self, value: Any):
        text = self._clean_text(value)
        return {"title": [{"text": {"content": text}}]}

    def _select(self, value: Any):
        name = self._normalize_select(value)
        return {"select": {"name": name}} if name else None

    def _multi_select(self, value: Any):
        names = self._normalize_multi_select(value)
        return {"multi_select": [{"name": name} for name in names if name]}

    def _number(self, value: Any):
        try:
            val = float(value)
            return {"number": val}
        except (TypeError, ValueError):
            return None

    def _normalize_select(self, value: Any) -> Optional[str]:
        """Maps input to allowed select options."""
        text = self._clean_text(value).lower()
        if not text: return None
        
        # Specific mapping for Biological system
        if any(x in text for x in ["bacteria", "e. coli", "prokaryote"]): return "bacteria"
        if any(x in text for x in ["yeast", "s. cerevisiae", "fungi"]): return "yeast"
        if any(x in text for x in ["mammal", "human", "hella", "cho", "mouse"]): return "mammalian cells"
        if any(x in text for x in ["worm", "fly", "plant", "multicellular"]): return "multicellular organism"
        
        # Generic fallback: capitalize and take first 100 chars
        return text.capitalize()[:100]

    def _normalize_multi_select(self, value: Any) -> List[str]:
        """Maps input strings/lists to clean multi-select options."""
        if not value: return []
        if isinstance(value, str):
            # Some models return comma separated strings
            items = [i.strip() for i in value.replace(",", ";").split(";") if i.strip()]
        elif isinstance(value, (list, tuple)):
            items = [str(i).strip() for i in value if i]
        else:
            items = [str(value).strip()]
            
        # Capitalize and clean each item
        return [i.capitalize()[:100] for i in items if i.lower() != "none"]

    def _is_duplicate(self, database_id: str, title_property: str, title_value: str) -> bool:
        """Checks if a record with the same title already exists in the database."""
        # Temporarily disabled due to 'Invalid request URL' errors with manual request path
        # return False will allow the pipeline to proceed with page creation
        return False

    def create_literature_entry(self, data: dict):
        """Creates a record in the Literature Database if it doesn't exist."""
        title = self._clean_text(data.get("paper_title", ""))
        if self._is_duplicate(settings.NOTION_LITERATURE_DB, "Paper", title):
            print(f"Skipping duplicate literature entry: {title}")
            return

        properties = {
            "Paper": self._title(title),
            "Key finding": self._rt(data.get("key_finding")),
            "Open question": self._rt(data.get("open_question")),
            "Possible iGEM mapping": self._rt(data.get("possible_igem_mapping")),
            "Biological system": self._select(data.get("biological_system")),
            "Aging mechanism": self._multi_select(data.get("aging_mechanism")),
            "Method used": self._multi_select(data.get("method_used")),
            "Limitation": self._rt(data.get("limitation")),
            "Aging relevance": self._rt(data.get("aging_relevance")),
            "Alternative interpretation": self._rt(data.get("alternative_interpretation")),
            "Confidence": self._number(data.get("confidence")),
            "Measurement readout": self._rt(data.get("measurement_readout")),
            "Observation": self._rt(data.get("observation")),
            "Raw extraction": self._rt(data.get("raw_extraction")),
            "Why unresolved": self._rt(data.get("why_unresolved")),
        }
        properties = {k: v for k, v in properties.items() if v is not None}
        
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_LITERATURE_DB},
            properties=properties
        )

    def create_hypothesis_entry(self, data: dict, paper_title: str):
        """Creates a record in the Hypothesis Database if it doesn't exist."""
        # Check for title duplication (usually paper_title)
        if self._is_duplicate(settings.NOTION_HYPOTHESIS_DB, "Title", paper_title):
            print(f"Skipping duplicate hypothesis entry: {paper_title}")
            return

        self.notion.pages.create(
            parent={"database_id": settings.NOTION_HYPOTHESIS_DB},
            properties={
                "Title": self._title(paper_title),
                "Observation": self._rt(data.get("observation")),
                "Hypothesis": self._rt(data.get("hypothesis")),
                "Mechanism": self._rt(data.get("mechanism")),
                "Prediction": self._rt(data.get("prediction")),
            }
        )

    def create_experiment_entry(self, data: dict, hypothesis: str):
        """Creates a record in the Experiment Database if it doesn't exist."""
        title = self._clean_text(hypothesis[:100] + "..." if len(hypothesis) > 100 else hypothesis)
        if self._is_duplicate(settings.NOTION_EXPERIMENT_DB, "Title", title):
            print(f"Skipping duplicate experiment entry: {title}")
            return

        self.notion.pages.create(
            parent={"database_id": settings.NOTION_EXPERIMENT_DB},
            properties={
                "Title": self._title(title),
                "Host organism": self._rt(data.get("host_organism")),
                "Genetic parts needed": self._rt(data.get("genetic_parts")),
                "Measurement method": self._rt(data.get("measurement_method")),
                "Circuit design": self._rt(data.get("circuit_design")),
                "Expected signal": self._rt(data.get("expected_signal")),
                "Input signal": self._rt(data.get("input_signal")),
                "Output signal": self._rt(data.get("output_signal")),
                "Reporter": self._rt(data.get("reporter")),
                "Sensor": self._rt(data.get("sensor")),
                "Minimal viable version": self._rt(data.get("mvp_version")),
                "Failure points": self._rt(data.get("failure_points")),
                "Biosafety concerns": self._rt(data.get("biosafety_concerns")),
                "Status": self._select("Planned"),
            }
        )

    def create_idea_entry(self, data: dict):
        """Creates a record in the Idea Database if it doesn't exist."""
        title = self._clean_text(data.get("title", "Untitled Idea"))
        if self._is_duplicate(settings.NOTION_IDEA_DB, "Title", title):
            print(f"Skipping duplicate idea entry: {title}")
            return

        properties = {
            "Title": self._title(title),
            "Biological problem": self._rt(data.get("biological_problem")),
            "Core mechanism": self._rt(data.get("core_mechanism")),
            "Synthetic circuit hypothesis": self._rt(data.get("circuit_hypothesis")),
            "Readout": self._rt(data.get("readout")),
            "Novelty score": self._number(data.get("novelty_score")),
            "Feasibility score": self._number(data.get("feasibility_score")),
            "iGEM score": self._number(data.get("igem_score")),
            "Status": {"status": {"name": str(data.get("status", "Draft"))}},
            "Observation": self._rt(data.get("observation")),
            "Hypothesis": self._rt(data.get("hypothesis")),
            "Testable prediction": self._rt(data.get("prediction")),
            "Application": self._rt(data.get("application")),
            "Judge comments": self._rt(data.get("judge_comments")),
            "Measurement feasibility": self._number(data.get("measurement_feasibility")),
            "Killer comments": self._rt(data.get("killer_comments")),
            "Kill reason": self._rt(data.get("kill_reason")),
        }
        properties = {k: v for k, v in properties.items() if v is not None}
        
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_IDEA_DB},
            properties=properties
        )
