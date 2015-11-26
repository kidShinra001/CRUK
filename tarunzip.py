__author__ = 'Jonathan'

import tarfile
tar = tarfile.open("enki-1.0.2.tar.gz")
tar.extractall()
tar.close()
