import unittest
import os
from app import app, db, TrackableQR # Asegúrate de que TrackableQR se pueda importar
import tempfile
from urllib.parse import urlparse, parse_qs

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + self.test_db_path
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # Deshabilitar CSRF para pruebas de formulario si se usa Flask-WTF
        app.config['SERVER_NAME'] = 'localhost:5000' # Necesario para url_for con _external=True
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Generador de C\xc3\xb3digos QR Avanzado', response.data)

    def test_generate_simple_url_qr(self):
        response = self.app.post('/generate', data={
            'content_type': 'url',
            'data_url': 'https://example.com',
            'error_correction': 'M',
            'scale': '10',
            'border': '4',
            'dark_color': '#000000',
            'light_color': '#ffffff',
            'output_format': 'png'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')

    def test_generate_trackable_url_qr(self):
        with app.app_context(): # Necesario para url_for y operaciones de BD
            original_url = 'https://trackme.example.com'
            response = self.app.post('/generate', data={
                'content_type': 'url',
                'data_url': original_url,
                'enable_tracking': 'on',
                'error_correction': 'M',
                'scale': '10',
                'border': '4',
                'dark_color': '#000000',
                'light_color': '#ffffff',
                'output_format': 'png'
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'image/png')

            # Verificar que se creó un registro en la BD
            qr_record = TrackableQR.query.filter_by(original_url=original_url).first()
            self.assertIsNotNone(qr_record)
            self.assertEqual(qr_record.visit_count, 0)
            self.assertIsNotNone(qr_record.short_code)

            # No podemos verificar el contenido del QR directamente aquí fácilmente,
            # pero la lógica asume que la URL de seguimiento se usó.

    def test_qr_tracking_redirect_and_count(self):
         with app.app_context():
            original_url = 'https://test-redirect.com'
            # Crear manualmente un QR rastreable para la prueba
            short_code = "test01"
            new_qr = TrackableQR(original_url=original_url, short_code=short_code, visit_count=0)
            db.session.add(new_qr)
            db.session.commit()

            # Primera visita
            tracking_url = f'/track/{short_code}'
            response = self.app.get(tracking_url, follow_redirects=False) # No seguir el redirect para ver el status 302
            self.assertEqual(response.status_code, 302) # Espera una redirección
            self.assertEqual(response.location, original_url)

            qr_record = TrackableQR.query.filter_by(short_code=short_code).first()
            self.assertEqual(qr_record.visit_count, 1)

            # Segunda visita
            response = self.app.get(tracking_url, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            qr_record_after_second_visit = TrackableQR.query.filter_by(short_code=short_code).first()
            self.assertEqual(qr_record_after_second_visit.visit_count, 2)

    def test_tracking_nonexistent_qr(self):
        response = self.app.get('/track/nonexistentcode', follow_redirects=False)
        self.assertEqual(response.status_code, 404)


    def test_stats_page_empty(self):
        response = self.app.get('/stats')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No hay c\xc3\xb3digos QR rastreables generados todav\xc3\xada.', response.data)

    def test_stats_page_with_data(self):
        with app.app_context():
            qr1 = TrackableQR(original_url='https://example.com/stats1', short_code='stat01', visit_count=5)
            qr2 = TrackableQR(original_url='https://example.com/stats2', short_code='stat02', visit_count=10)
            db.session.add_all([qr1, qr2])
            db.session.commit()

            response = self.app.get('/stats')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'stat01', response.data)
            self.assertIn(b'https://example.com/stats1', response.data)
            self.assertIn(b'5', response.data)
            self.assertIn(b'stat02', response.data)
            self.assertIn(b'https://example.com/stats2', response.data)
            self.assertIn(b'10', response.data)
            self.assertNotIn(b'No hay c\xc3\xb3digos QR rastreables generados todav\xc3\xada.', response.data)

if __name__ == '__main__':
    unittest.main()
