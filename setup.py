from setuptools import find_packages, setup


setup(
    name="spacex-twitter-bot",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "joblib>=1.3",
        "pandas>=2.0",
        "python-dotenv>=1.0",
        "requests>=2.31",
        "scikit-learn>=1.4",
        "tweepy>=4.14",
    ],
    python_requires=">=3.9",
)

