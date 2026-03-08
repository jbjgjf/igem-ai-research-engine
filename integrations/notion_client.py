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

    def create_literature_entry(self, data: dict):
        """Creates a record in the Literature Database."""
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_LITERATURE_DB},
            properties={
                "Paper": self._title(data.get("paper_title", "")),
                "Key Finding": self._rt(data.get("key_finding", "")),
                "Open Question": self._rt(data.get("open_question", "")),
                "SynBio Opportunity": self._rt(data.get("synbio_opportunity", "")),
            }
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

    def create_idea_entry(self, data: dict, hypothesis: str):
        """Creates a record in the Idea Database."""
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_IDEA_DB},
            properties={
                "Title": self._title(hypothesis[:100] + "..." if len(hypothesis) > 100 else hypothesis),
                "Host Organism": self._rt(data.get("host_organism", "")),
                "Sensor": self._rt(data.get("sensor", "")),
                "Genetic Circuit": self._rt(data.get("genetic_circuit", "")),
                "Reporter": self._rt(data.get("reporter", "")),
                "Measurement Method": self._rt(data.get("measurement_method", "")),
            }
        )

    def create_experiment_entry(self, data: dict, hypothesis: str):
        """Creates a record in the Experiment Database."""
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_EXPERIMENT_DB},
            properties={
                "Title": self._title(hypothesis[:100] + "..." if len(hypothesis) > 100 else hypothesis),
                "Host Organism": self._rt(data.get("host_organism", "")),
                "Sensor": self._rt(data.get("sensor", "")),
                "Genetic Circuit": self._rt(data.get("genetic_circuit", "")),
                "Reporter": self._rt(data.get("reporter", "")),
                "Measurement Method": self._rt(data.get("measurement_method", "")),
            }
        )
