import unittest
import subprocess
import re


def find_str(output, pattern):
    m = re.search(pattern, output)
    return True if m else False


class TestREST(unittest.TestCase):
    def setUp(self) -> None:
        self.api_addr = 'http://0.0.0.0:8000/'

    def test_transaction(self):
        qp = 'min_date=2020-01-01&max_date=2022-12-31'
        urls = [
            ('transaction/transactions.api', 'HTTP 200 OK'),
            ('transaction/transactions.json', '.*count.*'),
            ('transaction/transactions.datatables', ".*recordsTotal.*")
        ]
        for url, pattern in urls:
            cmd = ['curl', self.api_addr + url + '?' + qp]
            r = subprocess.run(cmd, capture_output=True)
            res = find_str(r.stdout.decode('utf-8'), pattern)
            self.assertTrue(res)

    def test_transaction_stat(self):
        qp = 'min_date=2023-05-01&max_date=2023-12-31'
        urls = [
            ('transaction/stat?format=api', 'HTTP 200 OK'),
            ('transaction/stat?format=json', '.*min_date.*'),
            ('transaction/stat?format=datatables', ".*min_date.*")
        ]
        for url, pattern in urls:
            cmd = ['curl', self.api_addr + url + '&' + qp]
            r = subprocess.run(cmd, capture_output=True)
            res = find_str(r.stdout.decode('utf-8'), pattern)
            self.assertTrue(res)


if __name__ == '__main__':
    unittest.main()
