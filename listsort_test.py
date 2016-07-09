import os
import listsort
import unittest
import tempfile

class ListsortTestCase(unittest.TestCase):

    def setUp(self):
        self.app = listsort.app.test_client()

    def tearDown(self):
        pass

    def test_add_empty_domain_to_list(self):
        rv = listsort.domain_to_list('','bu')
        assert rv == False

    def test_sanitize_mail(self):
        rv = listsort.sanitize_entry('name@foo.bar')
        assert rv == 'foo.bar'

    def test_sanitize_utf8_mail(self):
        rv = listsort.sanitize_entry(u'name@fo\xc3.bar')
        assert rv == 'fo.bar'

    def test_sanitize_domain(self):
        rv = listsort.sanitize_entry('foo.bar')
        assert rv == 'foo.bar'


if __name__ == '__main__':
    unittest.main()

