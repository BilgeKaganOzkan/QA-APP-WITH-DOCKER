import os

log_file_dir = "./.log"
temp_database_file_dir = "./.temp_databases"
vector_stores_file_dir = "./.vector_stores"

if not os.path.exists(log_file_dir):
    os.mkdir(log_file_dir)

if not os.path.exists(temp_database_file_dir):
    os.mkdir(temp_database_file_dir)

if not os.path.exists(vector_stores_file_dir):
    os.mkdir(vector_stores_file_dir)