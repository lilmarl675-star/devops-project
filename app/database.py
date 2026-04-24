import sqlite3
import os
import bcrypt
from datetime import datetime

DB_PATH = '/app/data/inptic.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('/app/data', exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS filieres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            code TEXT NOT NULL,
            couleur TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etudiants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            filiere_id INTEGER NOT NULL,
            niveau TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (filiere_id) REFERENCES filieres (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppressions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            etudiant_id INTEGER,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT NOT NULL,
            filiere TEXT NOT NULL,
            niveau TEXT NOT NULL,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_by TEXT
        )
    ''')
    
    conn.commit()
    
    filieres = [
        ('MTIC (Métiers du numérique)', 'MTIC', '#3B82F6'),
        ('GI (Génie Informatique)', 'GI', '#10B981'),
        ('RT (Réseaux et Télécommunications)', 'RT', '#F59E0B')
    ]
    for f in filieres:
        cursor.execute('INSERT OR IGNORE INTO filieres (nom, code, couleur) VALUES (?, ?, ?)', f)
    
    cursor.execute('SELECT COUNT(*) as total FROM admins')
    if cursor.fetchone()['total'] == 0:
        hashed = bcrypt.hashpw('Admin2024!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('INSERT INTO admins (nom, prenom, email, password, role) VALUES (?, ?, ?, ?, ?)',
                       ('Administrateur', 'Système', 'admin@inptic.com', hashed, 'super_admin'))
    
    conn.commit()
    conn.close()
    print("✅ Base initialisée")

def hash_password(pw): 
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(hashed, pw): 
    return bcrypt.checkpw(pw.encode('utf-8'), hashed.encode('utf-8'))

def get_admin_by_email(email):
    conn = get_db()
    admin = conn.execute('SELECT * FROM admins WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(admin) if admin else None

def get_admin_by_id(admin_id):
    conn = get_db()
    admin = conn.execute('SELECT * FROM admins WHERE id = ?', (admin_id,)).fetchone()
    conn.close()
    return dict(admin) if admin else None

def get_all_filieres():
    conn = get_db()
    f = conn.execute('SELECT * FROM filieres').fetchall()
    conn.close()
    return [dict(x) for x in f]

def get_all_etudiants():
    conn = get_db()
    e = conn.execute('''
        SELECT e.*, f.nom as filiere_nom, f.couleur 
        FROM etudiants e 
        JOIN filieres f ON e.filiere_id = f.id 
        ORDER BY e.id DESC
    ''').fetchall()
    conn.close()
    return [dict(x) for x in e]

def get_etudiant_by_id(etudiant_id):
    conn = get_db()
    e = conn.execute('SELECT * FROM etudiants WHERE id = ?', (etudiant_id,)).fetchone()
    conn.close()
    return dict(e) if e else None

def create_etudiant(nom, prenom, email, filiere_id, niveau):
    conn = get_db()
    c = conn.execute('''
        INSERT INTO etudiants (nom, prenom, email, filiere_id, niveau) 
        VALUES (?, ?, ?, ?, ?)
    ''', (nom, prenom, email, filiere_id, niveau))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

def update_etudiant(etudiant_id, nom, prenom, email, filiere_id, niveau):
    conn = get_db()
    conn.execute('''
        UPDATE etudiants 
        SET nom=?, prenom=?, email=?, filiere_id=?, niveau=? 
        WHERE id=?
    ''', (nom, prenom, email, filiere_id, niveau, etudiant_id))
    conn.commit()
    conn.close()

def delete_etudiant(etudiant_id, deleted_by="admin"):
    conn = get_db()
    e = conn.execute('''
        SELECT e.*, f.nom as filiere_nom 
        FROM etudiants e 
        JOIN filieres f ON e.filiere_id = f.id 
        WHERE e.id = ?
    ''', (etudiant_id,)).fetchone()
    if e:
        conn.execute('''
            INSERT INTO suppressions (etudiant_id, nom, prenom, email, filiere, niveau, deleted_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (e['id'], e['nom'], e['prenom'], e['email'], e['filiere_nom'], e['niveau'], deleted_by))
    conn.execute('DELETE FROM etudiants WHERE id = ?', (etudiant_id,))
    conn.commit()
    conn.close()

def get_all_suppressions():
    conn = get_db()
    s = conn.execute('SELECT * FROM suppressions ORDER BY deleted_at DESC').fetchall()
    conn.close()
    return [dict(x) for x in s]

def get_etudiants_count():
    conn = get_db()
    c = conn.execute('SELECT COUNT(*) as total FROM etudiants').fetchone()['total']
    conn.close()
    return c

def get_stats_counts():
    conn = get_db()
    stats = conn.execute('''
        SELECT f.id, f.nom, f.code, f.couleur, COUNT(e.id) as total
        FROM filieres f 
        LEFT JOIN etudiants e ON f.id = e.filiere_id
        GROUP BY f.id
    ''').fetchall()
    conn.close()
    return [dict(s) for s in stats]

def get_crud_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) as total FROM etudiants').fetchone()['total']
    supp = conn.execute('SELECT COUNT(*) as total FROM suppressions').fetchone()['total']
    conn.close()
    return {'total_etudiants': total, 'ajoutes': total, 'supprimes': supp}

def get_filiere_by_id(filiere_id):
    conn = get_db()
    filiere = conn.execute('SELECT * FROM filieres WHERE id = ?', (filiere_id,)).fetchone()
    conn.close()
    return dict(filiere) if filiere else None
