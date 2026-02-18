"""
RailPlan — Application de planification ferroviaire
Backend Flask avec SQLite, export CSV, alertes email
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import csv
import io
import os

app = Flask(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///railplan.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email config (via variables d'environnement)
app.config['MAIL_SERVER']   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT']     = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'railplan@app.fr')

db   = SQLAlchemy(app)
mail = Mail(app)

# ─── Modèles ─────────────────────────────────────────────────────────────────
class Train(db.Model):
    __tablename__ = 'trains'
    id         = db.Column(db.Integer, primary_key=True)
    train_id   = db.Column(db.String(20), unique=True, nullable=False)
    rail       = db.Column(db.Integer, nullable=False)          # 1, 2, 3
    cargo      = db.Column(db.String(50), nullable=False)
    tonnage    = db.Column(db.Integer, nullable=False)
    client     = db.Column(db.String(100), nullable=False)
    depart     = db.Column(db.DateTime, nullable=False)
    arrivee    = db.Column(db.DateTime, nullable=False)
    status     = db.Column(db.String(20), default='Planifié')   # En route / Planifié / Arrivé / Alerte
    notes      = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'train_id':  self.train_id,
            'rail':      self.rail,
            'cargo':     self.cargo,
            'tonnage':   self.tonnage,
            'client':    self.client,
            'depart':    self.depart.isoformat(),
            'arrivee':   self.arrivee.isoformat(),
            'status':    self.status,
            'notes':     self.notes,
            'created_at': self.created_at.isoformat(),
        }


class AlertConfig(db.Model):
    __tablename__ = 'alert_config'
    id          = db.Column(db.Integer, primary_key=True)
    email       = db.Column(db.String(200), nullable=False)
    delay_min   = db.Column(db.Integer, default=60)
    alert_types = db.Column(db.String(50), default='all')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'delay_min': self.delay_min,
            'alert_types': self.alert_types,
        }


# ─── Seed data ────────────────────────────────────────────────────────────────
def seed_data():
    if Train.query.count() > 0:
        return
    samples = [
        dict(train_id='TRN-001', rail=1, cargo='Orge',      tonnage=1800, client='Groupe Limagrain',
             depart='2025-02-18T06:00', arrivee='2025-02-18T14:30', status='En route'),
        dict(train_id='TRN-002', rail=2, cargo='Blé',       tonnage=2400, client='Soufflet Agriculture',
             depart='2025-02-18T08:00', arrivee='2025-02-18T16:00', status='En route'),
        dict(train_id='TRN-003', rail=3, cargo='Maïs',      tonnage=1500, client='Agri Invest SAS',
             depart='2025-02-18T10:00', arrivee='2025-02-18T18:45', status='Planifié'),
        dict(train_id='TRN-004', rail=1, cargo='Colza',     tonnage=950,  client='Oleon France',
             depart='2025-02-17T20:00', arrivee='2025-02-18T07:00', status='Alerte', notes='Retard météo'),
        dict(train_id='TRN-005', rail=2, cargo='Tournesol', tonnage=3200, client='Saipol',
             depart='2025-02-18T12:00', arrivee='2025-02-19T04:00', status='Planifié'),
    ]
    for s in samples:
        t = Train(
            train_id=s['train_id'], rail=s['rail'], cargo=s['cargo'],
            tonnage=s['tonnage'], client=s['client'],
            depart=datetime.fromisoformat(s['depart']),
            arrivee=datetime.fromisoformat(s['arrivee']),
            status=s.get('status','Planifié'),
            notes=s.get('notes','')
        )
        db.session.add(t)
    db.session.commit()


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# --- Trains CRUD ---
@app.route('/api/trains', methods=['GET'])
def get_trains():
    rail   = request.args.get('rail')
    cargo  = request.args.get('cargo')
    status = request.args.get('status')

    q = Train.query
    if rail   and rail   != 'all': q = q.filter_by(rail=int(rail))
    if cargo  and cargo  != 'all': q = q.filter_by(cargo=cargo)
    if status and status != 'all': q = q.filter_by(status=status)

    return jsonify([t.to_dict() for t in q.order_by(Train.depart).all()])


@app.route('/api/trains', methods=['POST'])
def create_train():
    data = request.get_json()
    # Auto-generate train_id
    count = Train.query.count() + 1
    train_id = f"TRN-{count:03d}"
    while Train.query.filter_by(train_id=train_id).first():
        count += 1
        train_id = f"TRN-{count:03d}"

    t = Train(
        train_id = train_id,
        rail     = int(data['rail']),
        cargo    = data['cargo'],
        tonnage  = int(data['tonnage']),
        client   = data.get('client', 'Client inconnu'),
        depart   = datetime.fromisoformat(data['depart']),
        arrivee  = datetime.fromisoformat(data['arrivee']),
        status   = data.get('status', 'Planifié'),
        notes    = data.get('notes', ''),
    )
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict()), 201


@app.route('/api/trains/<int:train_id>', methods=['PUT'])
def update_train(train_id):
    t    = Train.query.get_or_404(train_id)
    data = request.get_json()
    for field in ['cargo', 'tonnage', 'client', 'status', 'notes']:
        if field in data:
            setattr(t, field, data[field])
    if 'depart'  in data: t.depart  = datetime.fromisoformat(data['depart'])
    if 'arrivee' in data: t.arrivee = datetime.fromisoformat(data['arrivee'])
    db.session.commit()
    return jsonify(t.to_dict())


@app.route('/api/trains/<int:train_id>', methods=['DELETE'])
def delete_train(train_id):
    t = Train.query.get_or_404(train_id)
    db.session.delete(t)
    db.session.commit()
    return jsonify({'deleted': train_id})


# --- Export CSV ---
@app.route('/api/export/csv')
def export_csv():
    rail   = request.args.get('rail')
    cargo  = request.args.get('cargo')
    status = request.args.get('status')

    q = Train.query
    if rail   and rail   != 'all': q = q.filter_by(rail=int(rail))
    if cargo  and cargo  != 'all': q = q.filter_by(cargo=cargo)
    if status and status != 'all': q = q.filter_by(status=status)
    trains = q.order_by(Train.depart).all()

    RAIL_NAMES = {1: 'Ligne A — Nord', 2: 'Ligne B — Est', 3: 'Ligne C — Ouest'}

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'ID Convoi', 'Ligne', 'Marchandise', 'Tonnage (t)',
        'Client', 'Date Départ', 'Date Arrivée', 'Statut', 'Notes'
    ])
    for t in trains:
        writer.writerow([
            t.train_id,
            RAIL_NAMES.get(t.rail, f'Ligne {t.rail}'),
            t.cargo,
            t.tonnage,
            t.client,
            t.depart.strftime('%d/%m/%Y %H:%M'),
            t.arrivee.strftime('%d/%m/%Y %H:%M'),
            t.status,
            t.notes or '',
        ])

    output.seek(0)
    filename = f"railplan_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),   # BOM pour Excel
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename,
    )


# --- Alertes config ---
@app.route('/api/alerts/config', methods=['GET'])
def get_alert_config():
    cfg = AlertConfig.query.first()
    if not cfg:
        return jsonify({'email':'', 'delay_min':60, 'alert_types':'all'})
    return jsonify(cfg.to_dict())


@app.route('/api/alerts/config', methods=['POST'])
def save_alert_config():
    data = request.get_json()
    cfg  = AlertConfig.query.first()
    if not cfg:
        cfg = AlertConfig()
        db.session.add(cfg)
    cfg.email       = data.get('email', '')
    cfg.delay_min   = int(data.get('delay_min', 60))
    cfg.alert_types = data.get('alert_types', 'all')
    db.session.commit()
    return jsonify(cfg.to_dict())


@app.route('/api/alerts/test', methods=['POST'])
def test_alert():
    cfg = AlertConfig.query.first()
    if not cfg or not cfg.email:
        return jsonify({'error': 'Aucun email configuré'}), 400
    try:
        msg = Message(
            subject='[RailPlan] ✅ Test d\'alerte',
            recipients=[cfg.email],
            body=(
                'Bonjour,\n\n'
                'Ceci est un email de test de votre système RailPlan.\n'
                'Les alertes sont correctement configurées.\n\n'
                '— RailPlan Système'
            )
        )
        mail.send(msg)
        return jsonify({'sent': True, 'to': cfg.email})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Stats ────────────────────────────────────────────────────────────────────
@app.route('/api/stats')
def get_stats():
    all_trains = Train.query.all()
    return jsonify({
        'total':      len(all_trains),
        'en_route':   sum(1 for t in all_trains if t.status == 'En route'),
        'planifie':   sum(1 for t in all_trains if t.status == 'Planifié'),
        'arrive':     sum(1 for t in all_trains if t.status == 'Arrivé'),
        'alerte':     sum(1 for t in all_trains if t.status == 'Alerte'),
        'tonnage_total': sum(t.tonnage for t in all_trains),
    })


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('DEBUG', 'false').lower() == 'true')
