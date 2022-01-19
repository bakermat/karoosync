import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='karoosync',
    version='1.3.0',
    description='Syncs workouts from intervals.icu to Hammerhead Karoo',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/bakermat/karoosync',
    author='Bakermat',
    author_email='',
    license='MIT',
    py_modules=['karoosync'],
    install_requires=[
        'requests>=2.26',
        'PyJWT',
        'bs4',
        'lxml'
    ],
    entry_points={
        'console_scripts': [
            'karoosync=karoosync:main',
        ],
    },
)
