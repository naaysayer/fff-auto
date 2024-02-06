from setuptools import setup

setup(
    name='fffauto',
    version='1.0.0',
    url='https://github.com/naaysayer/fff-auto',
    py_modules=['fffauto'],
    packages=['fffauto'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'fffauto = fffauto.fffauto:main',
        ],

    }
)
