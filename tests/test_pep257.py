import glob
import pep257


def test_pep257():
    filenames = glob.glob('./economicpy/*.py')
    result = pep257.check(filenames, ['D100'])
    for r in result:
        print(r)
