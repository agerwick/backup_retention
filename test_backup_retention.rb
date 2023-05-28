import os
import shutil
from datetime import datetime
from backup_retention import get_matching_files, generate_regex_pattern, get_file_datetime

def test_get_matching_files(tmpdir):
    # Create test files
    file1 = os.path.join(tmpdir, "data_20230520.txt")
    file2 = os.path.join(tmpdir, "data_20230521.txt")
    file3 = os.path.join(tmpdir, "data_20230522.txt")
    file4 = os.path.join(tmpdir, "other.txt")
    open(file1, 'w').close()
    open(file2, 'w').close()
    open(file3, 'w').close()
    open(file4, 'w').close()

    # Test get_matching_files
    directory = str(tmpdir)
    file_format = "data_{YYYY}{MM}{DD}.txt"
    matching_files = get_matching_files(directory, file_format)

    assert len(matching_files) == 3
    assert file1 in matching_files
    assert file2 in matching_files
    assert file3 in matching_files
    assert file4 not in matching_files

def test_generate_regex_pattern():
    file_format = "file_*.txt"
    regex_pattern = generate_regex_pattern(file_format)
    assert regex_pattern == r"^file_\w*\.txt$"

    file_format = "{YYYY}{MM}{DD}T{hh}{mm}"
    regex_pattern = generate_regex_pattern(file_format)
    assert regex_pattern == r"^(?P<YYYY>\d{4})(?P<MM>\d{2})(?P<DD>\d{2})T(?P<hh>\d{2})(?P<mm>\d{2})$"

def test_get_file_datetime():
    file_path = "/path/to/file_20220523T0830.txt"
    file_format = "file_{YYYY}{MM}{DD}T{hh}{mm}.txt"
    file_datetime = get_file_datetime(file_path, file_format)

    assert file_datetime == datetime(2022, 5, 23, 8, 30)
