import traceback

from prepare_districts import main as prepare_districts_main
from extract_features import main as extract_features_main
from download_from_drive import main as download_from_drive_main
from check_dataset_v2 import main as check_dataset_main
from feature_engineering import main as feature_engineering_main
from model_training import main as model_training_main
from inspect_alerts import main as inspect_alerts_main


def run_step(step_name, func):
    print("\n" + "=" * 70)
    print(f"RUNNING: {step_name}")
    print("=" * 70)
    func()
    print(f"COMPLETED: {step_name}")


def main():
    try:
        run_step("1. Prepare districts", prepare_districts_main)
        run_step("2. Extract features from Earth Engine", extract_features_main)
        run_step("3. Copy latest export from Google Drive", download_from_drive_main)
        run_step("4. Clean dataset", check_dataset_main)
        run_step("5. Feature engineering", feature_engineering_main)
        run_step("6. Train model and generate alerts", model_training_main)
        run_step("7. Build summaries and inspection outputs", inspect_alerts_main)

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("You can now launch the dashboard with:")
        print("streamlit run src/dashboard.py")

    except Exception as e:
        print("\n" + "=" * 70)
        print("PIPELINE FAILED")
        print("=" * 70)
        print(str(e))
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()