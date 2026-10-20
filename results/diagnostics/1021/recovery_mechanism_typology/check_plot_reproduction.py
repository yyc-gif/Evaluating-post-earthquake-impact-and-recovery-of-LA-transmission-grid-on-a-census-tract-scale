"""Repeat rendering from saved numerical arrays; no models are refitted."""
from support import *
import subprocess


def main():
    paths=[*HERE.glob("*.pdf"),*HERE.glob("*.png"),*HERE.glob("pdf_previews/*.png"),
           HERE/"PLOTTED_EXACT_CLASS_MEAN_CURVES.csv"]
    before={p.relative_to(HERE).as_posix():sha(p) for p in paths}
    subprocess.run([sys.executable,str(HERE/"plot_recovery.py")],cwd=ROOT,check=True)
    after={p.relative_to(HERE).as_posix():sha(p) for p in paths}
    assert before==after
    dump("PLOT_REPRODUCIBILITY_QA.json",{
        "status":"PASS_BYTE_IDENTICAL","files":after,"rendered_from_saved_numerical_arrays":True,
        "all_full_and_resampled_fit_arithmetic_verified_separately":True,
        "full_model_refits_for_exact_deterministic_test":["A-full K2 seed42","A-PCA K3 seed42","B K3 seed42"],
        "all_1215_models_refitted_a_second_time":False,
        "explanation":"Every saved model's geometry/labels and scores were reconstructed independently; three registered fits were deterministically refitted in tests. No second exploratory search."})
    print("All",len(paths),"plot/data exports reproduced byte-identically.")


if __name__=="__main__":
    main()
