from flask import Blueprint, request, jsonify
from models import db, ContactMessage
import re

contact_bp = Blueprint('contact', __name__, url_prefix='/api/contact')

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

@contact_bp.route('', methods=['POST'])
def send_contact_message():
    data = request.get_json() or {}
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    
    if not name or len(name) < 2:
        return jsonify({'success': False, 'message': 'Please provide your full name.'}), 400
        
    if not email or not re.match(EMAIL_REGEX, email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400
        
    if not subject or len(subject) < 3:
        return jsonify({'success': False, 'message': 'Please specify a subject for your message.'}), 400
        
    if not message or len(message) < 10:
        return jsonify({'success': False, 'message': 'Message must be at least 10 characters long.'}), 400
        
    contact_msg = ContactMessage(
        name=name,
        email=email,
        subject=subject,
        message=message,
        status='new'
    )
    db.session.add(contact_msg)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Thank you! Your inquiry has been transmitted to the FindIt Help Desk team. We will respond via email shortly.',
        'contact': contact_msg.to_dict()
    }), 201


@contact_bp.route('/messages', methods=['GET'])
def get_contact_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(50).all()
    return jsonify({
        'success': True,
        'messages': [m.to_dict() for m in messages]
    }), 200
