from datetime import datetime, timedelta
from models import db, User, Category, Item, ItemImage, ClaimRequest, Notification, ActivityLog

def seed_database():
    """
    Seeds initial default data if the database is empty.
    Provides categories, admin, demo users, sample items, and claims.
    """
    # 1. Seed Categories
    default_categories = [
        {'name': 'Electronics', 'slug': 'electronics', 'icon': 'laptop', 'description': 'Laptops, smartphones, headphones, smartwatches, chargers, tablets, power banks'},
        {'name': 'Identity Cards', 'slug': 'identity-cards', 'icon': 'id-card', 'description': 'Student IDs, driver licenses, university badges, library cards, national IDs'},
        {'name': 'Books and Documents', 'slug': 'books-and-documents', 'icon': 'book', 'description': 'Textbooks, lab manuals, certificates, spiral notebooks, degree certificates, files'},
        {'name': 'Bags and Wallets', 'slug': 'bags-and-wallets', 'icon': 'briefcase', 'description': 'Backpacks, leather wallets, purses, laptop sleeves, handbags, gym duffels'},
        {'name': 'Accessories', 'slug': 'accessories', 'icon': 'watch', 'description': 'Watches, prescription glasses, sunglasses, rings, bracelets, umbrellas, jewellery'},
        {'name': 'Keys', 'slug': 'keys', 'icon': 'key', 'description': 'Hostel keys, motorcycle/car keys, locker keys, keychains with tags'},
        {'name': 'Clothing', 'slug': 'clothing', 'icon': 'shirt', 'description': 'Hoodies, varsity jackets, blazers, lab coats, caps, winter scarves'},
        {'name': 'Other', 'slug': 'other', 'icon': 'package', 'description': 'Sports equipment, water bottles, scientific calculators, musical instruments, art supplies'}
    ]
    
    for cat_data in default_categories:
        if not Category.query.filter_by(slug=cat_data['slug']).first():
            cat = Category(**cat_data)
            db.session.add(cat)
            
    db.session.commit()
    
    # 2. Seed Users
    # Admin
    admin_email = 'admin@findit.com'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            name='Campus Administrator',
            email=admin_email,
            phone='+91 80 6782 1000',
            role='admin',
            status='active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
    # Normal User (Ravi)
    user_email = 'ravi@dsu.edu.in'
    if not User.query.filter_by(email=user_email).first():
        user = User(
            name='Ravi Kumar',
            email=user_email,
            phone='+91 98765 43210',
            role='user',
            status='active'
        )
        user.set_password('user123')
        db.session.add(user)
        
    # Finder / Security Officer
    finder_email = 'security@dsu.edu.in'
    if not User.query.filter_by(email=finder_email).first():
        finder = User(
            name='Officer Suresh (Campus Security)',
            email=finder_email,
            phone='+91 99887 76655',
            role='finder',
            status='active'
        )
        finder.set_password('finder123')
        db.session.add(finder)
        
    # Student Priya
    jane_email = 'priya@dsu.edu.in'
    if not User.query.filter_by(email=jane_email).first():
        jane = User(
            name='Priya Sharma',
            email=jane_email,
            phone='+91 91234 56789',
            role='user',
            status='active'
        )
        jane.set_password('user123')
        db.session.add(jane)
        
    db.session.commit()
    
    # Check if items exist
    if Item.query.count() == 0:
        admin_u = User.query.filter_by(email=admin_email).first()
        john_u = User.query.filter_by(email=user_email).first()
        sec_u = User.query.filter_by(email=finder_email).first()
        jane_u = User.query.filter_by(email=jane_email).first()
        
        cat_elec = Category.query.filter_by(slug='electronics').first()
        cat_id = Category.query.filter_by(slug='identity-cards').first()
        cat_bag = Category.query.filter_by(slug='bags-and-wallets').first()
        cat_key = Category.query.filter_by(slug='keys').first()
        cat_book = Category.query.filter_by(slug='books-and-documents').first()
        cat_acc = Category.query.filter_by(slug='accessories').first()
        
        today = datetime.utcnow().date()
        
        sample_items = [
            # 1. Lost Laptop by Ravi
            Item(
                report_type='lost',
                item_name='Dell XPS 13 Laptop – Silver (AI&DS Lab)',
                category_id=cat_elec.id,
                description='Lost in the DSU Central Library 2nd floor near Table 14. Has a DSU sticker on lid and a blue-black protective sleeve. Runs Ubuntu 24.04.',
                location='DSU Central Library, 2nd Floor Reading Hall',
                event_date=today - timedelta(days=2),
                contact_phone='+91 98765 43210',
                contact_email='ravi@dsu.edu.in',
                primary_image='https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80',
                reward='₹500 Reward for Safe Return',
                status='open',
                user_id=john_u.id
            ),
            # 2. Found Laptop by Campus Security (Potential Smart Match!)
            Item(
                report_type='found',
                item_name='Dell Laptop Silver with DSU Sticker & Blue Sleeve',
                category_id=cat_elec.id,
                description='Turned in to Central Security Desk. Found on 2nd floor of DSU Library. Has a university sticker and Linux stickers on the lid. Secured at Security Room 101.',
                location='DSU Library Security Desk / Room 101',
                event_date=today - timedelta(days=1),
                contact_phone='+91 99887 76655',
                contact_email='security@dsu.edu.in',
                primary_image='https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?auto=format&fit=crop&w=600&q=80',
                reward=None,
                status='open',
                user_id=sec_u.id
            ),
            # 3. Lost Student ID by Priya
            Item(
                report_type='lost',
                item_name='DSU Student ID Card – Priya Sharma (AI&DS)',
                category_id=cat_id.id,
                description='DSU identity card with blue lanyard. Department of AI & Data Science. Lost near the North Canteen during lunch break around 1:00 PM.',
                location='DSU North Canteen & Food Court',
                event_date=today - timedelta(days=3),
                contact_phone='+91 91234 56789',
                contact_email='priya@dsu.edu.in',
                primary_image='https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=600&q=80',
                reward='Gratitude + Coffee treat',
                status='open',
                user_id=jane_u.id
            ),
            # 4. Found Black Leather Wallet by Security
            Item(
                report_type='found',
                item_name='Black Bifold Leather Wallet with Cards & Cash',
                category_id=cat_bag.id,
                description='Found under seat 18 in DSU Main Auditorium after the department orientation. Contains an Aadhaar card, student transit pass, and some cash (₹800).',
                location='DSU Main Auditorium, Row G',
                event_date=today - timedelta(days=4),
                contact_phone='+91 99887 76655',
                contact_email='security@dsu.edu.in',
                primary_image='https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=600&q=80',
                reward=None,
                status='open',
                user_id=sec_u.id
            ),
            # 5. Lost Honda Motorcycle Key by Ravi
            Item(
                report_type='lost',
                item_name='Honda Activa Key with Red Keychain & ID Tag',
                category_id=cat_key.id,
                description='Single Honda Activa ignition key on a red metal carabiner with a small Lord Ganesha figurine keychain. Lost in DSU Parking Zone B.',
                location='DSU Student Parking Lot – Zone B',
                event_date=today - timedelta(days=5),
                contact_phone='+91 98765 43210',
                contact_email='ravi@dsu.edu.in',
                primary_image='https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a?auto=format&fit=crop&w=600&q=80',
                reward='₹200',
                status='open',
                user_id=john_u.id
            ),
            # 6. Found Sony Headphones (Claimed example)
            Item(
                report_type='found',
                item_name='Sony WH-1000XM4 Wireless Headphones (Black)',
                category_id=cat_elec.id,
                description='Black over-ear Sony headphones left on bench in DSU Science Quad East Lawn. Includes zip case and USB-C charging cable.',
                location='DSU Science Quad – East Lawn Benches',
                event_date=today - timedelta(days=7),
                contact_phone='+91 99887 76655',
                contact_email='security@dsu.edu.in',
                primary_image='https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=600&q=80',
                reward=None,
                status='claimed',
                user_id=sec_u.id
            ),
            # 7. Lost Ray-Ban Sunglasses (Recovered)
            Item(
                report_type='lost',
                item_name='Ray-Ban Wayfarer Classic Sunglasses – Matte Black',
                category_id=cat_acc.id,
                description='Classic matte black Ray-Ban Wayfarer sunglasses in brown leather case. Lost around DSU Gym entrance / Locker area after evening sports session.',
                location='DSU Gymnasium Entrance & Locker Room',
                event_date=today - timedelta(days=10),
                contact_phone='+91 91234 56789',
                contact_email='priya@dsu.edu.in',
                primary_image='https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=600&q=80',
                reward=None,
                status='recovered',
                user_id=jane_u.id
            ),
            # 8. Found NPTEL Book
            Item(
                report_type='found',
                item_name='Machine Learning – NPTEL Study Material & Notes',
                category_id=cat_book.id,
                description='A thick spiral-bound NPTEL Machine Learning notes with handwritten annotations inside chapters 5–9. Found in DSU Mathematics Building Room 204.',
                location='DSU Mathematics Building, Room 204',
                event_date=today - timedelta(days=1),
                contact_phone='+91 99887 76655',
                contact_email='security@dsu.edu.in',
                primary_image='https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80',
                reward=None,
                status='open',
                user_id=sec_u.id
            )
        ]
        
        for it in sample_items:
            db.session.add(it)
            
        db.session.commit()
        
        # Add sample claim request on the headphones
        hp_item = Item.query.filter_by(item_name='Sony WH-1000XM4 Wireless Headphones (Black)').first()
        if hp_item:
            claim = ClaimRequest(
                item_id=hp_item.id,
                claimant_id=john_u.id,
                proof_details='Serial number on left headband ends with 8841. My phone Bluetooth name is "John\'s XM4". The custom EQ preset in Sony Headphones app is Bass Boosted.',
                claimant_phone='+91 98765 43210',
                claimant_email='ravi@dsu.edu.in',
                status='approved',
                admin_notes='Claim verified by Officer Suresh. Bluetooth device name and serial number matched in person at Security Room 101.',
                reviewed_by=sec_u.id,
                reviewed_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(claim)
            
        # Add initial notifications for users
        notif1 = Notification(
            user_id=john_u.id,
            title='🎉 Claim Approved for Sony Headphones',
            message='Your claim for the Sony WH-1000XM4 has been approved by Campus Security. Please bring your student ID to Room 101 to collect.',
            type='claim',
            link='/my-claims'
        )
        notif2 = Notification(
            user_id=john_u.id,
            title='Potential Smart Match Detected!',
            message='We detected a Dell Laptop with DSU sticker turned in at DSU Library Security Desk that matches your lost report!',
            type='match',
            link='/items/2'
        )
        db.session.add(notif1)
        db.session.add(notif2)
        
        # Initial activity logs
        log1 = ActivityLog(
            user_id=admin_u.id,
            action='SYSTEM_BOOT',
            details='FindIt Platform database initialized and seeded with demo data',
            ip_address='127.0.0.1'
        )
        db.session.add(log1)
        db.session.commit()
        print("[FindIt Backend] Initial database seeding completed successfully.")
