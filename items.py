from flask import Blueprint, request, jsonify, g
from datetime import datetime
import re
from models import db, User, Item, ItemImage, Category, ActivityLog, Notification, ClaimRequest
from utils.auth_middleware import token_required, optional_token, admin_required
from utils.file_upload import save_image
from utils.matcher import find_matches_for_item
from sqlalchemy import or_

items_bp = Blueprint('items', __name__, url_prefix='/api/items')

@items_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify({
        'success': True,
        'categories': [cat.to_dict() for cat in categories]
    }), 200


@items_bp.route('', methods=['GET'])
@optional_token
def get_items():
    """
    Search, filter, and paginate items.
    Query params:
      - type: 'lost', 'found', or 'all'
      - category_id or category (slug)
      - status: 'open', 'claimed', 'recovered', 'all'
      - q: search query for title, description, location
      - location: location search
      - start_date, end_date
      - sort: 'newest', 'oldest', 'date_asc', 'date_desc'
      - page: int
      - per_page: int
    """
    query = Item.query
    
    # Filter by report type
    report_type = request.args.get('type')
    if report_type and report_type in ['lost', 'found']:
        query = query.filter(Item.report_type == report_type)
        
    # Filter by category
    category_id = request.args.get('category_id')
    category_slug = request.args.get('category')
    if category_id:
        query = query.filter(Item.category_id == int(category_id))
    elif category_slug and category_slug != 'all':
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter(Item.category_id == cat.id)
            
    # Filter by status
    status = request.args.get('status')
    if status and status != 'all':
        query = query.filter(Item.status == status)
    else:
        # By default exclude rejected
        query = query.filter(Item.status != 'rejected')
        
    # Search query
    q = request.args.get('q', '').strip()
    if q:
        search_filter = or_(
            Item.item_name.ilike(f"%{q}%"),
            Item.description.ilike(f"%{q}%"),
            Item.location.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
        
    # Location filter
    location = request.args.get('location', '').strip()
    if location:
        query = query.filter(Item.location.ilike(f"%{location}%"))
        
    # Date filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Item.event_date >= s_date)
        except ValueError:
            pass
    if end_date:
        try:
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Item.event_date <= e_date)
        except ValueError:
            pass
            
    # Suspicious flag check for non-admins
    current_user = getattr(g, 'current_user', None)
    is_admin = current_user and current_user.role == 'admin'
    if not is_admin:
        query = query.filter(Item.is_suspicious == False)
        
    # Sorting
    sort = request.args.get('sort', 'newest')
    if sort == 'oldest':
        query = query.order_by(Item.created_at.asc())
    elif sort == 'date_asc':
        query = query.order_by(Item.event_date.asc())
    elif sort == 'date_desc':
        query = query.order_by(Item.event_date.desc())
    else:
        query = query.order_by(Item.created_at.desc())
        
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 12))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    current_user_id = current_user.id if current_user else None
    items_data = [item.to_dict(safe_mode=True, current_user_id=current_user_id, is_admin=is_admin) for item in pagination.items]
    
    return jsonify({
        'success': True,
        'items': items_data,
        'pagination': {
            'total': pagination.total,
            'pages': pagination.pages,
            'page': page,
            'per_page': per_page,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    }), 200


@items_bp.route('/<int:item_id>', methods=['GET'])
@optional_token
def get_item_details(item_id):
    item = Item.query.get_or_404(item_id)
    current_user = getattr(g, 'current_user', None)
    is_admin = current_user and current_user.role == 'admin'
    current_user_id = current_user.id if current_user else None
    
    # Fetch potential smart matches for this item
    opposite_type = 'found' if item.report_type == 'lost' else 'lost'
    candidates = Item.query.filter(
        Item.report_type == opposite_type,
        Item.status.in_(['open', 'pending_claim']),
        Item.is_suspicious == False
    ).all()
    
    smart_matches = find_matches_for_item(item, candidates, threshold=35.0)[:5]
    
    return jsonify({
        'success': True,
        'item': item.to_dict(safe_mode=True, current_user_id=current_user_id, is_admin=is_admin),
        'smart_matches': smart_matches
    }), 200


@items_bp.route('/upload-image', methods=['POST'])
@token_required
def upload_item_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file provided in upload.'}), 400
        
    file = request.files['image']
    try:
        image_url = save_image(file, subfolder='items')
        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully.',
            'image_url': image_url
        }), 200
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@items_bp.route('', methods=['POST'])
def report_item():
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    
    report_type = data.get('report_type', '').strip().lower()
    item_name = data.get('item_name', '').strip()
    category_id = data.get('category_id')
    description = data.get('description', '').strip()
    location = data.get('location', '').strip()
    event_date_str = data.get('event_date', '').strip()
    contact_phone = data.get('contact_phone', '')
    contact_phone = contact_phone.strip() if isinstance(contact_phone, str) else ''
    submitted_email = data.get('contact_email', '')
    contact_email = submitted_email.strip() if isinstance(submitted_email, str) else ''
    reward = data.get('reward', '').strip()
    reporter_name = data.get('reporter_name', '').strip()
    usn = data.get('usn', '').strip()
    department = data.get('department', '').strip()
    
    # Validations
    if report_type not in ['lost', 'found']:
        return jsonify({'success': False, 'message': "Report type must be either 'lost' or 'found'."}), 400
        
    if not item_name or len(item_name) < 2:
        return jsonify({'success': False, 'message': 'Item name is required and must be at least 2 characters.'}), 400

    if not reporter_name:
        return jsonify({'success': False, 'message': 'Reporter name is required.'}), 400

    if not usn:
        return jsonify({'success': False, 'message': 'USN is required.'}), 400

    if not department:
        return jsonify({'success': False, 'message': 'Department is required.'}), 400
        
    if not category_id:
        return jsonify({'success': False, 'message': 'Category is required.'}), 400
        
    category = Category.query.get(int(category_id))
    if not category:
        return jsonify({'success': False, 'message': 'Selected category does not exist.'}), 400
        
    if not description or len(description) < 10:
        return jsonify({'success': False, 'message': 'Description is required and must be at least 10 characters with helpful identifying details.'}), 400
        
    if not location:
        return jsonify({'success': False, 'message': 'Location is required (e.g., Library 2nd Floor, Main Cafeteria, Science Block Room 102).'}), 400
        
    if not event_date_str:
        return jsonify({'success': False, 'message': 'Date of incident is required.'}), 400

    if contact_phone:
        phone_digits = re.sub(r'\D', '', contact_phone)
        if not 7 <= len(phone_digits) <= 15:
            return jsonify({'success': False, 'message': 'Enter a valid contact phone number.'}), 400
        
    try:
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        
    # Process primary image file if provided in multipart
    primary_image_url = data.get('primary_image')
    if 'image' in request.files:
        try:
            uploaded_url = save_image(request.files['image'], subfolder='items')
            if uploaded_url:
                primary_image_url = uploaded_url
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
            
    # For found items, image is strongly recommended
    reporting_user = User.query.filter_by(role='admin').first()
    item = Item(
        report_type=report_type,
        item_name=item_name,
        category_id=category.id,
        description=description,
        location=location,
        event_date=event_date,
        contact_phone=contact_phone,
        contact_email=contact_email,
        primary_image=primary_image_url,
        reward=reward if report_type == 'lost' else None,
        reporter_name=reporter_name,
        usn=usn,
        department=department,
        status='open',
        user_id=reporting_user.id if reporting_user else None
    )
    
    db.session.add(item)
    db.session.flush()
    
    # If image URL exists, save in item_images table as primary
    if primary_image_url:
        img_record = ItemImage(
            item_id=item.id,
            image_url=primary_image_url,
            is_primary=True
        )
        db.session.add(img_record)
        
    # Log activity
    log = ActivityLog(
        user_id=None,
        action=f"REPORT_{report_type.upper()}_ITEM",
        details=f"{reporter_name} ({usn}, {department}) reported {report_type} item: {item.item_name} (ID: FID-{item.id:05d})",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    # Check for smart matches immediately and notify if high confidence match found!
    opposite_type = 'found' if report_type == 'lost' else 'lost'
    potential_matches = Item.query.filter(
        Item.report_type == opposite_type,
        Item.category_id == item.category_id,
        Item.status == 'open'
    ).all()
    
    high_matches = find_matches_for_item(item, potential_matches, threshold=50.0)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"Your {report_type} item report has been published successfully!",
        'item': item.to_dict(safe_mode=False),
        'potential_matches_found': len(high_matches)
    }), 201


@items_bp.route('/<int:item_id>', methods=['PUT'])
@token_required
def update_item(item_id):
    user = g.current_user
    item = Item.query.get_or_404(item_id)
    
    is_admin = (user.role == 'admin')
    if item.user_id != user.id and not is_admin:
        return jsonify({'success': False, 'message': 'You are not authorized to edit this report.'}), 403
        
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    
    if 'item_name' in data and data['item_name'].strip():
        item.item_name = data['item_name'].strip()
    if 'category_id' in data and data['category_id']:
        item.category_id = int(data['category_id'])
    if 'description' in data and data['description'].strip():
        item.description = data['description'].strip()
    if 'location' in data and data['location'].strip():
        item.location = data['location'].strip()
    if 'event_date' in data and data['event_date'].strip():
        try:
            item.event_date = datetime.strptime(data['event_date'].strip(), '%Y-%m-%d').date()
        except ValueError:
            pass
    if 'reward' in data:
        item.reward = data['reward'].strip()
    if 'contact_phone' in data:
        item.contact_phone = data['contact_phone'].strip()
    if 'contact_email' in data:
        item.contact_email = data['contact_email'].strip()
    if 'status' in data and data['status'] in ['open', 'pending_claim', 'claimed', 'recovered', 'rejected']:
        item.status = data['status']
        
    if 'image' in request.files:
        try:
            new_image = save_image(request.files['image'], subfolder='items')
            if new_image:
                item.primary_image = new_image
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
            
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Item report updated successfully.',
        'item': item.to_dict(safe_mode=False, current_user_id=user.id, is_admin=is_admin)
    }), 200


@items_bp.route('/<int:item_id>', methods=['DELETE'])
@token_required
def delete_item(item_id):
    user = g.current_user
    item = Item.query.get_or_404(item_id)
    
    is_admin = (user.role == 'admin')
    if item.user_id != user.id and not is_admin:
        return jsonify({'success': False, 'message': 'You do not have permission to delete this listing.'}), 403
        
    item_title = item.item_name
    db.session.delete(item)
    
    log = ActivityLog(
        user_id=user.id,
        action='DELETE_ITEM',
        details=f"Deleted item '{item_title}' (ID: {item_id})",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"Item '{item_title}' has been deleted."
    }), 200


@items_bp.route('/<int:item_id>/status', methods=['PATCH'])
@token_required
def update_item_status(item_id):
    user = g.current_user
    item = Item.query.get_or_404(item_id)
    
    is_admin = (user.role == 'admin')
    if item.user_id != user.id and not is_admin:
        return jsonify({'success': False, 'message': 'Permission denied.'}), 403
        
    data = request.get_json() or {}
    new_status = data.get('status')
    
    valid_statuses = ['open', 'pending_claim', 'claimed', 'recovered', 'rejected']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': f"Invalid status. Choose from {valid_statuses}."}), 400
        
    item.status = new_status
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f"Item status changed to {new_status}.",
        'item': item.to_dict(safe_mode=False, current_user_id=user.id, is_admin=is_admin)
    }), 200


@items_bp.route('/<int:item_id>/matches', methods=['GET'])
@optional_token
def get_smart_matches(item_id):
    item = Item.query.get_or_404(item_id)
    opposite_type = 'found' if item.report_type == 'lost' else 'lost'
    candidates = Item.query.filter(
        Item.report_type == opposite_type,
        Item.status.in_(['open', 'pending_claim']),
        Item.is_suspicious == False
    ).all()
    
    matches = find_matches_for_item(item, candidates, threshold=25.0)
    return jsonify({
        'success': True,
        'item_id': item.id,
        'item_name': item.item_name,
        'matches': matches
    }), 200


@items_bp.route('/my-items', methods=['GET'])
@token_required
def get_my_items():
    user = g.current_user
    report_type = request.args.get('type')  # 'lost', 'found', or None
    
    query = Item.query.filter_by(user_id=user.id)
    if report_type in ['lost', 'found']:
        query = query.filter_by(report_type=report_type)
        
    items = query.order_by(Item.created_at.desc()).all()
    return jsonify({
        'success': True,
        'items': [item.to_dict(safe_mode=False, current_user_id=user.id) for item in items]
    }), 200


@items_bp.route('/search-match', methods=['POST'])
def dynamic_search_match():
    """
    Takes an ad-hoc lost or found item criteria and returns smart matches against the database.
    Useful for the Search page's Smart Match tool.
    """
    data = request.get_json() or {}
    report_type = data.get('report_type', 'lost')
    category_id = data.get('category_id')
    title = data.get('title', '')
    description = data.get('description', '')
    location = data.get('location', '')
    
    opposite_type = 'found' if report_type == 'lost' else 'lost'
    
    # Create a transient Item for comparison
    mock_item = Item(
        id=0,
        report_type=report_type,
        item_name=title,
        category_id=int(category_id) if category_id else 0,
        description=description,
        location=location,
        event_date=datetime.utcnow().date()
    )
    
    query = Item.query.filter(
        Item.report_type == opposite_type,
        Item.status.in_(['open', 'pending_claim']),
        Item.is_suspicious == False
    )
    if category_id:
        query = query.filter(Item.category_id == int(category_id))
        
    candidates = query.all()
    matches = find_matches_for_item(mock_item, candidates, threshold=20.0)
    
    return jsonify({
        'success': True,
        'matches': matches
    }), 200
