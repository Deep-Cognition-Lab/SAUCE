import subprocess
import json
import os
import pandas as pd
import numpy as np
from pathlib import Path
from experiments.experiment import Experiment  # Use actual experiment class

# Define paths
data_path = "/Users/zohar/Downloads/Data2"  # Folder where JSONs are stored
experiment_c_path = "/Users/zohar/Downloads/experiment_C_majority_rule_2"
pro_conviction_folder = os.path.join(experiment_c_path, "pro_conviction_5_1_left")
pro_acquittal_folder = os.path.join(experiment_c_path, "pro_acquittal_5_1_left")
output_folder = experiment_c_path  # ✅ FIXED to avoid double folder issue
final_output_path = os.path.join(output_folder, "final_report.xlsx")

def calculate_z_score(pw_c, pw_a, n_c, n_a):
    """Computes the z-score for asymmetry testing."""
    if n_c == 0 or n_a == 0:
        print("\nZ-Score Calculation: No cases processed in one or both groups. Returning NaN.")
        return np.nan  # Avoid division by zero if one of the groups has no data

    p_diff = pw_a - pw_c
    pooled_var = ((pw_c * (1 - pw_c)) / n_c) + ((pw_a * (1 - pw_a)) / n_a)

    if pooled_var <= 0:
        print("\nZ-Score Calculation: Variance too low, returning 0.")
        z = 0.0
    else:
         z = p_diff / np.sqrt(pooled_var)

    # Print significance level for reference
    significance = "(Not Significant)"
    if abs(z) > 2.58:
        significance = "** (p < 0.01, Highly Significant)"
    elif abs(z) > 1.96:
        significance = "* (p < 0.05, Significant)"

    print(f"\nComputed Z-Score: {z:.3f} {significance}")

    return z

def run_experiment_from_json(config_path, group_folder):
    """Runs a single experiment from a JSON config and saves the results."""
    try:
        print(f"\nRunning experiment for: {os.path.basename(config_path)}")

        # Load JSON config
        with open(config_path, "r", encoding="utf-8") as f:
            conf_json = json.load(f)

        # Create subfolder for this experiment
        experiment_name = os.path.splitext(os.path.basename(config_path))[0]  # Extracts filename without extension
        experiment_output_dir = os.path.join(group_folder, experiment_name)
        os.makedirs(experiment_output_dir, exist_ok=True)

        # Define output filenames
        output_json = os.path.join(experiment_output_dir, f"{experiment_name}_hist.json")
        output_pdf = os.path.join(experiment_output_dir, f"{experiment_name}_hist.pdf")
        output_excel = os.path.join(experiment_output_dir, f"Results_{experiment_name}.xlsx")  # ✅ Ensures Excel is stored

        # Inject output path into config
        conf_json["output_file"] = str(output_json)

        # Run the experiment
        experiment = Experiment.load_from_string(json.dumps(conf_json))
        experiment.run()

        # Retrieve deliberation results
        end_type = experiment.session_room.experiment.end_type
        rounds_taken = end_type.rounds
        final_verdict = end_type.unanimity_status  # Stores "Guilty", "Not Guilty", or "Hung Jury"

        # Save deliberation output to JSON
        experiment_output = {
            "chat_room": [{"entity": {"name": e.entity.name}, "answer": e.answer} for e in experiment.session_room.chat_room]
        }
        with open(output_json, "w", encoding="utf-8") as json_file:
            json.dump(experiment_output, json_file, indent=4)

        print(f"✅ JSON saved: {output_json}")

        # Call external script to process the JSON and create a PDF
        subprocess.run(["python", "utils/extract_deliberation.py", str(output_json), str(output_pdf)])
        print(f"✅ Deliberation processed: JSON -> {output_json}, PDF -> {output_pdf}")

        # Save individual experiment results to Excel ✅ Now saves per experiment
        result_data = pd.DataFrame([{
            "File": os.path.basename(config_path),
            "Rounds Taken": rounds_taken,
            "Final Verdict": final_verdict
        }])
        result_data.to_excel(output_excel, index=False)
        print(f"✅ Experiment results saved at: {output_excel}")

        return {
            "File": os.path.basename(config_path),
            "Rounds Taken": rounds_taken,
            "Final Verdict": final_verdict
        }

    except Exception as e:
        print(f"❌ Error during experiment {os.path.basename(config_path)}: {e}")
        return None

def process_individual_experiments(group_folder):
    """Reads each individual case file (Results_group_X.xlsx) and computes per-group statistics."""
    all_groups = [f for f in os.listdir(group_folder) if os.path.isdir(os.path.join(group_folder, f))]

    all_results = []
    for group in all_groups:
        file_path = os.path.join(group_folder, group, f"Results_{group}.xlsx")
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            all_results.append(df.iloc[0].to_dict())  # ✅ Extracting first row

    if not all_results:
        print("\n⚠️ Warning: No results found. Returning zeros.")
        return 0, 0, 0, 0, 0, 0, 0

    # Convert to DataFrame
    summary_df = pd.DataFrame(all_results)

    # Determine majority verdict based on folder
    majority_verdict = "Guilty" if "conviction" in group_folder else "Not Guilty"

    # Count outcomes
    majority_wins = summary_df["Final Verdict"].eq(majority_verdict).sum()
    minority_flips = summary_df["Final Verdict"].ne(majority_verdict).sum() - summary_df["Final Verdict"].eq("Hung").sum()
    hung_jury_count = summary_df["Final Verdict"].eq("Hung").sum()
    total_cases = len(summary_df)

    # Compute probabilities
    p_w = majority_wins / total_cases if total_cases > 0 else 0
    p_f = minority_flips / total_cases if total_cases > 0 else 0
    p_h = hung_jury_count / total_cases if total_cases > 0 else 0

    # Save corrected summary file as `summary_results.xlsx`
    summary_path = os.path.join(group_folder, "summary_results.xlsx")
    summary_df.to_excel(summary_path, index=False)

    print(f"✅ Updated per-group summary saved at: {summary_path}")

    return total_cases, majority_wins, minority_flips, hung_jury_count, p_w, p_f, p_h

# Run all JSON files from each folder
for json_file in os.listdir(os.path.join(data_path, "pro_conviction_5_1_left")):
    if json_file.endswith(".json"):
        run_experiment_from_json(os.path.join(data_path, "pro_conviction_5_1_left", json_file), pro_conviction_folder)

for json_file in os.listdir(os.path.join(data_path, "pro_acquittal_5_1_left")):
    if json_file.endswith(".json"):
        run_experiment_from_json(os.path.join(data_path, "pro_acquittal_5_1_left", json_file), pro_acquittal_folder)

# Process all JSON files to generate per-group summaries
n_c, mw_c, mf_c, hj_c, pw_c, pf_c, ph_c = process_individual_experiments(pro_conviction_folder)
n_a, mw_a, mf_a, hj_a, pw_a, pf_a, ph_a = process_individual_experiments(pro_acquittal_folder)

# Compute Z-score & final report
z_score = calculate_z_score(pw_c, pw_a, n_c, n_a)

# Compute total row
total_n = n_c + n_a
total_mw = mw_c + mw_a
total_mf = mf_c + mf_a
total_hj = hj_c + hj_a
avg_pw = (pw_c + pw_a) / 2
avg_pf = (pf_c + pf_a) / 2
avg_ph = (ph_c + ph_a) / 2

# Create the final table
final_data = [
    ["4:2 (C)", n_c, mw_c, mf_c, hj_c, pw_c, pf_c, ph_c, ""],  # Majority Conviction Group
    ["4:2 (A)", n_a, mw_a, mf_a, hj_a, pw_a, pf_a, ph_a, ""],  # Majority Acquittal Group
    ["Total", total_n, total_mw, total_mf, total_hj, avg_pw, avg_pf, avg_ph, z_score]  # Overall Total
]

# Convert to DataFrame
final_df = pd.DataFrame(final_data, columns=[
    "Group", "n", "Majority Win", "Minority Flip", "Hung Jury",
    "P(W)", "P(F)", "P(H)", "Z-Score"
])

# Ensure output directory exists
os.makedirs(output_folder, exist_ok=True)

# Save the final table
final_df.to_excel(final_output_path, index=False)

print(f"\n✅ final comparative report saved at: {final_output_path}")
