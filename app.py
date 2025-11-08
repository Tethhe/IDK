from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
from qr_generator_logic import generate_qr_code
from io import BytesIO
import datetime
import re
import uuid
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuración de la base de datos SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'qr_codes.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la base de datos para los QRs rastreables
class TrackableQR(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_url = db.Column(db.String(2048), nullable=False)
    visit_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    short_code = db.Column(db.String(10), unique=True, nullable=False)

    def __repr__(self):
        return f'<TrackableQR {self.short_code} -> {self.original_url} (Visits: {self.visit_count})>'

with app.app_context():
    db.create_all() # Crea las tablas si no existen

ERROR_LEVELS = {'L': 'L (Low ~7%)', 'M': 'M (Medium ~15%)', 'Q': 'Q (Quartile ~25%)', 'H': 'H (High ~30%)'}
OUTPUT_FORMATS = {'png': 'PNG', 'svg': 'SVG', 'txt': 'TXT (Text Art)'} # HTML no soportado por ahora
CONTENT_TYPES = {
    'url': 'URL', 'text': 'Text', 'wifi': 'WiFi', 'vcard': 'vCard (Contact)',
    'mecard': 'MeCard (Contact)', 'email': 'Email', 'sms': 'SMS', 'tel': 'Telephone',
    'event': 'Event (iCalendar)', 'geo': 'Geo Location', 'epc': 'EPC (Payment)'
}
WIFI_SECURITY_TYPES = {'': 'None (Open)', 'WPA': 'WPA/WPA2', 'WEP': 'WEP'}

def is_valid_color_hex(s):
    return s and re.match(r'^#[0-9a-fA-F]{6}$', s)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', content_types=CONTENT_TYPES, error_levels=ERROR_LEVELS,
                           output_formats=OUTPUT_FORMATS, wifi_security_types=WIFI_SECURITY_TYPES)

# --- Funciones Auxiliares para /generate ---

def _validate_common_params(form_data):
    """Valida parámetros comunes a todos los tipos de QR."""
    errors = {}
    params = {}

    params['error_correction'] = form_data.get('error_correction', 'M')
    if params['error_correction'] not in ERROR_LEVELS:
        errors['error_correction'] = "Nivel de error inválido."

    try:
        params['scale'] = int(form_data.get('scale', '20'))
        if not 1 <= params['scale'] <= 200:
            errors['scale'] = "La escala debe estar entre 1 y 200."
    except ValueError:
        errors['scale'] = "La escala debe ser un número."
        params['scale'] = 20

    try:
        params['border'] = int(form_data.get('border', '4'))
        if not 0 <= params['border'] <= 20:
            errors['border'] = "El borde debe estar entre 0 y 20."
    except ValueError:
        errors['border'] = "El borde debe ser un número."
        params['border'] = 4

    params['dark_color'] = form_data.get('dark_color', '#000000')
    if not is_valid_color_hex(params['dark_color']):
        errors['dark_color'] = "Formato de color oscuro inválido (ej: #RRGGBB)."

    light_color_input = form_data.get('light_color', '#ffffff')
    is_transparent = form_data.get('transparent_bg') == 'on'
    params['light_color'] = "transparent" if is_transparent else light_color_input
    if not is_transparent and not is_valid_color_hex(params['light_color']):
        errors['light_color'] = "Formato de color claro inválido (ej: #RRGGBB)."

    params['output_format'] = form_data.get('output_format', 'png')
    if params['output_format'] not in OUTPUT_FORMATS:
        errors['output_format'] = "Formato de salida inválido."

    return params, errors

def _handle_url(form_data, errors):
    data = form_data.get('data_url', '')
    if not data or not (data.startswith('http://') or data.startswith('https://')):
        errors['data_url'] = "Se requiere una URL válida (http:// o https://)."
    return data, {}

def _handle_text(form_data, errors):
    data = form_data.get('data_text', '')
    if not data.strip():
        errors['data_text'] = "El texto no puede estar vacío."
    return data, {}

def _handle_wifi(form_data, errors):
    kwargs = {
        'wifi_ssid': form_data.get('wifi_ssid'),
        'wifi_password': form_data.get('wifi_password'),
        'wifi_security': form_data.get('wifi_security'),
        'wifi_hidden': form_data.get('wifi_hidden') == 'on'
    }
    if not kwargs['wifi_ssid']:
        errors['wifi_ssid'] = "SSID es obligatorio."
    if kwargs['wifi_security'] not in WIFI_SECURITY_TYPES:
        errors['wifi_security'] = "Tipo de seguridad WiFi inválido."
    if not kwargs['wifi_password'] and kwargs['wifi_security'] in ['WPA', 'WEP']:
        errors['wifi_password'] = "Se requiere contraseña para seguridad WPA/WEP."
    return None, kwargs

def _handle_vcard(form_data, errors):
    params = {
        'firstname': form_data.get('vcard_firstname'), 'lastname': form_data.get('vcard_lastname'),
        'displayname': form_data.get('vcard_displayname'), 'email': form_data.get('vcard_email'),
        'phone': form_data.get('vcard_phone_work'), 'mobile': form_data.get('vcard_phone_mobile'),
        'homephone': form_data.get('vcard_phone_home'), 'fax': form_data.get('vcard_fax'),
        'org': form_data.get('vcard_company'), 'title': form_data.get('vcard_jobtitle'),
        'address': form_data.get('vcard_address_full'), 'street': form_data.get('vcard_street'),
        'city': form_data.get('vcard_city'), 'region': form_data.get('vcard_region'),
        'zipcode': form_data.get('vcard_postcode'), 'country': form_data.get('vcard_country'),
        'url': form_data.get('vcard_website'), 'birthday': form_data.get('vcard_birthday'),
        'note': form_data.get('vcard_note'), 'nickname': form_data.get('vcard_nickname')
    }
    params = {k: v for k, v in params.items() if v}
    if not any(params.get(k) for k in ['firstname', 'lastname', 'displayname']):
        errors['vcard_name'] = "Se requiere Nombre, Apellido o Nombre a Mostrar para vCard."
    return None, {'vcard_params': params}

# ... crear funciones similares para mecard, email, sms, tel, geo, event, epc ...
def _handle_mecard(form_data, errors):
    params = {
        'firstname': form_data.get('mecard_firstname'), 'lastname': form_data.get('mecard_lastname'),
        'reading': form_data.get('mecard_reading'), 'nickname': form_data.get('mecard_nickname'),
        'email': form_data.get('mecard_email'), 'phone': form_data.get('mecard_phone'),
        'address': form_data.get('mecard_address'), 'birthday': form_data.get('mecard_birthday_formatted'),
        'url': form_data.get('mecard_url'), 'memo': form_data.get('mecard_memo')
    }
    params = {k: v for k, v in params.items() if v}
    if not any(params.get(k) for k in ['firstname', 'lastname']):
        errors['mecard_name'] = "Se requiere Nombre o Apellido para MeCard."
    return None, {'mecard_params': params}

def _handle_email(form_data, errors):
    kwargs = {
        'email_to': form_data.get('email_to'),
        'email_subject': form_data.get('email_subject'),
        'email_body': form_data.get('email_body')
    }
    if not kwargs['email_to']:
        errors['email_to'] = "Email 'Para' es obligatorio."
    return None, kwargs

def _handle_sms(form_data, errors):
    kwargs = {'sms_to': form_data.get('sms_to'), 'sms_body': form_data.get('sms_body')}
    if not kwargs['sms_to']:
        errors['sms_to'] = "Número SMS 'Para' es obligatorio."
    return None, kwargs

def _handle_tel(form_data, errors):
    kwargs = {'tel_number': form_data.get('tel_number')}
    if not kwargs['tel_number']:
        errors['tel_number'] = "Número de teléfono es obligatorio."
    return None, kwargs

def _handle_geo(form_data, errors):
    kwargs = {}
    try:
        kwargs['geo_latitude'] = float(form_data.get('geo_latitude', '0'))
        kwargs['geo_longitude'] = float(form_data.get('geo_longitude', '0'))
    except (ValueError, TypeError):
        errors['geo_coords'] = "Latitud y Longitud deben ser números."
    if not form_data.get('geo_latitude') or not form_data.get('geo_longitude'):
        errors['geo_coords'] = "Latitud y Longitud son obligatorios."
    return None, kwargs

def _handle_event(form_data, errors):
    kwargs = {
        'event_summary': form_data.get('event_summary'),
        'event_start': form_data.get('event_start_datetime'),
        'event_end': form_data.get('event_end_datetime'),
        'event_description': form_data.get('event_description'),
        'event_location': form_data.get('event_location'),
        'event_allday': form_data.get('event_allday') == 'on'
    }
    if not kwargs['event_summary']: errors['event_summary'] = "Título del evento es obligatorio."
    if not kwargs['event_start']: errors['event_start_datetime'] = "Fecha/hora de inicio es obligatoria."
    if not kwargs['event_end']: errors['event_end_datetime'] = "Fecha/hora de fin es obligatoria."
    if kwargs['event_start'] and kwargs['event_end']:
        try:
            start_dt = datetime.datetime.fromisoformat(kwargs['event_start'])
            end_dt = datetime.datetime.fromisoformat(kwargs['event_end'])
            if end_dt <= start_dt:
                errors['event_end_datetime'] = "La fecha de fin debe ser posterior a la de inicio."
        except ValueError:
            errors['event_dates'] = "Formato de fecha/hora de evento inválido."
    return None, kwargs

def _handle_epc(form_data, errors):
    kwargs = {
        'epc_name': form_data.get('epc_name'), 'epc_iban': form_data.get('epc_iban'),
        'epc_amount': form_data.get('epc_amount'), 'epc_currency': form_data.get('epc_currency', 'EUR'),
        'epc_bic': form_data.get('epc_bic'), 'epc_purpose': form_data.get('epc_purpose'),
        'epc_reference': form_data.get('epc_reference'), 'epc_remittance': form_data.get('epc_remittance')
    }
    if not kwargs['epc_name']: errors['epc_name'] = "Nombre del beneficiario EPC es obligatorio."
    if not kwargs['epc_iban']: errors['epc_iban'] = "IBAN EPC es obligatorio."
    if not kwargs['epc_amount']:
        errors['epc_amount'] = "Importe EPC es obligatorio."
    else:
        try:
            float(kwargs['epc_amount'])
        except ValueError:
            errors['epc_amount'] = "Importe EPC debe ser un número."
    return None, kwargs


def _get_content_handlers():
    return {
        'url': _handle_url, 'text': _handle_text, 'wifi': _handle_wifi,
        'vcard': _handle_vcard, 'mecard': _handle_mecard, 'email': _handle_email,
        'sms': _handle_sms, 'tel': _handle_tel, 'geo': _handle_geo,
        'event': _handle_event, 'epc': _handle_epc
    }

@app.route('/generate', methods=['POST'])
def generate():
    form_data = request.form
    content_type = form_data.get('content_type', 'url')

    # 1. Validar parámetros comunes
    common_params, errors = _validate_common_params(form_data)

    # 2. Obtener y ejecutar el manejador de contenido específico
    content_handlers = _get_content_handlers()
    handler = content_handlers.get(content_type)
    if not handler:
        return jsonify({"success": False, "error": "Tipo de contenido no válido."}), 400

    data_for_qr, kwargs_for_generator = handler(form_data, errors)

    # 3. Comprobar errores acumulados
    if errors:
        return jsonify({"success": False, "error": "Datos inválidos.", "field_errors": errors}), 400

    # 4. Manejar lógica de seguimiento de URL
    enable_tracking = form_data.get('enable_tracking') == 'on'
    if content_type == 'url' and enable_tracking:
        if not data_for_qr or not (data_for_qr.startswith('http://') or data_for_qr.startswith('https://')):
             return jsonify({"success": False, "error": "URL válida requerida para seguimiento.", "field_errors": {'data_url': 'URL inválida.'}}), 400

        short_code = uuid.uuid4().hex[:6]
        while TrackableQR.query.filter_by(short_code=short_code).first():
            short_code = uuid.uuid4().hex[:6]

        new_qr_record = TrackableQR(original_url=data_for_qr, short_code=short_code)
        db.session.add(new_qr_record)
        try:
            db.session.commit()
            data_for_qr = url_for('track_qr_visit', short_code=short_code, _external=True)
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error al guardar QR rastreable: {e}")
            return jsonify({"success": False, "error": "No se pudo crear el QR rastreable en la BD."}), 500

    # 5. Generar el código QR
    try:
        qr_result = generate_qr_code(
            data=data_for_qr,
            content_type=content_type,
            error=common_params['error_correction'],
            scale=common_params['scale'],
            border=common_params['border'],
            dark_color=common_params['dark_color'],
            light_color=common_params['light_color'],
            output_format=common_params['output_format'],
            **kwargs_for_generator
        )
    except (ValueError, NotImplementedError) as e:
        return jsonify({"success": False, "error": str(e)}), 400

    if not qr_result:
        return jsonify({"success": False, "error": "Fallo al generar el código QR."}), 500

    # 6. Enviar el archivo
    filename = f"qrcode_gen.{common_params['output_format']}"
    mimetype_map = {
        'png': 'image/png', 'svg': 'image/svg+xml', 'txt': 'text/plain',
        'pdf': 'application/pdf', 'eps': 'application/postscript'
    }
    mimetype = mimetype_map.get(common_params['output_format'], 'application/octet-stream')
    return send_file(qr_result, mimetype=mimetype, as_attachment=True, download_name=filename)

@app.route('/track/<short_code>')
def track_qr_visit(short_code):
    qr_record = TrackableQR.query.filter_by(short_code=short_code).first_or_404()

    # Incrementar el contador de visitas
    qr_record.visit_count += 1
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al actualizar el contador de visitas para {short_code}: {e}")
        # Opcionalmente, redirigir igualmente o mostrar un error diferente
        # Por ahora, redirigimos para no interrumpir al usuario

    return redirect(qr_record.original_url)

@app.route('/stats')
def show_stats():
    tracked_qrs = TrackableQR.query.order_by(TrackableQR.created_at.desc()).all()
    return render_template('stats.html', qrs=tracked_qrs)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
