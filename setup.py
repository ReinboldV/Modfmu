from setuptools import setup
setup(
    name='modfmu',
    version=0.1,
    description='Library for FMU translation of modelica models',
    author='Vincent Reinbold',
    author_email='vincent.reinbold@gmail.com',
    license='GNU GENERAL PUBLIC LICENSE',
    packages=['modfmu'],
    install_requires=['matplotlib', 'numpy', 'pandas', 'buildingspy'],
    classifiers=[	"Programming Language :: Python :: 3.5",
					"Programming Language :: Python :: 3.6"])
