from pipelines.research_pipeline import ResearchPipeline
from config import settings
import sys

def main():
    print("=== iGEM AI Research Engine ===")
    try:
        settings.validate_required_env()
        print(f"LLM Backend: {settings.LLM_BACKEND}")
        if settings.LLM_BACKEND == "mlx":
            print(f"MLX Model: {settings.MLX_MODEL_ID}")
        
        pipeline = ResearchPipeline()
        pipeline.run()
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
