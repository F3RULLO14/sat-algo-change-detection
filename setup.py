from setuptools import find_packages, setup

setup(
    name='change-detection',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    version='0.0.1',
    description='Change Detection Algorithm',
    author='Andrew Ferullo',
    license='MIT',
    python_requires='>=3.6',
    # Version of software used on local machine
    install_requires=[
        'numpy>=1.23.4',
        'GDAL>=3.4.3',
        'rasterio>=1.2.10'
    ],
)