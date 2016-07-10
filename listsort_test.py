import os
import listsort
import unittest
import tempfile

class ListsortTestCase(unittest.TestCase):

    def setUp(self):
        self.greylist_fd, listsort.app.config['GREYLISTFILE'] = tempfile.mkstemp()
        self.app = listsort.app.test_client()

    def tearDown(self):
        os.close(self.greylist_fd)
        os.unlink(listsort.app.config['GREYLISTFILE'])

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

    def test_greylist_writeread(self):
        listsort.save_greylist(['foo.bar','bar.foo'])
        rv = listsort.load_greylist()
        assert rv == ['bar.foo','foo.bar']

    def test_greylist_cleandomainadd(self):
        listsort.save_greylist(['foo.bar','bar.foo'])
        listsort.domain_to_list('example.com','grey')
        rv = listsort.load_greylist()
        assert rv == ['bar.foo','example.com','foo.bar']

    def test_greylist_mailadd(self):
        listsort.save_greylist(['foo.bar','bar.foo'])
        listsort.domain_to_list('foo@example.com','grey')
        rv = listsort.load_greylist()
        assert rv == ['bar.foo','example.com','foo.bar']

if __name__ == '__main__':
    unittest.main()

