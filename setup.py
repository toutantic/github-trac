from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points

setup(
    name='GithubPlugin',
    version='0.2',
    author='Paolo Capriotti',
    author_email='p.capriotti@gmail.com',
    description = "Creates an entry point for a GitHub post-commit hook.",
    license = """Unknown Status""",
    url = "http://github.com/pcapriotti/github-trac/tree/master",
    packages = find_packages(exclude=['*.tests*']),
	package_data={'github' : []},

    install_requires = [
        'simplejson>=2.0.5',
    ],
    entry_points = {
        'trac.plugins': [
            'github = github',

        ]    
    }

)
