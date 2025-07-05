import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.svg import SvgPathImage
from io import BytesIO
import urllib.parse
import datetime

# --- Funciones para construir strings de datos estructurados ---
# (Las funciones construir_vcard_string, construir_mecard_string, etc. permanecen igual que en la versión anterior exitosa)
def construir_vcard_string(**kwargs):
    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    n_parts = []
    lastname = kwargs.get('lastname')
    firstname = kwargs.get('firstname')
    if lastname: n_parts.append(lastname)
    if firstname: n_parts.append(firstname)

    displayname = kwargs.get('displayname')
    final_fn = None
    # FN es obligatorio. Si no se da displayname, construirlo.
    if displayname: final_fn = displayname
    elif firstname and lastname: final_fn = f"{firstname} {lastname}".strip()
    elif firstname: final_fn = firstname
    elif lastname: final_fn = lastname
    elif kwargs.get('name'): final_fn = kwargs.get('name').replace(';', ' ').strip()

    if not final_fn: raise ValueError("vCard requiere FN (displayname o firstname/lastname).")
    lines.append(f"FN:{final_fn}")

    final_n = None
    if kwargs.get('name'): final_n = kwargs.get('name')
    elif lastname or firstname: final_n = f"{lastname or ''};{firstname or ''}"

    if final_n: lines.append(f"N:{final_n}")
    elif final_fn: lines.append(f"N:{final_fn.replace(' ',';',1)}")

    if kwargs.get('org'): lines.append(f"ORG:{kwargs.get('org')}")
    if kwargs.get('title'): lines.append(f"TITLE:{kwargs.get('title')}")
    if kwargs.get('nickname'): lines.append(f"NICKNAME:{kwargs.get('nickname')}")
    if kwargs.get('email'): lines.append(f"EMAIL;TYPE=INTERNET:{kwargs.get('email')}")
    if kwargs.get('url'): lines.append(f"URL:{kwargs.get('url')}")
    if kwargs.get('phone'): lines.append(f"TEL;TYPE=WORK,VOICE:{kwargs.get('phone')}")
    if kwargs.get('mobile'): lines.append(f"TEL;TYPE=CELL,VOICE:{kwargs.get('mobile')}")
    if kwargs.get('homephone'): lines.append(f"TEL;TYPE=HOME,VOICE:{kwargs.get('homephone')}")
    if kwargs.get('fax'): lines.append(f"TEL;TYPE=FAX:{kwargs.get('fax')}")

    adr_str_parts = []
    if kwargs.get('street'): adr_str_parts.append(kwargs.get('street'))
    if kwargs.get('city'): adr_str_parts.append(kwargs.get('city'))
    if kwargs.get('region'): adr_str_parts.append(kwargs.get('region'))
    if kwargs.get('zipcode'): adr_str_parts.append(kwargs.get('zipcode'))
    if kwargs.get('country'): adr_str_parts.append(kwargs.get('country'))
    final_adr = kwargs.get('address')
    if not final_adr and adr_str_parts:
        final_adr = ";".join(["", "", *adr_str_parts])
    if final_adr: lines.append(f"ADR;TYPE=WORK:{final_adr if isinstance(final_adr, str) else ';'.join(filter(None,final_adr))}")

    if kwargs.get('birthday'):
        bday_str = kwargs.get('birthday')
        try:
            datetime.datetime.strptime(bday_str, '%Y-%m-%d')
            lines.append(f"BDAY:{bday_str}")
        except ValueError:
            try:
                bday_dt = datetime.datetime.strptime(bday_str, '%Y%m%d')
                lines.append(f"BDAY:{bday_dt.strftime('%Y-%m-%d')}")
            except ValueError: pass
    if kwargs.get('note'): lines.append(f"NOTE:{kwargs.get('note')}")
    lines.append("END:VCARD")
    return "\r\n".join(lines)

def construir_mecard_string(**kwargs):
    lines = ["MECARD:"]
    name_val = None; firstname = kwargs.get('firstname'); lastname = kwargs.get('lastname')
    if kwargs.get('name'): name_val = kwargs.get('name')
    elif lastname and firstname: name_val = f"{lastname},{firstname}"
    elif lastname: name_val = lastname
    elif firstname: name_val = firstname
    if not name_val: raise ValueError("MeCard requiere 'name' (o firstname/lastname).")
    lines.append(f"N:{name_val};")

    if kwargs.get('reading'): lines.append(f"SOUND:{kwargs.get('reading')};")
    if kwargs.get('nickname'): lines.append(f"NICKNAME:{kwargs.get('nickname')};")
    if kwargs.get('phone'): lines.append(f"TEL:{kwargs.get('phone')};")
    if kwargs.get('email'): lines.append(f"EMAIL:{kwargs.get('email')};")
    if kwargs.get('url'): lines.append(f"URL:{kwargs.get('url')};")
    if kwargs.get('memo'): lines.append(f"NOTE:{kwargs.get('memo')};")

    adr_str_parts = [];
    if kwargs.get('street'): adr_str_parts.append(kwargs.get('street'))
    if kwargs.get('city'): adr_str_parts.append(kwargs.get('city'))
    if kwargs.get('address'): adr_str_parts = [kwargs.get('address')]
    elif adr_str_parts: adr_str_parts = [", ".join(filter(None,adr_str_parts))]
    if adr_str_parts: lines.append(f"ADR:{adr_str_parts[0]};")

    if kwargs.get('birthday'):
        bday_str = kwargs.get('birthday')
        try: datetime.datetime.strptime(bday_str, '%Y%m%d'); lines.append(f"BDAY:{bday_str};")
        except ValueError:
            try: bday_dt = datetime.datetime.strptime(bday_str, '%Y-%m-%d'); lines.append(f"BDAY:{bday_dt.strftime('%Y%m%d')};")
            except ValueError: pass
    lines.append(";")
    return "".join(lines)

def construir_wifi_string(ssid, password, security, hidden=False):
    if not ssid: raise ValueError("SSID no puede ser vacío para WiFi QR.")
    sec_type = "WPA";
    if security and security.upper() in ["WPA", "WPA2", "WEP"]: sec_type = security.upper()
    elif not password: sec_type = "nopass"
    elements = [f"S:{ssid}", f"T:{sec_type}"]
    if password: elements.append(f"P:{password}")
    if hidden: elements.append("H:true")
    return "WIFI:" + ";".join(elements) + ";;"

def construir_email_string(to, subject=None, body=None):
    if not to: raise ValueError("Email 'to' no puede ser vacío.")
    actual_data = f"mailto:{to}"; params = {}
    if subject: params['subject'] = subject
    if body: params['body'] = body
    if params: actual_data += f"?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    return actual_data

def construir_sms_string(to, body=None):
    if not to: raise ValueError("SMS 'to' no puede ser vacío.")
    actual_data = f"SMSTO:{to}"
    if body: actual_data += f":{body}"
    return actual_data

def construir_tel_string(number):
    if not number: raise ValueError("Número de teléfono no puede ser vacío.")
    return f"tel:{number}"

def construir_geo_string(latitude, longitude, query=None):
    try: lat = float(latitude); lon = float(longitude)
    except ValueError: raise ValueError("Latitud y longitud deben ser números.")
    actual_data = f"geo:{lat},{lon}"
    if query: actual_data += f"?q={urllib.parse.quote(query)}"
    return actual_data

def construir_event_string(summary, dtstart, dtend, description=None, location=None, allday=False):
    def format_ical_datetime(dt, is_allday_event):
        dt_obj = None
        if isinstance(dt, str):
            try: dt_obj = datetime.datetime.fromisoformat(dt)
            except ValueError:
                try: dt_obj = datetime.datetime.strptime(dt, '%Y%m%dT%H%M%S')
                except ValueError:
                    try: dt_obj = datetime.datetime.strptime(dt, '%Y%m%d')
                    except ValueError: raise ValueError(f"Formato de fecha/hora no reconocido: {dt}")
        elif isinstance(dt, datetime.datetime): dt_obj = dt
        elif isinstance(dt, datetime.date): dt_obj = datetime.datetime.combine(dt, datetime.time.min)
        else: raise ValueError(f"Tipo de fecha/hora no válido: {type(dt)}")
        if is_allday_event: return dt_obj.strftime('%Y%m%d')
        return dt_obj.strftime('%Y%m%dT%H%M%S')

    if not summary or not dtstart or not dtend: raise ValueError("Evento requiere summary, dtstart y dtend.")
    event_lines = ["BEGIN:VEVENT", f"SUMMARY:{summary}"]
    dtstart_formatted = format_ical_datetime(dtstart, allday)
    dtend_formatted = format_ical_datetime(dtend, allday)
    dt_start_obj_for_end_calc = datetime.datetime.strptime(dtstart_formatted[:8], '%Y%m%d')
    if allday:
        event_lines.append(f"DTSTART;VALUE=DATE:{dtstart_formatted}")
        dt_end_obj_for_allday = datetime.datetime.strptime(dtend_formatted[:8], '%Y%m%d')
        if dt_end_obj_for_allday <= dt_start_obj_for_end_calc:
             dt_end_obj_for_allday = dt_start_obj_for_end_calc + datetime.timedelta(days=1)
        event_lines.append(f"DTEND;VALUE=DATE:{dt_end_obj_for_allday.strftime('%Y%m%d')}")
    else:
        event_lines.append(f"DTSTART:{dtstart_formatted}"); event_lines.append(f"DTEND:{dtend_formatted}")
    if description: event_lines.append(f"DESCRIPTION:{description.replace(chr(10), chr(92)+'n')}")
    if location: event_lines.append(f"LOCATION:{location.replace(chr(10), chr(92)+'n')}")
    event_lines.append("END:VEVENT"); ical_content = "\r\n".join(event_lines)
    return f"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//QR Generator//EN\r\n{ical_content}\r\nEND:VCALENDAR"

def construir_epc_string(name, iban, amount, currency='EUR', bic=None, purpose=None, reference=None, remittance=None):
    if not name or not iban or not amount: raise ValueError("EPC requiere name, iban y amount.")
    elements = [ "BCD", "002", "1", "SCT", bic or "", name, iban, f"{currency.upper()}{amount}",
                 purpose or "", reference or "", remittance or "", "" ]
    return "\n".join(elements).replace("\n\n","\n").strip()

def generate_qr_code(data, error='q', scale=10, border=4,
                     dark_color='#000000', light_color='#ffffff',
                     output_format='png', content_type='url', **kwargs):
    actual_data = data
    try:
        if output_format == 'html':
             raise NotImplementedError("HTML output no está soportado directamente con python-qrcode en esta implementación.")

        # Construcción de datos específicos
        if content_type == 'wifi':
            actual_data = construir_wifi_string(kwargs.get('wifi_ssid'), kwargs.get('wifi_password'), kwargs.get('wifi_security'), kwargs.get('wifi_hidden', False))
        elif content_type == 'vcard':
            actual_data = construir_vcard_string(**kwargs.get('vcard_params', {}))
        elif content_type == 'mecard':
            actual_data = construir_mecard_string(**kwargs.get('mecard_params', {}))
        elif content_type == 'email':
            actual_data = construir_email_string(kwargs.get('email_to'), kwargs.get('email_subject'), kwargs.get('email_body'))
        elif content_type == 'sms':
            actual_data = construir_sms_string(kwargs.get('sms_to'), kwargs.get('sms_body'))
        elif content_type == 'tel':
            actual_data = construir_tel_string(kwargs.get('tel_number'))
        elif content_type == 'event':
            actual_data = construir_event_string(kwargs.get('event_summary'), kwargs.get('event_start'), kwargs.get('event_end'), kwargs.get('event_description'), kwargs.get('event_location'), kwargs.get('event_allday', False))
        elif content_type == 'geo':
            actual_data = construir_geo_string(kwargs.get('geo_latitude'), kwargs.get('geo_longitude'))
        elif content_type == 'epc':
            actual_data = construir_epc_string(kwargs.get('epc_name'), kwargs.get('epc_iban'), kwargs.get('epc_amount'), kwargs.get('epc_currency','EUR'), kwargs.get('epc_bic'), kwargs.get('epc_purpose'), kwargs.get('epc_reference'), kwargs.get('epc_remittance'))
        elif content_type not in ['url', 'text'] and (actual_data is None or str(actual_data).strip() == ''):
             raise ValueError(f"Datos insuficientes para content_type: {content_type}")

        if actual_data is None or str(actual_data).strip() == '':
            raise ValueError("El contenido a codificar no puede ser vacío.")

        error_correction_map = {
            'L': qrcode.constants.ERROR_CORRECT_L, 'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q, 'H': qrcode.constants.ERROR_CORRECT_H
        }
        qr_error = error_correction_map.get(error.upper(), qrcode.constants.ERROR_CORRECT_M)

        qr_obj = qrcode.QRCode(version=None, error_correction=qr_error, box_size=scale, border=border)
        qr_obj.add_data(actual_data)
        qr_obj.make(fit=True)

        # Determinar kwargs para make_image basado en transparencia
        effective_light_color = light_color
        if light_color and light_color.lower() == 'transparent' and output_format in ['png', 'svg']:
            effective_light_color = "transparent" # PilImage y SvgImage manejan "transparent"

        pil_kwargs = {'fill_color': dark_color, 'back_color': effective_light_color}
        svg_kwargs = {'module_color': dark_color} # SvgImage usa module_color
        if effective_light_color != "transparent":
            svg_kwargs['background_color'] = effective_light_color # y background_color
        # Si es transparent, SvgImage omite el fondo por defecto.

        out = BytesIO()
        if output_format == 'svg':
            img = qr_obj.make_image(image_factory=SvgPathImage, **svg_kwargs)
            img.save(out)
        elif output_format == 'txt':
            import io
            temp_out = io.StringIO()
            qr_obj.print_ascii(out=temp_out, tty=False)
            temp_out.seek(0)
            out.write(temp_out.read().encode('utf-8'))
        else: # PNG y otros formatos que PilImage pueda manejar
            img = qr_obj.make_image(image_factory=StyledPilImage, **pil_kwargs)
            pil_format = 'PNG' # Default
            if output_format.upper() in ["JPEG", "JPG"]: pil_format = "JPEG"
            elif output_format.upper() == "BMP": pil_format = "BMP"
            elif output_format.upper() == "GIF": pil_format = "GIF"
            # EPS/PDF no son directos, se quedarán como PNG por ahora si se piden.
            if output_format not in ['png', 'svg', 'txt', 'jpeg', 'jpg', 'bmp', 'gif']:
                pil_format = 'PNG'
            img.save(out, format=pil_format)

        out.seek(0)
        return out

    except ValueError as ve: raise ve
    except NotImplementedError as nie: raise nie
    except Exception as e:
        print(f"Error generando QR ({content_type}, format {output_format}): {e}")
        return None

if __name__ == '__main__':
    print("Para pruebas, ejecute test_qr_generator_logic.py")
