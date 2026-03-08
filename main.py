import sys
import argparse
from pipelines.research_pipeline import ResearchPipeline
from config import settings

def main():
    parser = argparse.ArgumentParser(description="iGEM AI Research Engine")
    parser.add_argument("--mode", type=str, default="full", 
                        choices=["full", "smoke", "test-circuit", "test-idea", "test-retrieval", "test-critic"],
                        help="Execution mode (default: full)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit the number of papers to process")
    parser.add_argument("--skip-notion", action="store_true",
                        help="Skip saving to Notion")
    parser.add_argument("--source", type=str, default=None,
                        help="Specific paper source to use (optional)")
    parser.add_argument("--paper-title", type=str, default=None,
                        help="Specific paper title to analyze (optional)")

    args = parser.parse_args()

    print("=== iGEM AI Research Engine ===")
    try:
        settings.validate_required_env()
        print(f"LLM Backend: {settings.LLM_BACKEND}")
        if settings.LLM_BACKEND == "mlx":
            print(f"MLX Model: {settings.MLX_MODEL_ID}")
        
        print(f"Mode: {args.mode}")
        if args.limit:
            print(f"Limit: {args.limit}")
        if args.skip_notion:
            print("Skip Notion: True")
        
        pipeline = ResearchPipeline(args)
        success = pipeline.run()
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
