from distutils.core import setup

setup(
    name='Python Weather Observations',
    version='0.2',
    description='NOAA XML weather observations interface for python',
    long_description="",
    author="Justin Quick",
    author_email='justquick@gmail.com',
    url='http://code.google.com/p/python-weather/',
    packages=['Weather','Weather.data'],
    package_data={'Weather':['data/*.csv']},
#    scripts=['bin/runwsgi.py','bin/cronjob.py','bin/runcgi.py'],
)
