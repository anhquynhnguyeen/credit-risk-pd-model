import sys, json
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from validation import run
r = run(Path(sys.argv[1]).parent / "Sample data for validation.xlsx")
g = r.grades
out = {
  "n": int(len(r.data)), "n_bad": int(r.data["bad"].sum()), "odr": float(r.data["bad"].mean()), "avg_pd": float(r.data["pd"].mean()),
  "auc": r.auc_score, "auc_ci": list(r.auc_ci), "ar": r.ar_score, "auc_grade": r.auc_grade, "ar_cap": r.ar_cap,
  "hl": {k: float(v) for k, v in r.hl.items() if isinstance(v, (int, float))},
  "grades": [{k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()} for row in g.to_dict("records")],
  "curve": [{k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()} for row in r.curve.to_dict("records")],
}
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1, default=str)
print("bai1 ok", list(g.columns), list(r.curve.columns), out["hl"])
