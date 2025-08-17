
import subprocess
import os


def run_architecture_center_pipeline():
    print("[ETL] Running Architecture Center pipeline")

    def run_script(script):
        result = subprocess.run(
            ["python", script], capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise RuntimeError(f"Script {script} failed.")

    # 1. Crawl Architecture Center
    run_script("../../crawl_aws_architecture_center.py")
    if not os.path.exists(
        "../../aws_architecture_center_titles_summaries.jsonl"
    ):
        print(
            "[ERROR] .jsonl not created. Aborting."
        )
        return

    print("[ETL] Architecture Center pipeline complete.")
