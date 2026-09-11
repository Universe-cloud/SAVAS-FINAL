
"""
SASVA Feedback and Self-Learning Loop
As per PPT: No Feedback Loop -> Self-Learning Feedback Loop | Connect • Apply • Succeed
No Handholding after Apply -> Success Tracking | Learn • Apply • Advance • Develop
"""
import json
from pathlib import Path
from datetime import datetime

FEEDBACK_FILE = Path("data/feedback.json")
SUCCESS_FILE = Path("data/success_tracking.json")

def save_feedback(user_id, scheme_id, rating, comment, applied=False, success=False):
    """Save feedback for self-learning"""
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    feedbacks = []
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
        except:
            feedbacks = []
    
    entry = {
        "user_id": user_id,
        "scheme_id": scheme_id,
        "rating": rating,
        "comment": comment,
        "applied": applied,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    feedbacks.append(entry)
    
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(feedbacks, f, indent=2, ensure_ascii=False)
    
    # Also update success tracking
    if applied or success:
        save_success_tracking(user_id, scheme_id, applied, success)
    
    return True

def save_success_tracking(user_id, scheme_id, applied, success):
    SUCCESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tracking = []
    if SUCCESS_FILE.exists():
        try:
            with open(SUCCESS_FILE, 'r', encoding='utf-8') as f:
                tracking = json.load(f)
        except:
            tracking = []
    
    tracking.append({
        "user_id": user_id,
        "scheme_id": scheme_id,
        "applied": applied,
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "stage": "Success" if success else "Applied" if applied else "Interested"
    })
    
    with open(SUCCESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracking, f, indent=2, ensure_ascii=False)

def get_feedback_stats():
    """For self-learning loop analysis"""
    if not FEEDBACK_FILE.exists():
        return {"total": 0, "avg_rating": 0, "success_rate": 0}
    
    try:
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            feedbacks = json.load(f)
        
        total = len(feedbacks)
        avg_rating = sum([x.get('rating',0) for x in feedbacks]) / total if total else 0
        applied = len([x for x in feedbacks if x.get('applied')])
        success = len([x for x in feedbacks if x.get('success')])
        success_rate = (success / applied * 100) if applied else 0
        
        return {
            "total": total,
            "avg_rating": round(avg_rating, 2),
            "applied": applied,
            "success": success,
            "success_rate": round(success_rate, 1),
            "recent": feedbacks[-5:] if feedbacks else []
        }
    except:
        return {"total": 0, "avg_rating": 0, "success_rate": 0}

def get_success_journey(user_id):
    """Learn • Apply • Advance • Develop"""
    if not SUCCESS_FILE.exists():
        return []
    try:
        with open(SUCCESS_FILE, 'r', encoding='utf-8') as f:
            tracking = json.load(f)
        return [t for t in tracking if t.get('user_id') == user_id]
    except:
        return []
