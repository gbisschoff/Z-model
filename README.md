# Z-Model

A simple IFRS 9 and Stress Testing Credit Risk Model.

## Getting Started
### Requirements:
1. Install [Git](https://git-scm.com/download/win).
    During setup ensure the following options are selected:
    - **Select Components**: ensure "Windows Explorer integration" is selected.
	- **Choosing the SSH executable**: select "Use OpenSSH".  This option may not be displayed.  
	- **Configuring the line endings conventions**: select "Checkout as-is, commit Unix-style line endings".

2. Install [Python](https://www.python.org/downloads/windows/).
3. Install [PyCharm](https://www.jetbrains.com/pycharm/download/#section=windows) or any other IDE of your choice.
4. Install [C++ Build Tools](https://wiki.python.org/moin/WindowsCompilers), it is required by packages like Numpy that use Cython.
5. If you are working from behind a proxy make sure to set the `HTTP_PROXY` and `HTTPS_PROXY` environment variables using the following format:
    `http://{username}:{password}@{proxy}:{port}`
6. Create a [`pip.ini`](./pip.ini) file in you Home/User directory 

### How to install the Z-model package:
0. Open Git Bash (Right click in a folder and select `Git Bash Here`)
1. Create working directory `mkdir Z-model`
2. Change directory into Z-model `cd Z-model`
3. Inside the directory create a virtual environment to store all your packages `py -m venv .venv`
4. Activate the virtual environment `source .venv/Scripts/activate`
5. Upgrade pip and setuptools `py -m pip install --upgrade pip setuptools`
6. Install dependencies `pip install wheel pyscaffold`
7. Install Z-model's dependencies `pip install --trusted-host raw.githubusercontent.com -r https://raw.githubusercontent.com/gbisschoff/Z-model/main/requirements.txt`
8. Install the Z-model `pip install git+https://github.com/gbisschoff/Z-model.git`
8. You are ready to use the Z-model by using `import z_model` in Python

## FAQ
TODO: Update section with common questions and answers
