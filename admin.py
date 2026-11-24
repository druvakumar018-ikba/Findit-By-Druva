from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from models import db, User, Item, ClaimRequest, Category, ActivityLog, Notification
from utils.auth_middleware import admin_required
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    """
    Returns platform key performance indicators and analytics for dashboard
    """
    total_users = User.query.count()
    total_lost = Item.query.filter_by(report_type='lost').count()
    total_found = Item.query.filter_by(report_type='found').count()
    total_items = total_lost + total_found
    
    pending_claims = ClaimRequest.query.filter_by(status='pending').count()
    approved_claims = ClaimRequest.query.filter_by(status='approved').count()
    rejected_claims = ClaimRequest.query.filter_by(status='rejected').count()
    
    recovered_items = Item.query.filter(Item.status.in_(['claimed', 'recovered'])).count()
    recovery_rate = round((recovered_items / total_items * 100), 1) if total_items > 0 else 0
    
    suspicious_items = Item.query.filter_by(is_suspicious=True).count()
    
    # 1. Lost vs Found Breakdown
    lost_found_chart = {
        'labels': ['Lost Items', 'Found Items'],
        'data': [total_lost, total_found]
    }
    
    # 2. Categories Distribution
    categories = Category.query.all()
    cat_labels = []
    cat_counts = []
    for c in categories:
        count = Item.query.filter_by(category_id=c.id).count()
        cat_labels.append(c.name)
        cat_counts.append(count)
        
    category_chart = {
        'labels': cat_labels,
        'data': cat_counts
    }
    
    # 3. Monthly Reports (Last 6 Months)
    # Generate past 6 months dynamically
    monthly_labels = []
    monthly_lost = []
    monthly_found = []
    
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        # Calculate month
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        m_start = datetime(year, month, 1)
        if month == 12:
            m_end = datetime(year + 1, 1, 1)
        else:
            m_end = datetime(year, month + 1, 1)
            
        m_name = m_start.strftime('%b %Y')
        monthly_labels.append(m_name)
        
        lost_c = Item.query.filter(
            Item.report_type == 'lost',
            Item.created_at >= m_start,
            Item.created_at < m_end
        ).count()
        
        found_c = Item.query.filter(
            Item.report_type == 'found',
            Item.created_at >= m_start,
            Item.created_at < m_end
        ).count()
        
        monthly_lost.append(lost_c)
        monthly_found.append(found_c)
        
    monthly_chart = {
        'labels': monthly_labels,
        'lost': monthly_lost,
        'found': monthly_found
    }
    
    # 4. Status Distribution
    status_counts = {
        'Open': Item.query.filter_by(status='open').count(),
        'Pending Claim': Item.query.filter_by(status='pending_claim').count(),
        'Claimed': Item.query.filter_by(status='claimed').count(),
        'Recovered': Item.query.filter_by(status='recovered').count()
    }
    status_chart = {
        'labels': list(status_counts.keys()),
        'data': list(status_counts.values())
    }
    
    # Recent Activity
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    
    return jsonify({
        'success': True,
        'metrics': {
            'total_users': total_users,
            'total_lost': total_lost,
            'total_found': total_found,
            'total_items': total_items,
            'pending_claims': pending_claims,
            'approved_claims': approved_claims,
            'rejected_claims': rejected_claims,
            'recovered_items': recovered_items,
            'recovery_rate': recovery_rate,
            'suspicious_items': suspicious_items
        },
        'charts': {
            'lost_found': lost_found_chart,
            'categories': category_chart,
            'monthly': monthly_chart,
            'status': status_chart
        },
        'recent_activity': [l.to_dict() for l in recent_logs]
    }), 200


# --- USER MANAGEMENT ---
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        'success': True,
        'users': [u.to_dict() for u in users]
    }), 200


@admin_bp.route('/users/<int:user_id>/status', methods=['PATCH'])
@admin_required
def toggle_user_status(user_id):
    admin_user = g.current_user
    user = User.query.get_or_404(user_id)
    
    if user.id == admin_user.id:
        return jsonify({'success': False, 'message': 'You cannot suspend your own admin account.'}), 400
        
    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ['active', 'suspended']:
        return jsonify({'success': False, 'message': "Status must be 'active' or 'suspended'."}), 400
        
    user.status = new_status
    
    log = ActivityLog(
        user_id=admin_user.id,
        action='ADMIN_TOGGLE_USER_STATUS',
        details=f"Admin {admin_user.name} changed user {user.email} status to {new_status}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"User account has been set to {new_status}.",
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<int:user_id>/role', methods=['PATCH'])
@admin_required
def change_user_role(user_id):
    admin_user = g.current_user
    user = User.query.get_or_404(user_id)
    
    if user.id == admin_user.id:
        return jsonify({'success': False, 'message': 'You cannot demote yourself from admin role.'}), 400
        
    data = request.get_json() or {}
    new_role = data.get('role')
    if new_role not in ['user', 'finder', 'admin']:
        return jsonify({'success': False, 'message': "Role must be 'user', 'finder', or 'admin'."}), 400
        
    user.role = new_role
    
    log = ActivityLog(
        user_id=admin_user.id,
        action='ADMIN_CHANGE_USER_ROLE',
        details=f"Admin {admin_user.name} changed {user.email} role to {new_role}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"User role changed to {new_role}.",
        'user': user.to_dict()
    }), 200


# --- ITEM MANAGEMENT ---
@admin_bp.route('/items', methods=['GET'])
@admin_required
def get_all_items_admin():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return jsonify({
        'success': True,
        'items': [item.to_dict(safe_mode=False, is_admin=True) for item in items]
    }), 200


@admin_bp.route('/items/<int:item_id>/suspicious', methods=['PATCH'])
@admin_required
def toggle_item_suspicious(item_id):
    admin_user = g.current_user
    item = Item.query.get_or_404(item_id)
    
    data = request.get_json() or {}
    is_suspicious = data.get('is_suspicious', not item.is_suspicious)
    item.is_suspicious = bool(is_suspicious)
    
    log = ActivityLog(
        user_id=admin_user.id,
        action='ADMIN_TOGGLE_SUSPICIOUS',
        details=f"Admin flagged item '{item.item_name}' (ID: {item.id}) as suspicious: {item.is_suspicious}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"Item flagged as suspicious: {item.is_suspicious}.",
        'item': item.to_dict(safe_mode=False, is_admin=True)
    }), 200


# --- CLAIM MANAGEMENT ---
@admin_bp.route('/claims', methods=['GET'])
@admin_required
def get_all_claims():
    status = request.args.get('status')
    query = ClaimRequest.query
    if status and status != 'all':
        query = query.filter_by(status=status)
        
    claims = query.order_by(ClaimRequest.created_at.desc()).all()
    return jsonify({
        'success': True,
        'claims': [c.to_dict() for c in claims]
    }), 200


# --- SYSTEM LOGS ---
@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_system_logs():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'logs': [l.to_dict() for l in logs]
    }), 200
