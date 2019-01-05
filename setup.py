from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='hdlcomposer',
    version='0.32',
    description='HDL simulation and autoverification made agile',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
    keywords='VHDL Verilog simulation verification parse hierarchy',
    url='https://github.com/bmpenuelas/hdlcomposer',
    author='Borja Penuelas',
    author_email='bmpenuelas@gmail.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'vcdvcd',
    ],
    scripts=[
        'bin/ghdl_cli/ghdl_cli',
    ],
    entry_points={
        'console_scripts': [
        ]
    },
    zip_safe=False
)
