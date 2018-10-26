from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='ghdl_tools',
    version='0.2',
    description='Effortless GHDL simulation automation, VHDL architecture parsing, object-oriented representation and more tools to accelerate HDL development.',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
    keywords='VHDL GHDL simulation parse hierarchy',
    url='',
    author='Borja Penuelas.',
    author_email='bmpenuelas@gmail.com',
    license='MIT',
    packages=[
    ],
    include_package_data=True,
    install_requires=[
    ],
    scripts=[
        'bin/ghdl_tools_cli',
    ],
    entry_points={
        'console_scripts': [
        ]
    },
    zip_safe=False
)