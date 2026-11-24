from flask import Blueprint, request, jsonify, g
from models import db, Notification
from utils.auth_middleware import token_required

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('', methods=['GET'])
@token_required
def get_user_notifications():
    user = g.current_user
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(30).all()
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    
    return jsonify({
        'success': True,
        'unread_count': unread_count,
        'notifications': [n.to_dict() for n in notifications]
    }), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PATCH'])
@token_required
def mark_notification_read(notification_id):
    user = g.current_user
    notif = Notification.query.filter_by(id=notification_id, user_id=user.id).first_or_404()
    
    notif.is_read = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Notification marked as read.'
    }), 200


@notifications_bp.route('/mark-all-read', methods=['PATCH'])
@token_required
def mark_all_read():
    user = g.current_user
    Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'All notifications marked as read.'
    }), 200
