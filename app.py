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

@app.route('/generate', methods=['POST'])
def generate():
    errors = {}
    form_data = request.form

    content_type = form_data.get('content_type', 'url')
    data_from_form = "" # Para URL y Texto
    if content_type == 'url': data_from_form = form_data.get('data_url', '')
    elif content_type == 'text': data_from_form = form_data.get('data_text', '')


    # --- Validación de Parámetros Comunes ---
    error_correction = form_data.get('error_correction', 'M')
    if error_correction not in ERROR_LEVELS: errors['error_correction'] = "Nivel de error inválido."

    try: scale = int(form_data.get('scale', '10'))
    except ValueError: errors['scale'] = "La escala debe ser un número."; scale = 10
    if not 1 <= scale <= 100: errors['scale'] = "La escala debe estar entre 1 y 100."

    try: border = int(form_data.get('border', '4'))
    except ValueError: errors['border'] = "El borde debe ser un número."; border = 4
    if not 0 <= border <= 20: errors['border'] = "El borde debe estar entre 0 y 20."

    dark_color = form_data.get('dark_color', '#000000')
    if not is_valid_color_hex(dark_color): errors['dark_color'] = "Formato de color oscuro inválido (ej: #RRGGBB)."

    light_color_input = form_data.get('light_color', '#ffffff')
    is_transparent = form_data.get('transparent_bg') == 'on'
    light_color = "transparent" if is_transparent else light_color_input
    if not is_transparent and not is_valid_color_hex(light_color):
        errors['light_color'] = "Formato de color claro inválido (ej: #RRGGBB)."

    output_format = form_data.get('output_format', 'png')
    if output_format not in OUTPUT_FORMATS: errors['output_format'] = "Formato de salida inválido."

    # --- Parámetros y Validación Específicos del Tipo de Contenido ---
    kwargs_for_generator = {}

    if content_type == 'url':
        if not data_from_form or not (data_from_form.startswith('http://') or data_from_form.startswith('https://')):
            errors['data_url'] = "Se requiere una URL válida (http:// o https://)."
    elif content_type == 'text':
        if not data_from_form.strip(): errors['data_text'] = "El texto no puede estar vacío."
    # No se necesita validación extra para 'enable_tracking' aquí, se maneja en la lógica de generación.
    elif content_type == 'wifi':
        kwargs_for_generator['wifi_ssid'] = form_data.get('wifi_ssid')
        if not kwargs_for_generator['wifi_ssid']: errors['wifi_ssid'] = "SSID es obligatorio."
        kwargs_for_generator['wifi_password'] = form_data.get('wifi_password')
        kwargs_for_generator['wifi_security'] = form_data.get('wifi_security')
        if kwargs_for_generator['wifi_security'] not in WIFI_SECURITY_TYPES: errors['wifi_security'] = "Tipo de seguridad WiFi inválido."
        kwargs_for_generator['wifi_hidden'] = form_data.get('wifi_hidden') == 'on'
        if not kwargs_for_generator['wifi_password'] and kwargs_for_generator['wifi_security'] in ['WPA', 'WEP']:
             errors['wifi_password'] = "Se requiere contraseña para seguridad WPA/WEP."

    elif content_type == 'vcard':
        vcard_p = {
            'firstname': form_data.get('vcard_firstname'), 'lastname': form_data.get('vcard_lastname'),
            'displayname': form_data.get('vcard_displayname'), 'email': form_data.get('vcard_email'),
            'phone': form_data.get('vcard_phone_work'), 'mobile': form_data.get('vcard_phone_mobile'),
            'homephone': form_data.get('vcard_phone_home'), 'fax': form_data.get('vcard_fax'),
            'org': form_data.get('vcard_company'), 'title': form_data.get('vcard_jobtitle'),
            'address': form_data.get('vcard_address_full'), # Un solo campo para dirección simple
            'street': form_data.get('vcard_street'), 'city': form_data.get('vcard_city'),
            'region': form_data.get('vcard_region'), 'zipcode': form_data.get('vcard_postcode'),
            'country': form_data.get('vcard_country'), 'url': form_data.get('vcard_website'),
            'birthday': form_data.get('vcard_birthday'), 'note': form_data.get('vcard_note'),
            'nickname': form_data.get('vcard_nickname')
        }
        vcard_p = {k: v for k, v in vcard_p.items() if v} # Limpiar vacíos
        if not (vcard_p.get('firstname') or vcard_p.get('lastname') or vcard_p.get('displayname')):
            errors['vcard_name'] = "Se requiere Nombre, Apellido o Nombre a Mostrar para vCard."
        kwargs_for_generator['vcard_params'] = vcard_p

    elif content_type == 'mecard':
        mecard_p = {
            'firstname': form_data.get('mecard_firstname'), 'lastname': form_data.get('mecard_lastname'),
            'reading': form_data.get('mecard_reading'), 'nickname': form_data.get('mecard_nickname'),
            'email': form_data.get('mecard_email'), 'phone': form_data.get('mecard_phone'),
            'address': form_data.get('mecard_address'),
            'birthday': form_data.get('mecard_birthday_formatted'), # YYYYMMDD
            'url': form_data.get('mecard_url'), 'memo': form_data.get('mecard_memo')
        }
        mecard_p = {k: v for k, v in mecard_p.items() if v}
        if not (mecard_p.get('firstname') or mecard_p.get('lastname')):
             errors['mecard_name'] = "Se requiere Nombre o Apellido para MeCard."
        kwargs_for_generator['mecard_params'] = mecard_p

    elif content_type == 'email':
        kwargs_for_generator['email_to'] = form_data.get('email_to')
        if not kwargs_for_generator['email_to']: errors['email_to'] = "Email 'Para' es obligatorio."
        kwargs_for_generator['email_subject'] = form_data.get('email_subject')
        kwargs_for_generator['email_body'] = form_data.get('email_body')

    elif content_type == 'sms':
        kwargs_for_generator['sms_to'] = form_data.get('sms_to')
        if not kwargs_for_generator['sms_to']: errors['sms_to'] = "Número SMS 'Para' es obligatorio."
        kwargs_for_generator['sms_body'] = form_data.get('sms_body')

    elif content_type == 'tel':
        kwargs_for_generator['tel_number'] = form_data.get('tel_number')
        if not kwargs_for_generator['tel_number']: errors['tel_number'] = "Número de teléfono es obligatorio."

    elif content_type == 'geo':
        try:
            kwargs_for_generator['geo_latitude'] = float(form_data.get('geo_latitude','0'))
            kwargs_for_generator['geo_longitude'] = float(form_data.get('geo_longitude','0'))
        except ValueError: errors['geo_coords'] = "Latitud y Longitud deben ser números."
        if not form_data.get('geo_latitude') or not form_data.get('geo_longitude'):
             errors['geo_coords'] = "Latitud y Longitud son obligatorios."


    elif content_type == 'event':
        kwargs_for_generator['event_summary'] = form_data.get('event_summary')
        kwargs_for_generator['event_start'] = form_data.get('event_start_datetime') # Formato ISO de datetime-local
        kwargs_for_generator['event_end'] = form_data.get('event_end_datetime')
        if not kwargs_for_generator['event_summary']: errors['event_summary'] = "Título del evento es obligatorio."
        if not kwargs_for_generator['event_start']: errors['event_start_datetime'] = "Fecha/hora de inicio es obligatoria."
        if not kwargs_for_generator['event_end']: errors['event_end_datetime'] = "Fecha/hora de fin es obligatoria."
        # Validar que end > start
        if kwargs_for_generator['event_start'] and kwargs_for_generator['event_end']:
            try:
                start_dt = datetime.datetime.fromisoformat(kwargs_for_generator['event_start'])
                end_dt = datetime.datetime.fromisoformat(kwargs_for_generator['event_end'])
                if end_dt <= start_dt: errors['event_end_datetime'] = "La fecha de fin debe ser posterior a la de inicio."
            except ValueError: errors['event_dates'] = "Formato de fecha/hora de evento inválido."

        kwargs_for_generator['event_description'] = form_data.get('event_description')
        kwargs_for_generator['event_location'] = form_data.get('event_location')
        kwargs_for_generator['event_allday'] = form_data.get('event_allday') == 'on'

    elif content_type == 'epc':
        kwargs_for_generator['epc_name'] = form_data.get('epc_name')
        kwargs_for_generator['epc_iban'] = form_data.get('epc_iban')
        kwargs_for_generator['epc_amount'] = form_data.get('epc_amount')
        if not kwargs_for_generator['epc_name']: errors['epc_name'] = "Nombre del beneficiario EPC es obligatorio."
        if not kwargs_for_generator['epc_iban']: errors['epc_iban'] = "IBAN EPC es obligatorio." # Podría añadir validación de formato IBAN
        if not kwargs_for_generator['epc_amount']: errors['epc_amount'] = "Importe EPC es obligatorio."
        else:
            try: float(kwargs_for_generator['epc_amount'])
            except ValueError: errors['epc_amount'] = "Importe EPC debe ser un número."
        kwargs_for_generator['epc_currency'] = form_data.get('epc_currency', 'EUR')
        kwargs_for_generator['epc_bic'] = form_data.get('epc_bic')
        kwargs_for_generator['epc_purpose'] = form_data.get('epc_purpose')
        kwargs_for_generator['epc_reference'] = form_data.get('epc_reference')
        kwargs_for_generator['epc_remittance'] = form_data.get('epc_remittance')

    if errors:
        # Si 'is_preview' es un parámetro en la request, devolver JSON. Sino, ¿redirigir con errores?
        # Por ahora, la UI siempre usa fetch, así que JSON está bien.
        return jsonify({"success": False, "error": "Datos inválidos.", "field_errors": errors}), 400

    # --- Llamada a la Lógica de Generación ---
    data_for_qr = data_from_form
    enable_tracking = form_data.get('enable_tracking') == 'on'

    if content_type == 'url' and enable_tracking:
        if not data_from_form or not (data_from_form.startswith('http://') or data_from_form.startswith('https://')):
            # Este error ya debería haber sido capturado antes, pero por si acaso.
            return jsonify({"success": False, "error": "Se requiere una URL válida para el seguimiento.", "field_errors": {'data_url': 'URL inválida.'}}), 400

        # Generar un short_code único
        short_code = uuid.uuid4().hex[:6] # Un código corto, podría necesitar lógica para asegurar unicidad si hay colisiones
        while TrackableQR.query.filter_by(short_code=short_code).first() is not None:
            short_code = uuid.uuid4().hex[:6]

        new_qr_record = TrackableQR(original_url=data_from_form, short_code=short_code)
        db.session.add(new_qr_record)
        try:
            db.session.commit()
            # La URL que se codificará en el QR será la URL de seguimiento
            data_for_qr = url_for('track_qr_visit', short_code=short_code, _external=True)
        except Exception as e: # Podría ser por colisión de short_code si no se maneja bien o error de BD
            db.session.rollback()
            app.logger.error(f"Error al guardar QR rastreable: {e}")
            return jsonify({"success": False, "error": "No se pudo crear el QR rastreable en la base de datos."}), 500

    try:
        qr_result = generate_qr_code(
            data=data_for_qr, # Usar data_for_qr que puede ser la URL de seguimiento
            error=error_correction, scale=scale, border=border,
            dark_color=dark_color, light_color=light_color,
            output_format=output_format, content_type=content_type, # content_type sigue siendo 'url' para la lógica de formato
            **kwargs_for_generator
        )
    except ValueError as ve:
         return jsonify({"success": False, "error": str(ve)}), 400
    except NotImplementedError as nie:
         return jsonify({"success": False, "error": str(nie)}), 501 # Not Implemented

    if qr_result is None:
        return jsonify({"success": False, "error": "Fallo al generar el código QR. Verifique los datos de entrada."}), 500

    filename = f"qrcode_gen.{output_format}"
    mimetype_map = {
        'png': 'image/png', 'svg': 'image/svg+xml',
        'txt': 'text/plain', 'pdf': 'application/pdf', 'eps': 'application/postscript'
    }
    mimetype = mimetype_map.get(output_format, 'application/octet-stream')

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
    app.run(debug=True, host='0.0.0.0')
