from sqlalchemy import inspect


def migrate_item_reporter_schema(engine):
    inspector = inspect(engine)
    if not inspector.has_table('items'):
        return

    columns = {column['name'] for column in inspector.get_columns('items')}
    missing = [
        name for name in ('reporter_name', 'usn', 'department')
        if name not in columns
    ]
    if not missing:
        return

    with engine.begin() as connection:
        if 'reporter_name' in missing:
            connection.exec_driver_sql(
                "ALTER TABLE items ADD COLUMN reporter_name VARCHAR(100) NOT NULL DEFAULT 'Anonymous'"
            )
        if 'usn' in missing:
            connection.exec_driver_sql(
                "ALTER TABLE items ADD COLUMN usn VARCHAR(50) NOT NULL DEFAULT ''"
            )
        if 'department' in missing:
            connection.exec_driver_sql(
                "ALTER TABLE items ADD COLUMN department VARCHAR(100) NOT NULL DEFAULT ''"
            )


def migrate_phone_auth_schema(engine):
    inspector = inspect(engine)
    if not inspector.has_table('users'):
        return

    columns = {column['name']: column for column in inspector.get_columns('users')}
    needs_migration = (
        not columns['email']['nullable']
        or not columns['password_hash']['nullable']
        or 'firebase_uid' not in columns
        or 'phone_verified_at' not in columns
    )
    if not needs_migration:
        return

    dialect = engine.dialect.name
    if dialect == 'sqlite':
        _migrate_sqlite_users(engine, columns)
    elif dialect == 'mysql':
        _migrate_mysql_users(engine, columns)
    elif dialect == 'postgresql':
        _migrate_postgresql_users(engine, columns)
    else:
        raise RuntimeError(f'Phone authentication migration is not supported for {dialect}.')


def _migrate_sqlite_users(engine, columns):
    connection = engine.raw_connection()
    cursor = connection.cursor()
    try:
        cursor.execute('PRAGMA foreign_keys=OFF')
        cursor.execute('BEGIN')
        index_statements = [
            row[0] for row in cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='users' AND sql IS NOT NULL"
            ).fetchall()
        ]
        existing_names = [name for name in ('firebase_uid', 'phone_verified_at') if name in columns]
        selected = [
            'id', 'name', 'email', 'password_hash', 'phone', 'role', 'status',
            'avatar', 'created_at', 'updated_at'
        ] + existing_names
        missing = [name for name in ('firebase_uid', 'phone_verified_at') if name not in columns]

        cursor.execute('DROP TABLE IF EXISTS users__phone_auth_new')
        cursor.execute(
            'CREATE TABLE users__phone_auth_new ('
            'id INTEGER NOT NULL PRIMARY KEY, '
            'name VARCHAR(100) NOT NULL, '
            'email VARCHAR(120), '
            'password_hash VARCHAR(255), '
            'phone VARCHAR(25), '
            'role VARCHAR(20) NOT NULL DEFAULT \'user\', '
            'status VARCHAR(20) NOT NULL DEFAULT \'active\', '
            'avatar VARCHAR(255), '
            'created_at DATETIME, '
            'updated_at DATETIME, '
            'firebase_uid VARCHAR(128), '
            'phone_verified_at DATETIME)'
        )
        source_values = [f'"{name}"' for name in selected]
        source_values.extend('NULL' for _ in missing)
        cursor.execute(
            'INSERT INTO users__phone_auth_new '
            '(id, name, email, password_hash, phone, role, status, avatar, created_at, updated_at, firebase_uid, phone_verified_at) '
            f'SELECT {", ".join(source_values)} FROM users'
        )
        cursor.execute('DROP TABLE users')
        cursor.execute('ALTER TABLE users__phone_auth_new RENAME TO users')
        for statement in index_statements:
            cursor.execute(statement)
        firebase_index = any('firebase_uid' in statement for statement in index_statements)
        if not firebase_index:
            cursor.execute('CREATE UNIQUE INDEX ix_users_firebase_uid ON users (firebase_uid)')
        violations = cursor.execute('PRAGMA foreign_key_check').fetchall()
        if violations:
            raise RuntimeError('Phone authentication migration found invalid foreign-key references.')
        connection.commit()
        cursor.execute('PRAGMA foreign_keys=ON')
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def _migrate_mysql_users(engine, columns):
    statements = []
    if not columns['email']['nullable']:
        statements.append('MODIFY COLUMN email VARCHAR(120) NULL')
    if not columns['password_hash']['nullable']:
        statements.append('MODIFY COLUMN password_hash VARCHAR(255) NULL')
    if 'firebase_uid' not in columns:
        statements.append('ADD COLUMN firebase_uid VARCHAR(128) NULL')
    if 'phone_verified_at' not in columns:
        statements.append('ADD COLUMN phone_verified_at DATETIME NULL')

    with engine.begin() as connection:
        if statements:
            connection.exec_driver_sql(f"ALTER TABLE users {', '.join(statements)}")
        indexes = inspect(connection).get_indexes('users')
        if not any(index.get('column_names') == ['firebase_uid'] and index.get('unique') for index in indexes):
            connection.exec_driver_sql(
                'CREATE UNIQUE INDEX ix_users_firebase_uid ON users (firebase_uid)'
            )


def _migrate_postgresql_users(engine, columns):
    with engine.begin() as connection:
        if not columns['email']['nullable']:
            connection.exec_driver_sql('ALTER TABLE users ALTER COLUMN email DROP NOT NULL')
        if not columns['password_hash']['nullable']:
            connection.exec_driver_sql('ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL')
        if 'firebase_uid' not in columns:
            connection.exec_driver_sql('ALTER TABLE users ADD COLUMN firebase_uid VARCHAR(128)')
        if 'phone_verified_at' not in columns:
            connection.exec_driver_sql('ALTER TABLE users ADD COLUMN phone_verified_at TIMESTAMP')
        connection.exec_driver_sql(
            'CREATE UNIQUE INDEX IF NOT EXISTS ix_users_firebase_uid ON users (firebase_uid)'
        )
