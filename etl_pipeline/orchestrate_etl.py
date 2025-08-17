
import argparse
from steps.whitepapers_modular import WhitepaperETL
from steps.wa_framework_modular import WellArchitectedETL
from steps.architecture_center_modular import ArchitectureCenterETL

# Topic-based pipeline registry for future expansion
PIPELINES = {
    'aws': {
        'whitepapers': lambda: WhitepaperETL().run(),
        'well_architected_framework': lambda: WellArchitectedETL().run(),
        'architecture_center': lambda: ArchitectureCenterETL().run(),
    },
    # 'azure': { ... },
    # 'gcp': { ... },
    # 'open_source': { ... },
}


def main():
    parser = argparse.ArgumentParser(
        description="Run ETL pipeline for datasets by topic."
    )
    parser.add_argument(
        '--topic',
        choices=PIPELINES.keys(),
        default='aws',
        help='Topic to process (default: aws)'
    )
    parser.add_argument(
        '--dataset',
        choices=None,  # Will set dynamically below
        help='Dataset to process (default: all for topic)'
    )
    args, unknown = parser.parse_known_args()

    topic = args.topic
    datasets = PIPELINES[topic]

    # Dynamically set choices for --dataset
    parser._option_string_actions['--dataset'].choices = list(datasets.keys())

    # Parse again to get dataset with choices
    args = parser.parse_args()

    if args.dataset:
        print(f"[Orchestrator] Running {args.dataset} for topic {topic}...")
        datasets[args.dataset]()
    else:
        print(f"[Orchestrator] Running ALL datasets for topic {topic}...")
        for name, fn in datasets.items():
            print(f"[Orchestrator] Running {name}...")
            fn()


if __name__ == "__main__":
    main()
