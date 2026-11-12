import sys, json, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import roc_curve
import features as F, model as M
from charts import LABELS
df = F.build_features(F.load_raw(Path(sys.argv[1]).parent / "data.csv"))
r = M.run(df); sc = M.compare_splits(df)
L = lambda c: LABELS.get(c, c)
sets = r["sets"]; test = sets["Test OOT"]
def roc(p, y, k=60):
    fpr, tpr, _ = roc_curve(y, p); idx = np.unique(np.linspace(0, len(fpr) - 1, k).astype(int))
    return [[float(fpr[i]), float(tpr[i])] for i in idx]
iv = r["iv_log"].sort_values("IV", ascending=False).head(20)
def cat(d): return "keep" if d == "Giữ" else ("sign" if "ngược" in d or "tương quan" in d else "low")
imp = r["gb_importance"].head(10)
out = {
  "n": int(len(df)), "bad_rate": float(df["flag_bad"].mean()),
  "monthly": [{"month": m, "n": int(row.n), "bad_rate": float(row.bad_rate), "set": row["Tập"]} for m, row in r["monthly"].iterrows()],
  "sets": {k: {"n": int(len(v)), "bad_rate": float(v["flag_bad"].mean())} for k, v in sets.items()},
  "iv": [{"var": L(c), "iv": float(row.IV), "cat": cat(row["Quyết định"])} for c, row in iv.iterrows()],
  "n_selected": len(r["selected"]), "sign_dropped": [L(c) for c in r["sign_dropped"]], "selected": [L(c) for c in r["selected"]],
  "woe": {c: {"label": L(c), "iv": float(r["binners"][c].iv),
              "bins": [{"bin": str(b), "n": int(t.n), "bad_rate": float(t.bad_rate), "woe": float(t.woe)} for b, t in r["binners"][c].table.iterrows()]}
          for c in ["n_loan_apps", "n_apps", "education"]},
  "perf": [{"model": x["Mô hình"], "set": x["Tập"], "auc": float(x.AUC), "gini": float(x.Gini)} for _, x in r["perf"].iterrows()],
  "roc": {m: roc(p["Test OOT"], test["flag_bad"]) for m, p in r["preds"].items()},
  "deciles": {m: [{"g": int(i), "bad_rate": float(t.bad_rate), "pd": float(t.pd_mean)} for i, t in d.iterrows()] for m, d in r["deciles"].items()},
  "hl": {m: float(v["HL"]) for m, v in r["hl"].items()},
  "split": {"time": sc["time"], "mean": sc["random"].mean().to_dict(), "min": sc["random"].min().to_dict(), "max": sc["random"].max().to_dict()},
  "no_fb": {m: float(v) for m, v in sc["no_fb_by_month"].items()},
  "lr_coef": [{"var": L(c), "v": float(abs(v))} for c, v in r["lr_coef"].abs().sort_values(ascending=False).items()],
  "gb_imp": [{"var": L(c), "v": float(v)} for c, v in imp.items()],
  "scorecard": [{"bin": str(x["Nhóm"]), "n": int(x["Số hồ sơ"]), "bad_rate": float(x["Tỷ lệ bad"]), "woe": float(x["WOE"]), "pts": int(x["Điểm"])}
                for _, x in r["scorecard"].query("`Biến` == 'n_loan_apps'").iterrows()],
}
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print("bai2 ok", out["hl"], out["split"]["time"], {k: round(v, 3) for k, v in out["no_fb"].items()})
