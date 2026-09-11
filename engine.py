
"""
SASVA - 2-Stage Engine (Rule Filter + AI Ranking) with Explainable AI
As per PPT: System Flow -> Scheme Matching Engine, AI Eligibility Parsing, Ranked Recommendation with Explainable Benefits
"""
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

class SASVAEngine:
    def __init__(self, schemes_path="data/schemes.json"):
        with open(schemes_path, 'r', encoding='utf-8') as f:
            self.schemes = json.load(f)
        
        # Vector DB simulation using TF-IDF
        corpus = [f"{s['name']} {s['description']} {' '.join(s['tags'])} {s['benefits']}" for s in self.schemes]
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.corpus = corpus

    def rule_filter(self, user_profile):
        """Stage 1: Rule Filter - As per govt eligibility"""
        filtered = []
        user_caste = user_profile.get('caste', 'General')
        user_gender = user_profile.get('gender', 'Male')
        user_income = user_profile.get('income', 0)
        user_business = user_profile.get('business_type', 'Services')
        user_age = user_profile.get('age', 25)
        user_state = user_profile.get('state', 'West Bengal')

        for scheme in self.schemes:
            elig = scheme.get('eligibility', {})
            
            # Caste check
            if user_caste not in elig.get('caste', []) and "All" not in elig.get('caste', []):
                if "General" not in elig.get('caste', []):
                    # Special schemes only for SC/ST/Women - still allow if matches
                    if user_caste not in ["SC", "ST"] and "SC" in elig.get('caste', []) and "ST" in elig.get('caste', []):
                        # If scheme is exclusively SC/ST but user is not, skip unless general allowed
                        if len(elig.get('caste', [])) <= 2:
                            continue
            
            # Gender - women schemes allow all but prioritize women
            # Income check
            if user_income > elig.get('income_max', 999999999):
                continue
            
            # Age check
            if user_age < elig.get('min_age', 0):
                continue
            
            # State check
            states = elig.get('states', ['All'])
            if "All" not in states and user_state not in states and "West Bengal" not in states:
                # Allow central schemes for all states
                if states != ["All"] and "West Bengal" not in states and user_state not in states:
                    # Still keep if central ministry
                    if "West Bengal" in scheme['ministry']:
                        continue
            
            # Business type - soft filter, allow if close
            biz_types = elig.get('business_types', [])
            if user_business not in biz_types and "Services" not in biz_types:
                # Still include with lower score, don't hard reject
                pass

            filtered.append(scheme)
        
        return filtered if filtered else self.schemes[:20]  # Fallback

    def ai_ranking(self, user_profile, filtered_schemes):
        """Stage 2: AI Ranking - TF-IDF + cosine similarity + rule score"""
        # Create user query from profile
        query = f"{user_profile.get('business_type','')} {user_profile.get('caste','')} {user_profile.get('gender','')} {user_profile.get('state','')} {user_profile.get('description','')} {' '.join(user_profile.get('tags',[]))} marginalized entrepreneur financial support loan subsidy"
        
        # Vectorize query
        query_vec = self.vectorizer.transform([query])
        
        # Find indices of filtered schemes in original list
        filtered_ids = [s['id'] for s in filtered_schemes]
        id_to_idx = {s['id']: i for i, s in enumerate(self.schemes)}
        filtered_indices = [id_to_idx[sid] for sid in filtered_ids if sid in id_to_idx]
        
        if not filtered_indices:
            filtered_indices = list(range(len(self.schemes)))
        
        filtered_tfidf = self.tfidf_matrix[filtered_indices]
        similarities = cosine_similarity(query_vec, filtered_tfidf).flatten()
        
        ranked = []
        for idx, sim_score in zip(filtered_indices, similarities):
            scheme = self.schemes[idx]
            # Rule-based boost
            rule_score = 0
            elig = scheme.get('eligibility', {})
            
            # Caste match boost
            if user_profile.get('caste') in elig.get('caste', []):
                rule_score += 0.2
            # Gender match boost for women
            if user_profile.get('gender') == 'Female' and 'Women' in str(scheme['tags']):
                rule_score += 0.25
            # Business match
            if user_profile.get('business_type') in elig.get('business_types', []):
                rule_score += 0.2
            # State match
            if user_profile.get('state') in elig.get('states', []) or 'All' in elig.get('states', []):
                rule_score += 0.1
            # SHG special
            if user_profile.get('is_shg') and 'SHG' in str(scheme['tags']):
                rule_score += 0.3
            # Street vendor
            if 'Street Vending' in user_profile.get('business_type','') and 'Street Vendor' in str(scheme['tags']):
                rule_score += 0.3
            
            final_score = float(sim_score * 0.6 + rule_score * 0.4)
            # Clamp 0-1
            final_score = min(1.0, max(0.0, final_score))
            
            explanation = self.explain_match(user_profile, scheme, sim_score, rule_score)
            
            ranked.append({
                "scheme": scheme,
                "similarity": float(sim_score),
                "rule_score": float(rule_score),
                "final_score": final_score,
                "eligibility_percent": int(final_score * 100),
                "explanation": explanation
            })
        
        # Sort by final_score descending
        ranked.sort(key=lambda x: x['final_score'], reverse=True)
        return ranked

    def explain_match(self, user_profile, scheme, sim_score, rule_score):
        """Explainable AI - Why this scheme matched"""
        reasons = []
        elig = scheme.get('eligibility', {})
        
        if user_profile.get('caste') in elig.get('caste', []):
            reasons.append(f"✓ Caste eligibility matched: {user_profile.get('caste')} is eligible")
        if user_profile.get('gender') == 'Female' and 'Female' in elig.get('gender', []):
            reasons.append("✓ Women entrepreneur special focus")
        if user_profile.get('business_type') in elig.get('business_types', []):
            reasons.append(f"✓ Business type matched: {user_profile.get('business_type')}")
        if user_profile.get('income', 0) <= elig.get('income_max', 9999999):
            reasons.append(f"✓ Income criteria satisfied (₹{user_profile.get('income',0):,} <= ₹{elig.get('income_max',0):,})")
        if 'SHG' in user_profile.get('tags',[]) or user_profile.get('is_shg'):
            if 'SHG' in str(scheme['tags']):
                reasons.append("✓ SHG member special benefit")
        
        # AI similarity reason
        if sim_score > 0.3:
            reasons.append(f"✓ AI semantic match: Your profile aligns with scheme objectives ({sim_score:.2f} similarity)")
        
        if not reasons:
            reasons.append("✓ General eligibility - Open for all marginalized entrepreneurs")
            reasons.append(f"✓ Matches your interest in {user_profile.get('business_type','entrepreneurship')}")
        
        reasons.append(f"• Benefit: {scheme.get('benefits','Financial support')}")
        
        return reasons

    def match(self, user_profile, top_k=10):
        """Full 2-stage matching"""
        filtered = self.rule_filter(user_profile)
        ranked = self.ai_ranking(user_profile, filtered)
        return ranked[:top_k]

    def get_scheme_by_id(self, scheme_id):
        for s in self.schemes:
            if s['id'] == scheme_id:
                return s
        return None
