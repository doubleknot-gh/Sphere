"""Integration checks against a disposable DB, never the project's member DB."""
import io
import os
import tempfile
import unittest

TEMP = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = 'sqlite:///' + TEMP.name.replace('\\', '/') + '/web-test.db'
os.environ['SECRET_KEY'] = 'isolated-test-key'

from fastapi.testclient import TestClient
from openpyxl import Workbook
import database
import models
from main import app, get_password_hash, create_access_token


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = get_password_hash('test-password')
        cls.client = TestClient(app)

    def setUp(self):
        with database.SessionLocal() as session:
            for model in [models.ChatMessage, models.Notice, models.Member]:
                session.query(model).delete()
            session.add_all([
                models.Member(student_id='admin-test', name='관리자', club='운영', password=self.password, role='admin'),
                models.Member(student_id='member-test', name='회원', club='동아리', password=self.password, role='member'),
            ])
            session.commit()
        self.admin = {'Authorization': 'Bearer ' + create_access_token({'sub': 'admin-test'})}
        self.member = {'Authorization': 'Bearer ' + create_access_token({'sub': 'member-test'})}

    def test_frontend_and_auth(self):
        self.assertIn('회원 로그인', self.client.get('/').text)
        for path in ['/assets/site.js', '/assets/site.css', '/assets/logo.png', '/assets/ku-logo.png', '/health']:
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get('/assets/../database.py').status_code, 404)
        self.assertEqual(self.client.get('/members/me').status_code, 401)
        login = self.client.post('/token', data={'username': 'member-test', 'password': 'test-password'})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get('/members/me', headers=self.member).json()['student_id'], 'member-test')
        self.assertEqual(self.client.get('/admin/members', headers=self.member).status_code, 403)
        self.assertEqual(self.client.post('/token', data={'username': 'member-test', 'password': 'wrong'}).status_code, 401)

    def test_mapped_excel_import_and_member_login(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['동아리', '학번', '성명'])
        sheet.append(['테니스', '00123', '새회원'])
        sheet.append(['음악', '00123', '새회원'])
        stream = io.BytesIO()
        workbook.save(stream)
        files = {'file': ('members.xlsx', stream.getvalue())}
        preview = self.client.post('/admin/import-preview', files=files, headers=self.admin)
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json()['count'], 2)
        self.assertEqual(preview.json()['rows'][0][1], '00123')
        data = {'name_column': 2, 'sid_column': 1, 'club_column': 0, 'has_header': 'true'}
        response = self.client.post('/admin/import-members', files=files, data=data, headers=self.admin)
        self.assertEqual(response.status_code, 200, response.text)
        login = self.client.post('/token', data={'username': '00123', 'password': '1234'})
        self.assertEqual(login.status_code, 200)
        result = self.client.get('/members/me', headers={'Authorization': 'Bearer ' + login.json()['access_token']}).json()
        self.assertEqual(result['club'], '테니스, 音楽'.replace('音楽', '음악'))
        self.assertEqual(result['role'], 'member')
        self.assertEqual(self.client.post('/admin/import-preview', files=files, headers=self.member).status_code, 403)

    def test_import_validation_and_legacy_csv(self):
        files = {'file': ('members.csv', '학번,소속,이름\n00234,연극,회원2'.encode('cp949'))}
        data = {'name_column': 2, 'sid_column': 0, 'club_column': 1, 'has_header': 'true'}
        self.assertEqual(self.client.post('/admin/import-members', files=files, data=data, headers=self.admin).status_code, 200)
        data['name_column'] = 0
        self.assertEqual(self.client.post('/admin/import-members', files=files, data=data, headers=self.admin).status_code, 400)
        self.assertEqual(self.client.post('/admin/import-preview', files={'file': ('bad.xlsx', b'bad')}, headers=self.admin).status_code, 400)
        response = self.client.post('/admin/upload-csv', files={'file': ('old.csv', '기존형식,00345,체육'.encode())}, headers=self.admin)
        self.assertEqual(response.status_code, 200)

    def test_notice_chat_permissions_and_persistence(self):
        self.assertEqual(self.client.put('/admin/notice', json={'content': '새 공지'}, headers=self.member).status_code, 403)
        self.assertEqual(self.client.put('/admin/notice', json={'content': '새 공지'}, headers=self.admin).status_code, 200)
        # Different client reads the same persisted DB record.
        with TestClient(app) as second:
            self.assertEqual(second.get('/notice', headers=self.member).json()['content'], '새 공지')
        self.assertEqual(self.client.get('/notice').status_code, 401)
        self.client.post('/messages', json={'message': '<script>hello</script>'}, headers=self.admin)
        message = self.client.get('/messages', headers=self.member).json()[0]
        self.assertFalse(message['can_delete'])
        self.assertNotIn('student_id', message)
        self.assertEqual(self.client.delete('/messages/' + str(message['id']), headers=self.member).status_code, 403)
        self.assertEqual(self.client.delete('/messages/' + str(message['id']), headers=self.admin).status_code, 200)
        self.assertEqual(self.client.post('/messages', json={'message': '  '}, headers=self.member).status_code, 400)

    def test_password_change_and_admin_edits(self):
        self.assertEqual(self.client.put('/members/me/password', json={'current_password': 'test-password', 'new_password': 'new-password'}, headers=self.member).status_code, 200)
        self.assertEqual(self.client.post('/token', data={'username': 'member-test', 'password': 'new-password'}).status_code, 200)
        for field, value in [('club', '변경동아리'), ('status', 'inactive'), ('role', 'member')]:
            response = self.client.patch('/admin/members/member-test/' + field, params={field: value}, headers=self.admin)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/members/me', headers=self.member).json()['status'], 'inactive')
        self.assertEqual(self.client.patch('/admin/members/member-test/reset-password', headers=self.admin).status_code, 200)
        self.assertEqual(self.client.delete('/admin/members/member-test', headers=self.admin).status_code, 200)
        self.assertEqual(self.client.get('/members/me', headers=self.member).status_code, 401)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        database.engine.dispose()
        TEMP.cleanup()


if __name__ == '__main__':
    unittest.main()
