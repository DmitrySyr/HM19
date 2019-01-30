import unittest
import poker

class TestPoker(unittest.TestCase):

    def test_flush(self):
        self.assertFalse(poker.flush("6C 7C 8C 9C TC 5C JS".split()))
        self.assertTrue(poker.flush("6C 7C 8C 9C TC 5C JC".split()))
        self.assertFalse(poker.flush("6C 7C 8C 9C TC 5C TF".split()))
        
    def test_card_ranks(self):
        self.assertTrue(poker.card_ranks("6C 7C 8C 9C TC 5C JS".split()) == 
                             sorted([6,7,8,9,10,5,11], reverse=True))
        self.assertTrue(poker.card_ranks("TD TC TH 7C 7D 8C 8S".split()) ==
                             sorted([10,10,10,7,7,8,8], reverse=True))
        self.assertTrue(poker.card_ranks("JD TC TH 7C 7D 7S 7H".split()) ==
                        sorted([11, 10, 10, 7, 7, 7, 7], reverse=True))
        self.assertFalse(poker.card_ranks("JD TC TH 7C 7D 7S 7H".split()) ==
                         sorted([11,10,10,7,7,7,6], reverse=True))
        self.assertFalse(poker.card_ranks("JD TC TH 7C 7D 7S 7H".split()) ==
                         sorted([11,10,10,7,15,7,7], reverse=True))
        
        self.assertTrue(poker.card_ranks("6C 9C 8C QC TC AC KS".split()) == 
                             [14, 13, 12, 10, 9, 8, 6])
        self.assertTrue(poker.card_ranks("JD TC QH 7C 2D 3S 5H".split()) == 
                             [12, 11, 10, 7, 5, 3, 2])        
        
    def test_kind(self):
        self.assertTrue(poker.kind(3, poker.card_ranks("6C 7C 8C 9C TC".split())) == None)
        self.assertTrue(poker.kind(4, poker.card_ranks("JD 7C 7D 7S 7H".split())) == 7)
        self.assertTrue(poker.kind(3, poker.card_ranks("JD TC 7H 7C 7D".split())) == 7)
        self.assertTrue(poker.kind(3, poker.card_ranks("JD TC TH 7C 7D".split())) == None)
        self.assertTrue(poker.kind(3, poker.card_ranks("TD TC TH 7C 7D".split())) == 10)
    
    def test_stright(self):
        self.assertTrue(poker.straight(poker.card_ranks("6C 7C 8C 9C TC".split())) == True)
        self.assertTrue(poker.straight(poker.card_ranks("JD 7C 7D 7S 7H".split())) == False)
        self.assertTrue(poker.straight(poker.card_ranks("JD TC 7H 6C 5D".split())) == False)
        self.assertTrue(poker.straight(poker.card_ranks("JD TC TH 7C 7D".split())) == False)
        self.assertTrue(poker.straight(poker.card_ranks("AC KC TH JC QD".split())) == True) 
        self.assertTrue(poker.straight(poker.card_ranks("7C 8C 9C TC AC".split())) == False) 
        
    def test_two_pair(self):
        self.assertTrue(poker.two_pair(poker.card_ranks("6C 7C 8C 9C TC".split())) == None)
        self.assertTrue(poker.two_pair(poker.card_ranks("JD 7C 7D 8S 8H".split())) == (8, 7))
        self.assertTrue(poker.two_pair(poker.card_ranks("JD TC 7H JC TD".split())) == (11, 10))
        self.assertTrue(poker.two_pair(poker.card_ranks("JD TC TH 7C 7D".split())) == (10, 7))
        self.assertTrue(poker.two_pair(poker.card_ranks("AC KC TH JC QD".split())) == None) 
        self.assertTrue(poker.two_pair(poker.card_ranks("AC AD TH QC QD".split())) == (14, 12))
        
    #def test_isupper(self):
        #self.assertTrue('FOO'.isupper())
        #self.assertFalse('Foo'.isupper())

    #def test_split(self):
        #s = 'hello world'
        #self.assertEqual(s.split(), ['hello', 'world'])
        ## check that s.split fails when the separator is not a string
        #with self.assertRaises(TypeError):
            #s.split(2)

if __name__ == '__main__':
    unittest.main()