from io import open
import os
import re
import six
from shutil import make_archive, unpack_archive, copytree
from base64 import encodebytes, decodebytes


PORT_INC_REGEX = '.*:[0-9]{1,5}$'

# The XML-RPC library may return a string as a str even though it was a unicode on the sending side.
# We're using UTF-8 file encodings as standard so need to make sure that we're using unicode strings (only an issue in
# Python 2)
if six.PY3:
    unicode = str  # pylint: disable=invalid-name


def read_file_from_disk(path, encoding='utf-8', into_lines=False):
    """
    Utility function to read and return a file from disk

    :param path: Path to the file to read
    :type path: str
    :param encoding: Encoding of the file
    :type encoding: str
    :param into_lines: Whether or not to return a list of lines
    :type into_lines: bool

    :return: Contents of the file
    :rtype: str
    """
    with open(path, 'r', encoding=encoding) as file_handle:
        return file_handle.readlines() if into_lines else file_handle.read()


def read_binary_from_disk(path, into_lines=False):
    """
    Utility function to read and return a binary from disk

    :param path: Path to the file to read
    :type path: str
    :param into_lines: Whether or not to return a list of lines
    :type into_lines: bool

    :return: Contents of the file
    :rtype: str, Base64 encoded.
    """
    filename    = os.path.basename(os.path.normpath(path))
    father_path = os.path.normpath(path).rstrip(f'{filename}')
    zipfile = make_archive(f'{filename}', 'zip', root_dir=f'{father_path}', base_dir=f'{filename}')
    with open(zipfile, 'rb') as file_handle:
        ret =  file_handle.readlines() if into_lines else encodebytes(file_handle.read()).decode()
        os.remove(zipfile)
        return ret

def write_file_to_disk(path, file_contents, encoding='utf-8'):
    """
    Utility function to write a file to disk

    :param path: Path to write to
    :type path: str
    :param file_contents: Contents of the file
    :type file_contents: str | unicode
    :param encoding: Encoding of the file
    :type encoding: str
    """
    with open(path, 'w', encoding=encoding) as file_handle:
        file_handle.write(unicode(file_contents))


def write_binary_to_disk(path, file_contents):
    """
    Utility function to write a binary to disk

    :param path: Path to write to
    :type path: str
    :param file_contents: Contents of the file
    :type file_contents: str | unicode
    """
    with open(path+'.zip', 'wb') as file_handle:
        file_handle.write(decodebytes(file_contents.encode()))
    unpack_archive(path+'.zip', format='zip')

def normalize_xmlrpc_address(address, default_port):
    """
    Normalises the server address by pre-pending with http:// if missing and appending :default_port if missing

    :param address: Address to normalise
    :type address: str
    :param default_port: Default port to append if missing
    :type default_port: int

    :return: Normalised address
    :rtype: str
    """
    if not re.match(re.compile(PORT_INC_REGEX), address):
        address = '{}:{}'.format(address, default_port)
    if not address.lower().startswith('http'):
        address = 'http://{}'.format(address)
    return address


def calculate_ts_parent_path(suite):
    """
    Parses up a test suite's ancestry and builds up a file path. This will then be used to create the correct test
    suite hierarchy on the remote host

    :param suite: test suite to parse the ancestry for
    :type suite: robot.running.model.TestSuite

    :return: file path of where the given suite is relative to the root test suite
    :rtype: str
    """
    family_tree = []

    if not suite.parent:
        return ''
    current_suite = suite.parent
    while current_suite:
        family_tree.append(current_suite.name)
        current_suite = current_suite.parent

    # Stick with unix style slashes for consistency
    return os.path.join(*reversed(family_tree)).replace('\\', '/')
