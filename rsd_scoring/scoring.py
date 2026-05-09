from models import db, User, Evidence

def calculate_user_score(user_id):
    """Tính tổng điểm của user từ các evidence đã được duyệt"""
    evidences = Evidence.query.filter_by(user_id=user_id, status='approved').all()
    total_score = sum(e.points_awarded for e in evidences)
    return total_score

def update_user_score(user_id):
    """Cập nhật điểm cho user"""
    user = User.query.get(user_id)
    if user:
        user.score = calculate_user_score(user_id)
        db.session.commit()
    return user.score

def get_leaderboard():
    """Lấy bảng xếp hạng theo điểm"""
    users = User.query.order_by(User.score.desc()).all()
    return users

def approve_evidence(evidence_id, points, reviewer_id):
    """Duyệt minh chứng và cộng điểm"""
    evidence = Evidence.query.get(evidence_id)
    if evidence and evidence.status == 'pending':
        evidence.status = 'approved'
        evidence.points_awarded = points
        evidence.reviewed_by = reviewer_id
        
        # Cập nhật điểm cho user
        update_user_score(evidence.user_id)
        
        db.session.commit()
        return True
    return False

def reject_evidence(evidence_id, reviewer_id):
    """Từ chối minh chứng"""
    evidence = Evidence.query.get(evidence_id)
    if evidence and evidence.status == 'pending':
        evidence.status = 'rejected'
        evidence.reviewed_by = reviewer_id
        db.session.commit()
        return True
    return False
