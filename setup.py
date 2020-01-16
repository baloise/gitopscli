from setuptools import setup
setup(
    name = 'gitopscli',
    version = '0.1.0',
    packages = ['gitopscli'],
    entry_points = {
        'console_scripts': [
            'gitopscli = gitopscli.__main__:main'
        ]
    })