# This file explicitly collects and runs tests from the web_api_tests/ directory.

# Import test modules from the web_api_tests directory
from tests.regression.web_api_tests import (
    test_01_server_management,
    test_02_database_operations,
    test_03_document_operations,
    test_04_search_operations,
    test_05_job_management,
)

# Pytest will discover tests within the imported modules.
# No additional code is needed in this file for collection.