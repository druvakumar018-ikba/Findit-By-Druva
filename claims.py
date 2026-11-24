from flask import Blueprint, request, jsonify, g
from datetime import datetime
from models import db, ClaimRequest, Item, Notification, ActivityLog
from utils.auth_middleware import token_required
from utils.file_upload import save_image

claims_bp = Blueprint('claims', __name__, url_prefix='/api/claims')

@claims_bp.route('', methods=['POST'])
@token_required
def submit_claim():
    user = g.current_user
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    
    item_id = data.get('item_id')
    proof_details = data.get('proof_details', '').strip()
    claimant_phone = data.get('claimant_phone', '').strip() or user.phone
    claimant_email = data.get('claimant_email', '').strip() or user.email or ''
    
    if not item_id:
        return jsonify({'success': False, 'message': 'Target item ID is required.'}), 400
        
    item = Item.query.get(int(item_id))
    if not item:
        return jsonify({'success': False, 'message': 'The item you are claiming does not exist.'}), 404
        
    if item.user_id == user.id:
        return jsonify({'success': False, 'message': 'You cannot submit a claim for an item you reported yourself.'}), 400
        
    if not proof_details or len(proof_details) < 15:
        return jsonify({
            'success': False,
            'message': 'Please provide comprehensive proof of ownership (e.g. specific markings, serial numbers, unique scratches, purchase invoices, lock screen details, contents inside).'
        }), 400
        
    if not claimant_phone:
        return jsonify({'success': False, 'message': 'Contact phone number is required for verification.'}), 400
        
    # Check if this user already submitted a pending claim for this item
    existing = ClaimRequest.query.filter_by(item_id=item.id, claimant_id=user.id, status='pending').first()
    if existing:
        return jsonify({'success': False, 'message': 'You already have a pending claim submitted for this item.'}), 409
        
    # Handle proof document upload if attached
    proof_doc_url = data.get('proof_document_image')
    if 'proof_image' in request.files:
        try:
            uploaded_doc = save_image(request.files['proof_image'], subfolder='claims')
            if uploaded_doc:
                proof_doc_url = uploaded_doc
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
            
    claim = ClaimRequest(
        item_id=item.id,
        claimant_id=user.id,
        proof_details=proof_details,
        claimant_phone=claimant_phone,
        claimant_email=claimant_email,
        proof_document_image=proof_doc_url,
        status='pending'
    )
    
    db.session.add(claim)
    
    # Update item status to pending_claim if it was open
    if item.status == 'open':
        item.status = 'pending_claim'
        
    # Notify item reporter that a claim has been received
    notif_reporter = Notification(
        user_id=item.user_id,
        title='New Claim Request Received',
        message=f"Someone submitted an ownership claim request for your reported item '{item.item_name}'.",
        type='claim',
        link=f"/my-reports"
    )
    db.session.add(notif_reporter)
    
    # Notify claimant
    notif_claimant = Notification(
        user_id=user.id,
        title='Claim Request Submitted',
        message=f"Your claim for '{item.item_name}' (ID: FID-{item.id:05d}) has been submitted. The finder and admin team will review your evidence.",
        type='claim',
        link="/my-claims"
    )
    db.session.add(notif_claimant)
    
    # Activity log
    log = ActivityLog(
        user_id=user.id,
        action='SUBMIT_CLAIM',
        details=f"Submitted claim for item {item.item_name} (ID: {item.id})",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Your claim request has been submitted successfully for verification.',
        'claim': claim.to_dict()
    }), 201


@claims_bp.route('/my-claims', methods=['GET'])
@token_required
def get_my_claims():
    user = g.current_user
    claims = ClaimRequest.query.filter_by(claimant_id=user.id).order_by(ClaimRequest.created_at.desc()).all()
    return jsonify({
        'success': True,
        'claims': [claim.to_dict() for claim in claims]
    }), 200


@claims_bp.route('/item/<int:item_id>', methods=['GET'])
@token_required
def get_item_claims(item_id):
    """
    Get all claims received for an item owned by current user (or if admin)
    """
    user = g.current_user
    item = Item.query.get_or_404(item_id)
    
    is_admin = (user.role == 'admin')
    if item.user_id != user.id and not is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized to view claims for this item.'}), 403
        
    claims = ClaimRequest.query.filter_by(item_id=item.id).order_by(ClaimRequest.created_at.desc()).all()
    return jsonify({
        'success': True,
        'item': item.to_dict(safe_mode=False, current_user_id=user.id, is_admin=is_admin),
        'claims': [claim.to_dict() for claim in claims]
    }), 200


@claims_bp.route('/<int:claim_id>/review', methods=['PUT'])
@token_required
def review_claim(claim_id):
    """
    Approve or reject a claim request.
    Can be done by the item reporter or by an administrator.
    """
    user = g.current_user
    claim = ClaimRequest.query.get_or_404(claim_id)
    item = claim.item
    
    is_admin = (user.role == 'admin')
    is_reporter = (item.user_id == user.id)
    
    if not (is_admin or is_reporter):
        return jsonify({'success': False, 'message': 'You do not have authorization to review this claim.'}), 403
        
    data = request.get_json() or {}
    new_status = data.get('status')  # 'approved' or 'rejected'
    admin_notes = data.get('admin_notes', '').strip()
    
    if new_status not in ['approved', 'rejected']:
        return jsonify({'success': False, 'message': "Status must be either 'approved' or 'rejected'."}), 400
        
    claim.status = new_status
    claim.admin_notes = admin_notes
    claim.reviewed_by = user.id
    claim.reviewed_at = datetime.utcnow()
    
    if new_status == 'approved':
        # Mark item as claimed/recovered
        item.status = 'claimed'
        
        # Reject any other pending claims for this same item
        other_pending_claims = ClaimRequest.query.filter(
            ClaimRequest.item_id == item.id,
            ClaimRequest.id != claim.id,
            ClaimRequest.status == 'pending'
        ).all()
        for oc in other_pending_claims:
            oc.status = 'rejected'
            oc.admin_notes = 'Another claim was verified and approved for this item.'
            oc.reviewed_by = user.id
            oc.reviewed_at = datetime.utcnow()
            
            # Notify rejected claimant
            notif_rej = Notification(
                user_id=oc.claimant_id,
                title='Claim Request Update',
                message=f"Your claim for '{item.item_name}' was not approved as another claim was verified.",
                type='claim',
                link="/my-claims"
            )
            db.session.add(notif_rej)
            
        # Notify the approved claimant with pickup / verification details
        notif_appr = Notification(
            user_id=claim.claimant_id,
            title='🎉 Congratulations! Your Claim Has Been Approved!',
            message=f"Your claim for '{item.item_name}' (ID: FID-{item.id:05d}) was approved. Contact/Pickup details: {item.contact_phone} or visit {item.location}.",
            type='claim',
            link=f"/my-claims"
        )
        db.session.add(notif_appr)
        
    else:  # rejected
        # If no other pending claims, reset item status back to open
        remaining = ClaimRequest.query.filter(
            ClaimRequest.item_id == item.id,
            ClaimRequest.id != claim.id,
            ClaimRequest.status == 'pending'
        ).count()
        if remaining == 0 and item.status == 'pending_claim':
            item.status = 'open'
            
        # Notify the claimant
        notif_rej = Notification(
            user_id=claim.claimant_id,
            title='Claim Request Update',
            message=f"Your claim for '{item.item_name}' was rejected. Note: {admin_notes or 'Insufficient proof provided.'}",
            type='claim',
            link="/my-claims"
        )
        db.session.add(notif_rej)
        
    # Activity log
    log = ActivityLog(
        user_id=user.id,
        action=f"CLAIM_{new_status.upper()}",
        details=f"Claim #{claim.id} for item '{item.item_name}' was {new_status} by {user.name} ({user.role})",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"Claim request #{claim.id} has been {new_status}.",
        'claim': claim.to_dict()
    }), 200
