import unittest
from coin import Blockchain

class TestBlockchain(unittest.TestCase):
    def setUp(self):
        self.blockchain = Blockchain()

    def test_create_genesis_block(self):
        self.assertEqual(len(self.blockchain.chain), 1)
        self.assertEqual(len(self.blockchain.pending_transactions), 0)

    # Add more test cases as needed

if __name__ == '__main__':
    unittest.main()
