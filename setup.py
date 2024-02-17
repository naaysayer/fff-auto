from setuptools import setup, find_packages

setup(
    name='fffauto',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'libclang'
    ],
    entry_points={
        'console_scripts': [
            'fffauto = fffauto.main:main',
        ],
    },
)
