from notion_client import Client
from config import settings

class NotionIntegration:
    def __init__(self):
        self.notion = Client(auth=settings.NOTION_TOKEN)

    def create_literature_entry(self, data: dict):
        """Creates a record in the Literature Database."""
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_LITERATURE_DB},
            properties={
                "Title": {"title": [{"text": {"content": data["paper_title"]}}]},
                "Key Finding": {"rich_text": [{"text": {"content": data["key_finding"]}}]},
                "Open Question": {"rich_text": [{"text": {"content": data["open_question"]}}]},
                "SynBio Opportunity": {"rich_text": [{"text": {"content": data["synbio_opportunity"]}}]},
            }
        )

    def create_hypothesis_entry(self, data: dict, paper_title: str):
        """Creates a record in the Hypothesis Database."""
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_HYPOTHESIS_DB},
            properties={
                "Paper Title": {"title": [{"text": {"content": paper_title}}]},
                "Observation": {"rich_text": [{"text": {"content": data["observation"]}}]},
                "Hypothesis": {"rich_text": [{"text": {"content": data["hypothesis"]}}]},
                "Mechanism": {"rich_text": [{"text": {"content": data["mechanism"]}}]},
                "Prediction": {"rich_text": [{"text": {"content": data["prediction"]}}]},
            }
        )

    def create_idea_entry(self, data: dict, hypothesis: str):
        """Creates a record in the Idea Database."""
        self.notion.pages.create(
            parent={"database_id": settings.NOTION_IDEA_DB},
            properties={
                "Hypothesis": {"title": [{"text": {"content": hypothesis[:100] + "..." if len(hypothesis) > 100 else hypothesis}}]},
                "Host Organism": {"rich_text": [{"text": {"content": data["host_organism"]}}]},
                "Sensor": {"rich_text": [{"text": {"content": data["sensor"]}}]},
                "Genetic Circuit": {"rich_text": [{"text": {"content": data["genetic_circuit"]}}]},
                "Reporter": {"rich_text": [{"text": {"content": data["reporter"]}}]},
                "Measurement Method": {"rich_text": [{"text": {"content": data["measurement_method"]}}]},
            }
        )
