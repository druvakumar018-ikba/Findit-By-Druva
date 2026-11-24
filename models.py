from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(25), nullable=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True, index=True)
    phone_verified_at = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user', 'admin', 'finder'
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'suspended'
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('Item', backref='reporter', lazy=True, cascade='all, delete-orphan')
    claims = db.relationship('ClaimRequest', backref='claimant', lazy=True, foreign_keys='ClaimRequest.claimant_id', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return bool(self.password_hash and check_password_hash(self.password_hash, password))
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'phone_verified': self.phone_verified_at is not None,
            'role': self.role,
            'status': self.status,
            'avatar': self.avatar,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'items_count': len(self.items) if self.items else 0
        }


class RevokedToken(db.Model):
    __tablename__ = 'revoked_tokens'

    token_id = db.Column(db.String(36), primary_key=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    icon = db.Column(db.String(50), nullable=False, default='tag')
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('Item', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'icon': self.icon,
            'description': self.description,
            'items_count': len(self.items) if self.items else 0
        }


class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(10), nullable=False, index=True)  # 'lost' or 'found'
    item_name = db.Column(db.String(150), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False, index=True)
    event_date = db.Column(db.Date, nullable=False)
    contact_phone = db.Column(db.String(50), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    primary_image = db.Column(db.String(255), nullable=True)
    reward = db.Column(db.String(50), nullable=True)
    reporter_name = db.Column(db.String(100), nullable=False, default='Anonymous')
    usn = db.Column(db.String(50), nullable=False, default='')
    department = db.Column(db.String(100), nullable=False, default='')
    status = db.Column(db.String(20), nullable=False, default='open')  # 'open', 'pending_claim', 'claimed', 'recovered', 'rejected'
    is_suspicious = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('ItemImage', backref='item', lazy=True, cascade='all, delete-orphan')
    claims = db.relationship('ClaimRequest', backref='item', lazy=True, foreign_keys='ClaimRequest.item_id', cascade='all, delete-orphan')
    
    def to_dict(self, safe_mode=False, current_user_id=None, is_admin=False):
        """
        safe_mode: when True, masks sensitive direct phone/email contact
        unless the viewer is the author of this item or an admin.
        """
        is_owner = (current_user_id is not None and self.user_id == current_user_id)
        show_contact = is_admin or is_owner or (not safe_mode and self.report_type == 'lost')
        
        return {
            'id': self.id,
            'report_id': f"FID-{self.id:05d}",
            'report_type': self.report_type,
            'item_name': self.item_name,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Other',
            'category_icon': self.category.icon if self.category else 'tag',
            'description': self.description,
            'location': self.location,
            'event_date': self.event_date.strftime('%Y-%m-%d') if self.event_date else None,
            'contact_phone': self.contact_phone if show_contact else 'Protected (Submit Claim to Contact)',
            'contact_email': self.contact_email if show_contact else 'Protected (Submit Claim to Contact)',
            'primary_image': self.primary_image,
            'images': [img.to_dict() for img in self.images] if self.images else [],
            'reward': self.reward,
            'reporter_name': self.reporter_name or (self.reporter.name if self.reporter else 'Anonymous'),
            'usn': self.usn or '',
            'department': self.department or '',
            'status': self.status,
            'is_suspicious': self.is_suspicious,
            'user_id': self.user_id,
            'reporter_name': self.reporter.name if self.reporter else 'Anonymous',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'claims_count': len(self.claims) if self.claims else 0
        }


class ItemImage(db.Model):
    __tablename__ = 'item_images'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'image_url': self.image_url,
            'is_primary': self.is_primary
        }


class ClaimRequest(db.Model):
    __tablename__ = 'claim_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    proof_details = db.Column(db.Text, nullable=False)
    claimant_phone = db.Column(db.String(30), nullable=False)
    claimant_email = db.Column(db.String(120), nullable=False)
    proof_document_image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    admin_notes = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'claim_id': f"CLM-{self.id:04d}",
            'item_id': self.item_id,
            'item_name': self.item.item_name if self.item else 'Unknown Item',
            'item_report_type': self.item.report_type if self.item else None,
            'item_primary_image': self.item.primary_image if self.item else None,
            'item_location': self.item.location if self.item else None,
            'item_reporter_id': self.item.user_id if self.item else None,
            'item_reporter_name': self.item.reporter.name if self.item and self.item.reporter else None,
            'claimant_id': self.claimant_id,
            'claimant_name': self.claimant.name if self.claimant else 'Unknown Claimant',
            'proof_details': self.proof_details,
            'claimant_phone': self.claimant_phone,
            'claimant_email': self.claimant_email,
            'proof_document_image': self.proof_document_image,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'reviewed_by_name': self.reviewer.name if self.reviewer else None,
            'reviewed_at': self.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if self.reviewed_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # 'claim', 'match', 'status', 'system'
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'System / Guest',
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='new')  # 'new', 'resolved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
