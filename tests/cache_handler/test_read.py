from checker_plus.cache_handler import CSV


def test_read():
    proc_file = CSV(r'C:\Users\Владимир\PycharmProjects\Checker-Plus-v2\processing\process.csv')
    print(proc_file.read())


test_read()
