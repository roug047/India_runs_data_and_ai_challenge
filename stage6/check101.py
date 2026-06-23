import json, numpy as np
import sys; sys.path.insert(0, ".")
from common import config
import pandas as pd, lightgbm as lgb
from scipy.stats import spearmanr
from sklearn.model_selection import KFold
from stage5.composite import score_dataframe

df = pd.read_parquet(config.FEATURES_PARQUET)
feats = json.load(open(config.LGB_FEATURES_JSON))
golden = {k:int(v) for k,v in json.load(open(config.GOLDEN_SET_JSON)).items()}
aids = [c for c in golden if c in df.index]
y = np.array([golden[c] for c in aids])
def mm(a): a=np.asarray(a,float); r=a.max()-a.min(); return (a-a.min())/r if r>1e-12 else a*0

m_rule = lgb.Booster(model_file=str(config.RANKER_RULE_TXT))
m_llm  = lgb.Booster(model_file=str(config.RANKER_LLM_TXT))
Xa = df.loc[aids, feats].fillna(0).values
pr, pl = mm(m_rule.predict(Xa)), mm(m_llm.predict(Xa))
alpha = json.load(open(config.BLEND_JSON))["alpha_rule"]
ranker = mm(alpha*pr + (1-alpha)*pl)
wts = json.load(open(config.COMPOSITE_WEIGHTS_JSON))
comp = mm(score_dataframe(df.loc[aids], wts))          # <-- no .values

kf = KFold(n_splits=5, shuffle=True, random_state=1)
r_ranker, r_comp = [], []
for _, te in kf.split(aids):
    if len(set(y[te])) < 2: continue
    r_ranker.append(spearmanr(ranker[te], y[te]).correlation)
    r_comp.append(spearmanr(comp[te], y[te]).correlation)
print(f"held-out Spearman  ranker={np.nanmean(r_ranker):.3f}  composite={np.nanmean(r_comp):.3f}")
print(f"per-fold ranker: {[round(x,2) for x in r_ranker]}")
print(f"per-fold comp:   {[round(x,2) for x in r_comp]}")

# full-pool top-100 agreement
full_ranker = mm(alpha*mm(m_rule.predict(df[feats].fillna(0).values)) + (1-alpha)*mm(m_llm.predict(df[feats].fillna(0).values)))
full_comp = mm(score_dataframe(df, wts))               # <-- no .values
top_r = set(pd.Series(full_ranker, index=df.index).nlargest(100).index)
top_c = set(pd.Series(full_comp, index=df.index).nlargest(100).index)
print(f"top-100 overlap between ranker and composite: {len(top_r & top_c)}/100")