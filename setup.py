import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()


setup(name='icc.cellula',
      version=0.1,
      description='icc.cellula',
      long_description=README,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pylons",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
      ],
      keywords="web services",
      author='',
      author_email='',
      url='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'rdflib',
        'rdflib-jsonld',
	'pyramid',
	'waitress==0.8.11dev0ipv6-1',
	'cornice',
	'icc.rdfservice==0.1',
	'icc.restfuldocs==0.0.1',
	'pyramid_debugtoolbar',
	'pyramid_chameleon',
	'Babel',
	'lingua',
	'passlib',
	'bcrypt',
    'pyramid_mailer',
        ],
      dependency_links = [
        'https://github.com/eugeneai/rdflib-kyotocabinet/archive/master.zip#egg=rdflib-kyotocabinet-0.1',
        'https://github.com/eugeneai/waitress/archive/0.8.11dev0ipv6-1.zip#egg=waitress-0.8.11dev0ipv6-1',
        'https://github.com/mozilla-services/cornice/archive/master.zip#egg=cornice-1.2.0.dev0',

        'https://github.com/eugeneai/icc.restfuldocs/archive/master.zip#egg=icc.restfuldocs-0.0.1',
        'https://github.com/eugeneai/icc.rdfservice/archive/master.zip#egg=icc.rdfservice-0.1',
        ],
      package_dir = {'': 'src'},
      entry_points = """\
      [paste.app_factory]
      main=icc.cellula.app:main
      """,
#    message_extractors = {
#        'src/icc/cellula': [
#            ('**.py',                'python', None),
#            ('**/templates/**.pt',   'xml', None),
#        ],
#    },
)
