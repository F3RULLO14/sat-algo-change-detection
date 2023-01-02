from setuptools import find_packages, setup

setup(
    name='change-detection',
    author='Andrew Ferullo',
    author_email='f3rullo14@gmail.com',
    version='0.1.0',
    description='Evaluate differences between SAR geotifs.',
    license='MIT',
    packages=find_packages(where='changedetect'),
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'numpy>=1.23.4',
        'GDAL>=3.4.3',
        'rasterio>=1.2.10'
    ],
)