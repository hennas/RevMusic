from setuptools import find_packages, setup

setup(
    name='revmusic',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
        'flask_restful',
        'SQLAlchemy',
        'jsonschema',
        'click'
    ]
)
