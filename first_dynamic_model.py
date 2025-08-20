import numpy as np

def sigmoid(x): return 1/(1+np.exp(-x))

class FirstDynamicModel:
    def __init__(self, alpha=0.75, lambda_ewma=0.35,
                 thresholds=None, betas=None, gammas=None):
        self.alpha = alpha
        self.lambda_ewma = lambda_ewma
        self.thresholds = thresholds or {"AG_down":0.30,"GA_up":0.38,"AR_up":0.62,"RA_down":0.54}
        self.betas = betas or {"Unemp_Norm":1.0,"Evict_Norm":0.8,"Food_Norm":0.7,"Shutoff_Norm":0.5,"Attendance_Norm":0.4,"FRL_Norm":0.6}
        self.gammas = gammas or {"BenefitUptake":0.9,"OutreachIntensity":0.6,"CommunityPartnerCoverage":0.5}

    def composite_index(self, row):
        z=0.0
        for k,b in self.betas.items(): z += b * float(row.get(k,0.0))
        for k,g in self.gammas.items(): z -= g * float(row.get(k,0.0))
        return float(sigmoid(z))

    def next_F(self, f_prev, row):
        comp = self.composite_index(row)
        f_tilde = (1-self.lambda_ewma)*f_prev + self.lambda_ewma*comp
        return float(np.clip(self.alpha*f_prev + (1-self.alpha)*f_tilde, 0, 1))

    def rag_transition(self, f, last):
        th=self.thresholds
        if last=="Red":   return "Amber" if f < th["RA_down"] else "Red"
        if last=="Green": return "Amber" if f > th["GA_up"] else "Green"
        if f > th["AR_up"]: return "Red"
        if f < th["AG_down"]: return "Green"
        return "Amber"

    def simulate(self, df, f0=None, rag0="Amber"):
        out = df.copy().reset_index(drop=True)
        F=[]; RAG=[]
        first_row = out.iloc[0] if len(out) else {}
        f_prev = self.composite_index(first_row) if f0 is None else float(f0)
        rag_prev = rag0
        for _, row in out.iterrows():
            f_next = self.next_F(f_prev, row)
            rag = self.rag_transition(f_next, rag_prev)
            F.append(f_next); RAG.append(rag)
            f_prev, rag_prev = f_next, rag
        out["F_t"]=F; out["RAG"]=RAG
        return out

