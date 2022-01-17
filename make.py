from importlib.metadata import version
import PyInstaller.__main__
import os
import string
import secrets

alphabet = string.ascii_letters + string.digits + string.punctuation
password = ''.join(secrets.choice(alphabet) for i in range(16))

version = version("Z-model")
split_verion = version.split('.')
Z_MODEL_KEY = os.getenv('Z_MODEL_KEY', default=password)

file_version_info = f'''
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({split_verion[0]}, {split_verion[1]}, {split_verion[2]}, 0),
    prodvers=({split_verion[0]}, {split_verion[1]}, {split_verion[2]}, 0),
 
   # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'Deloitte LLP'),
        StringStruct('FileDescription', 'Z-Model'),
        StringStruct('FileVersion', '{version}'),
        StringStruct('InternalName', 'Z-Model'),
        StringStruct('LegalCopyright', 'Deloitte LLP. All rights reserved.'),
        StringStruct('OriginalFilename', 'Z-Model.exe'),
        StringStruct('ProductName', 'Deloitte Z-Model'),
        StringStruct('ProductVersion', '{version}')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
'''

with open('.\\build\\file_version_info.txt', 'w') as f:
    f.write(file_version_info)


PyInstaller.__main__.run([
    r'.\\src\\z_model\\__main__.py',
    r'--log-level=INFO',
    r'--noconfirm',
    r'--onefile',
    r'--clean',
    r'--noupx',
    r'--icon=.\\icon.ico',
    r'--name=Z-Model',
    f'--key={Z_MODEL_KEY}',
    r'--version-file=.\\build\\file_version_info.txt',
    r'--exclude-module=matplotlib',
    r'--exclude-module=PIL',
    r'--exclude-module=tkinter',
    r'--exclude-module=sqlite3',
    r'--exclude-module=pytest'
])
