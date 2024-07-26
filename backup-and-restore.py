import mysql.connector as sql
import tkinter as tk
import threading
import datetime
import shutil


#Function to connect to MySQL instance and create databases and tables (if required)
def mysql_connection(hname, uname, pwd):
    con=sql.connect(host=hname, user=uname, passwd=pwd)
    cursor=mycon.cursor()

    create_database="CREATE DATABASE IF NOT EXISTS backup_restore"

    cursor.execute(create_database)
    cursor.execute("USE backup_restore")

    create_info_table='''CREATE TABLE IF NOT EXISTS backup_info(
    "Backup_ID" int primary key auto_increment,
    "Date" datetime NOT NULL,
    "Backup_Name" varchar(255),
    "Source_Path" mediumblob NOT NULL,
    "Backup_Path" mediumblob NOT NULL,
    "Total_Size" bigint NOT NULL)'''

    create_backup_table='''CREATE TABLE IF NOT EXISTS backup_files(
    "Backup_ID" int references backup_info("Backup_ID"),
    "File_Name" blob NOT NULL,
    "File_Type" varchar(255) NOT NULL,
    "File_Size" bigint NOT NULL,
    )'''

    cursor.execute(create_info_table)
    cursor.execute(create_backup_table)
    con.commit()

