from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from database import (
    init_db, 
    get_all_etudiants, get_etudiant_by_id,
    create_etudiant, update_etudiant, delete_etudiant, get_etudiants_count,
    get_all_filieres, get_filiere_by_id,
    get_admin_by_email, get_admin_by_id, verify_password,
    get_stats_counts, get_crud_stats,
    hash_password
)

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_inptic_2024_tres_longue_et_complexe'

# Configuration Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page'

# Métriques Prometheus
REQUEST_COUNT = Counter('app_requests_total', 'Total des requêtes', ['endpoint', 'method'])
CRUD_COUNT = Counter('crud_operations_total', 'Opérations CRUD', ['operation'])

# Initialiser la base de données
init_db()

# ========== MODÈLE UTILISATEUR ==========
class User:
    def __init__(self, user_data):
        self.id = user_data['id']
        self.email = user_data['email']
        self.nom = user_data['nom']
        self.prenom = user_data['prenom']
        self.role = user_data['role']
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    admin_data = get_admin_by_id(int(user_id))
    if admin_data:
        return User(admin_data)
    return None

# ========== ROUTES ==========

@app.route('/')
def home():
    REQUEST_COUNT.labels(endpoint='/', method='GET').inc()
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = get_admin_by_email(email)
        if admin and verify_password(admin['password'], password):
            user = User(admin)
            login_user(user)
            REQUEST_COUNT.labels(endpoint='/login', method='POST').inc()
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    REQUEST_COUNT.labels(endpoint='/dashboard', method='GET').inc()
    filieres = get_all_filieres()
    return render_template('dashboard.html', admin=current_user, filieres=filieres)

@app.route('/stats')
@login_required
def stats():
    REQUEST_COUNT.labels(endpoint='/stats', method='GET').inc()
    filieres = get_all_filieres()
    return render_template('stats.html', admin=current_user, filieres=filieres)

# ========== API CRUD ÉTUDIANTS ==========

@app.route('/api/etudiants', methods=['GET'])
@login_required
def api_list_etudiants():
    REQUEST_COUNT.labels(endpoint='/api/etudiants', method='GET').inc()
    etudiants = get_all_etudiants()
    return jsonify({'etudiants': etudiants, 'total': len(etudiants)})

@app.route('/api/etudiants', methods=['POST'])
@login_required
def api_create_etudiant():
    REQUEST_COUNT.labels(endpoint='/api/etudiants', method='POST').inc()
    data = request.get_json()
    
    etudiant_id = create_etudiant(
        nom=data['nom'],
        prenom=data['prenom'],
        email=data['email'],
        filiere_id=data['filiere_id'],
        niveau=data['niveau']
    )
    CRUD_COUNT.labels(operation='create').inc()
    
    return jsonify({'id': etudiant_id, 'message': 'Étudiant ajouté'}), 201

@app.route('/api/etudiants/<int:etudiant_id>', methods=['PUT'])
@login_required
def api_update_etudiant(etudiant_id):
    REQUEST_COUNT.labels(endpoint='/api/etudiants/<id>', method='PUT').inc()
    data = request.get_json()
    
    update_etudiant(
        etudiant_id,
        nom=data['nom'],
        prenom=data['prenom'],
        email=data['email'],
        filiere_id=data['filiere_id'],
        niveau=data['niveau']
    )
    CRUD_COUNT.labels(operation='update').inc()
    
    return jsonify({'message': 'Étudiant modifié'})

@app.route('/api/etudiants/<int:etudiant_id>', methods=['DELETE'])
@login_required
def api_delete_etudiant(etudiant_id):
    REQUEST_COUNT.labels(endpoint='/api/etudiants/<id>', method='DELETE').inc()
    delete_etudiant(etudiant_id)
    CRUD_COUNT.labels(operation='delete').inc()
    
    return jsonify({'message': 'Étudiant supprimé'})

# ========== API STATISTIQUES ==========

@app.route('/api/stats/filiere')
@login_required
def api_stats_filiere():
    REQUEST_COUNT.labels(endpoint='/api/stats/filiere', method='GET').inc()
    stats = get_stats_counts()
    return jsonify(stats)

@app.route('/api/stats/counts')
@login_required
def api_stats_counts():
    REQUEST_COUNT.labels(endpoint='/api/stats/counts', method='GET').inc()
    total_etudiants = get_etudiants_count()
    return jsonify({
        'total_etudiants': total_etudiants,
        'ajoutes': total_etudiants,
        'supprimes': 0
    })

# ========== MÉTRIQUES PROMETHEUS ==========

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
