import unittest
from io import BytesIO
import datetime
import urllib

from qr_generator_logic import (
    generate_qr_code,
    construir_vcard_string,
    construir_mecard_string,
    construir_wifi_string,
    construir_email_string,
    construir_sms_string,
    construir_tel_string,
    construir_geo_string,
    construir_event_string,
    construir_epc_string
)

class TestQRGeneratorLogicPythonQrcode(unittest.TestCase):

    def _assert_is_valid_bytesio_output(self, result, min_length=1, decode_as_text=False, content_type_for_debug=""):
        self.assertIsNotNone(result, f"Resultado None. Tipo: {content_type_for_debug}.")
        self.assertIsInstance(result, BytesIO, f"Resultado no es BytesIO. Tipo: {content_type_for_debug}.")
        content = result.getvalue()
        self.assertTrue(len(content) >= min_length, f"Contenido corto ({len(content)}B). Tipo: {content_type_for_debug}")
        if decode_as_text:
            try: return content.decode('utf-8')
            except UnicodeDecodeError as e: self.fail(f"UnicodeDecodeError. Tipo: {content_type_for_debug}. Error: {e}")
        return content

    # Pruebas para generate_qr_code con diferentes tipos de contenido
    def test_generate_url_png(self):
        result = generate_qr_code("https://example.com", content_type='url', output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="url_png")

    def test_generate_text_svg(self):
        dark_color_hex = "#336699"
        light_color_hex = "#EFEFEF"
        result = generate_qr_code("Hello SVG", content_type='text', output_format='svg', dark_color=dark_color_hex, light_color=light_color_hex)
        svg_content = self._assert_is_valid_bytesio_output(result, decode_as_text=True, content_type_for_debug="text_svg")

        self.assertTrue("<svg" in svg_content.strip()[:100], "SVG content should contain '<svg' near the beginning")

        # Check for module and background colors in the svg tag
        self.assertIn(f'module_color="{dark_color_hex}"', svg_content)
        if light_color_hex.lower() not in ['transparent', 'none']:
            self.assertIn(f'background="{light_color_hex}"', svg_content)


    def test_generate_text_txt(self):
        result = generate_qr_code("Hello ASCII", content_type='text', output_format='txt', border=1)
        txt_content = self._assert_is_valid_bytesio_output(result, decode_as_text=True, content_type_for_debug="text_txt")
        self.assertTrue(len(txt_content) > 0)
        self.assertTrue("█" in txt_content or " " in txt_content or "#" in txt_content)

    def test_generate_wifi_qr(self):
        result = generate_qr_code(
            data=None, content_type='wifi', output_format='png',
            wifi_ssid="MyNetwork", wifi_password="MyPassword123", wifi_security="WPA"
        )
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="wifi_qr")

    def test_generate_vcard_qr(self):
        vcard_params = {"firstname": "Jane", "lastname": "Doe", "email": "jane@example.com", "displayname":"Jane Doe"}
        result = generate_qr_code(data=None, content_type='vcard', vcard_params=vcard_params, output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="vcard_qr")

    def test_generate_mecard_qr(self):
        mecard_params = {"firstname": "John", "lastname": "Smith", "phone": "12345"}
        result = generate_qr_code(data=None, content_type='mecard', mecard_params=mecard_params, output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="mecard_qr")

    def test_generate_email_qr(self):
        result = generate_qr_code(data=None, content_type='email', email_to="recipient@example.com", email_subject="Test", output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="email_qr")

    def test_generate_sms_qr(self):
        result = generate_qr_code(data=None, content_type='sms', sms_to="1234567890", sms_body="Hello!", output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="sms_qr")

    def test_generate_tel_qr(self):
        result = generate_qr_code(data=None, content_type='tel', tel_number="1234567890", output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="tel_qr")

    def test_generate_geo_qr(self):
        result = generate_qr_code(data=None, content_type='geo', geo_latitude="40.7128", geo_longitude="-74.0060", output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="geo_qr")

    def test_generate_event_qr(self):
        result = generate_qr_code(data=None, content_type='event',
                                  event_summary="Planning Meeting",
                                  event_start="20240101T100000", event_end="20240101T110000",
                                  output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="event_qr")

    def test_generate_epc_qr(self):
        result = generate_qr_code(data=None, content_type='epc',
                                  epc_name="Test Merchant", epc_iban="DE123456789", epc_amount="10.99",
                                  output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="epc_qr")

    def test_error_correction_levels(self):
        for error_level_char in ['L', 'M', 'Q', 'H']:
            with self.subTest(level=error_level_char):
                result = generate_qr_code("test error levels", content_type='text', error=error_level_char, output_format='png')
                self._assert_is_valid_bytesio_output(result, content_type_for_debug=f"err_level_{error_level_char}")

    def test_transparent_background_png(self):
        result = generate_qr_code("transparent BG", content_type='text', light_color='transparent', output_format='png')
        self._assert_is_valid_bytesio_output(result, content_type_for_debug="transparent_png")

    def test_transparent_background_svg(self):
        result = generate_qr_code("transparent BG SVG", content_type='text', light_color='transparent', output_format='svg')
        svg_content = self._assert_is_valid_bytesio_output(result, decode_as_text=True, content_type_for_debug="transparent_svg")
        self.assertTrue("<svg" in svg_content.strip()[:100], "SVG content should contain '<svg' near the beginning")
        # Con back_color="transparent", SvgPathImage no debería definir un background_color sólido en el tag <svg>
        # o un <rect> de fondo con fill sólido.
        self.assertNotIn('background_color="#ffffff"', svg_content.lower())
        self.assertNotIn('fill="white"', svg_content.lower()) # Asegurar que no haya un rect blanco de fondo


    def test_empty_data_string_for_url_or_text(self):
        with self.assertRaisesRegex(ValueError, "El contenido a codificar no puede ser vacío."):
            generate_qr_code(data="", content_type='url', output_format='png')
        with self.assertRaisesRegex(ValueError, "El contenido a codificar no puede ser vacío."):
            generate_qr_code(data="  ", content_type='text', output_format='png')

    def test_insufficient_data_for_structured_types(self):
        with self.assertRaisesRegex(ValueError, "SSID no puede ser vacío para WiFi QR."):
            generate_qr_code(data=None, content_type='wifi', wifi_ssid=None, output_format='png')
        with self.assertRaisesRegex(ValueError, "vCard requiere FN \(displayname o firstname/lastname\)."):
            generate_qr_code(data=None, content_type='vcard', vcard_params={}, output_format='png')
        with self.assertRaisesRegex(ValueError, "MeCard requiere 'name' \(o firstname/lastname\)."):
            generate_qr_code(data=None, content_type='mecard', mecard_params={}, output_format='png')
        with self.assertRaisesRegex(ValueError, "Email 'to' no puede ser vacío."):
            generate_qr_code(data=None, content_type='email', email_to=None, output_format='png')
        with self.assertRaisesRegex(ValueError, "Evento requiere summary, dtstart y dtend."):
            generate_qr_code(data=None, content_type='event', event_summary=None, event_start=None, event_end=None, output_format='png')
        with self.assertRaisesRegex(ValueError, "EPC requiere name, iban y amount."):
            generate_qr_code(data=None, content_type='epc', epc_name=None, output_format='png')

    def test_unsupported_output_format_html(self):
        with self.assertRaises(NotImplementedError):
            generate_qr_code("test html", content_type='text', output_format='html')

    # Pruebas para las funciones de construcción de string (más directas)
    def test_construir_vcard_string_minimal(self):
        vcard_str = construir_vcard_string(firstname="Test", lastname="User")
        self.assertIn("FN:Test User", vcard_str)
        self.assertIn("N:User;Test", vcard_str)
        vcard_str_disp = construir_vcard_string(displayname="Display Only")
        self.assertIn("FN:Display Only", vcard_str_disp)


    def test_construir_mecard_string_minimal(self):
        mecard_str = construir_mecard_string(firstname="Test", lastname="User")
        self.assertIn("N:User,Test;", mecard_str)
        mecard_str_name = construir_mecard_string(name="OnlyName")
        self.assertIn("N:OnlyName;", mecard_str_name)

if __name__ == '__main__':
    unittest.main()
