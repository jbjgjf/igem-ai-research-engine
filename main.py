from pipelines.research_pipeline import ResearchPipeline
import sys

def main():
    print("=== iGEM AI Research Engine ===")
    try:
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
