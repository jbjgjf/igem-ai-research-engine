from notion_client import Client
from config import settings

class NotionIntegration:
    def __init__(self):
        self.notion = Client(auth=settings.NOTION_TOKEN)

    def _rt(self, value: str):
        safe = "" if value is None else str(value)
        return {"rich_text": [{"text": {"content": safe}}]}

    def _title(self, value: str):
        safe = "" if value is None else str(value)
        return {"title": [{"text": {"content": safe}}]}

    def _select(self, value: Any):
        if not value: return None
        # If list, take first
        if isinstance(value, list):
            name = str(value[0]) if value else None
        else:
            name = str(value)
        return {"select": {"name": name}} if name else None

    def _multi_select(self, value: Any):
        if not value: return {"multi_select": []}
        if isinstance(value, str):
            names = [value]
        elif isinstance(value, list):
            names = [str(v) for v in value]
        else:
            names = [str(value)]
        return {"multi_select": [{"name": name} for name in names if name]}

    def _number(self, value: Any):
        try:
            return {"number": float(value)}
        except (TypeError, ValueError):
            return None

    def create_literature_entry(self, data: dict):
        """Creates a record in the Literature Database."""
        properties = {
            "Paper": self._title(data.get("paper_title", "")),
            "Key finding": self._rt(data.get("key_finding", "")),
            "Open question": self._rt(data.get("open_question", "")),
            "Possible iGEM mapping": self._rt(data.get("possible_igem_mapping", "")),
            "Biological system": self._select(data.get("biological_system")),
            "Aging mechanism": self._multi_select(data.get("aging_mechanism")),
            "Method used": self._multi_select(data.get("method_used")),
            "Limitation": self._rt(data.get("limitation", "")),
            "Aging relevance": self._rt(data.get("aging_relevance", "")),
            "Alternative interpretation": self._rt(data.get("alternative_interpretation", "")),
            "Confidence": self._number(data.get("confidence")),
            "Measurement readout": self._rt(data.get("measurement_readout", "")),
            "Observation": self._rt(data.get("observation", "")),
            "Raw extraction": self._rt(data.get("raw_extraction", "")),
            "Why unresolved": self._rt(data.get("why_unresolved", "")),
        }
        # Filter out None values (like failed number coercion)
        properties = {k: v for k, v in properties.items() if v is not None}
        
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_LITERATURE_DB},
            properties=properties
        )

    def create_hypothesis_entry(self, data: dict, paper_title: str):
        """Creates a record in the Hypothesis Database."""
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_HYPOTHESIS_DB},
            properties={
                "Title": self._title(paper_title),
                "Observation": self._rt(data.get("observation", "")),
                "Hypothesis": self._rt(data.get("hypothesis", "")),
                "Mechanism": self._rt(data.get("mechanism", "")),
                "Prediction": self._rt(data.get("prediction", "")),
            }
        )

    def create_experiment_entry(self, data: dict, hypothesis: str):
        """Creates a record in the Experiment Database."""
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_EXPERIMENT_DB},
            properties={
                "Title": self._title(hypothesis[:100] + "..." if len(hypothesis) > 100 else hypothesis),
                "Host organism": self._rt(data.get("host_organism", "")),
                "Genetic parts needed": self._rt(data.get("genetic_parts", "")),
                "Measurement method": self._rt(data.get("measurement_method", "")),
                "Circuit design": self._rt(data.get("circuit_design", "")),
                "Expected signal": self._rt(data.get("expected_signal", "")),
                "Input signal": self._rt(data.get("input_signal", "")),
                "Output signal": self._rt(data.get("output_signal", "")),
                "Reporter": self._rt(data.get("reporter", "")),
                "Sensor": self._rt(data.get("sensor", "")),
                "Minimal viable version": self._rt(data.get("mvp_version", "")),
                "Failure points": self._rt(data.get("failure_points", "")),
                "Biosafety concerns": self._rt(data.get("biosafety_concerns", "")),
                "Status": self._select("Planned"), # Default status
            }
        )
