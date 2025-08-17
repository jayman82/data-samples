import subprocess
import os


def run_wa_framework_pipeline():
    print("[ETL] Running Well-Architected Framework pipeline")

    def run_script(script):
        result = subprocess.run(
            ["python", script], capture_output=True, text=True
            )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise RuntimeError(f"Script {script} failed.")

    # 1. Crawl Well-Architected Framework
    run_script("../../crawl_aws_wa_framework.py")
    if not os.path.exists("../../aws_wa_framework_crawl.jsonl"):
        print("[ERROR] aws_wa_framework_crawl.jsonl not created. Aborting.")
        return

    print("[ETL] Well-Architected Framework pipeline complete.")
