import mysql.connector as sql
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import datetime
import shutil
import os

#Defining these as global variables as they would be used across many functions
con=None
cursor=None
conn_gui=None


#Function to connect to MySQL instance and create databases and tables (if required)
def mysql_connection(hname, uname, pwd):

    global con
    global cursor
    global conn_gui

    try:
        con=sql.connect(host=hname, user=uname, passwd=pwd)
        cursor=con.cursor()

        create_database="CREATE DATABASE IF NOT EXISTS backup_restore"

        cursor.execute(create_database)
        cursor.execute("USE backup_restore")

        create_info_table='''CREATE TABLE IF NOT EXISTS backup_info(
        Backup_ID int primary key auto_increment,
        Date datetime NOT NULL,
        Backup_Name varchar(255),
        Source_Path mediumblob NOT NULL,
        Backup_Path mediumblob NOT NULL,
        Total_Size bigint NOT NULL)'''

        create_backup_table='''CREATE TABLE IF NOT EXISTS backup_files(
        Backup_ID int references backup_info(Backup_ID),
        File_Name blob NOT NULL,
        File_Type varchar(255) NOT NULL,
        File_Size bigint NOT NULL
        )'''

        cursor.execute(create_info_table)
        cursor.execute(create_backup_table)
        con.commit()

        if con.is_connected():
            messagebox.showinfo("Success", "Successfully connected to MySQL Database!\nNow you may take backups or restore from backups!")
            conn_gui.destroy()
    except:
        messagebox.showerror("Failed", "Couldn't connect to MySQL database.\nPlease Try Again!")

def connection_gui():

    global conn_gui

    conn_gui=tk.Tk()
    conn_gui.title("MySQL Connection")

    tk.Label(conn_gui, text="Host").grid(row=0)
    tk.Label(conn_gui, text="User").grid(row=1)
    tk.Label(conn_gui, text="Password").grid(row=2, padx=20)

    host_entry = tk.Entry(conn_gui)
    user_entry = tk.Entry(conn_gui)
    pwd_entry = tk.Entry(conn_gui, show='*')

    host_entry.grid(row=0, column=1, padx=20, pady=10)
    user_entry.grid(row=1, column=1, padx=20, pady=10)
    pwd_entry.grid(row=2, column=1, padx=20, pady=10)

    def collect_and_connect():
        hname=host_entry.get()
        uname=user_entry.get()
        pwd=pwd_entry.get()
        mysql_connection(hname, uname, pwd)

    conn_button=tk.Button(conn_gui, text="Connect to Database", command=collect_and_connect)
    conn_button.grid(row=4, columnspan=2, pady=15)

def backup_utility():

    global con
    
    # con will have None value if connection was never established
    # con.is_connected()==False will be True if connection was tried to be established but failed to take place for some reason
    if con is None or con.is_connected()==False:
        messagebox.showwarning("Error", "Kindly Connect to MySQL Database first!")
        connection_gui()

    else:
        backup_gui=tk.Tk()
        backup_gui.title("Backup Files")

        tk.Label(backup_gui, text="Source Path").grid(row=0)
        tk.Label(backup_gui, text="Destination Path").grid(row=1)
        tk.Label(backup_gui, text="Backup Name").grid(row=2)

        src_entry = tk.Entry(backup_gui)
        dest_entry = tk.Entry(backup_gui)
        name_entry = tk.Entry(backup_gui)

        src_entry.grid(row=0, column=1, padx=10, pady=10)
        dest_entry.grid(row=1, column=1, padx=10, pady=10)
        name_entry.grid(row=2, column=1, padx=10, pady=10)

        def browse_src_path():
            src_entry.delete(0)
            src_entry.insert(0, filedialog.askdirectory())

        def browse_dest_path():
            dest_entry.delete(0)
            dest_entry.insert(0, filedialog.askdirectory())

        src_browse = tk.Button(backup_gui, text="Browse", command=browse_src_path)
        src_browse.grid(row=0, column=2, padx=10, pady=10)

        dest_browse = tk.Button(backup_gui, text="Browse", command=browse_dest_path)
        dest_browse.grid(row=1, column=2, padx=10, pady=10)

        def backup():
            src_path = src_entry.get()
            dest_path = dest_entry.get()
            name = name_entry.get()

            if not src_path or not dest_path:
                messagebox.showerror("Error", "Source Path and Destination Path are required!")
            
            else:
                backup_time = datetime.datetime.now()


        backup_button = tk.Button(backup_gui, text="Start Backup", command=backup)
        backup_button.grid(row=4, columnspan=3, pady=10)
    

# Creating the main tKinter window
root=tk.Tk()
root.title("Backup and Restore")

# Add all the required buttons into the main window
connect_button = tk.Button(root, text="Connect To MySQL Database", command=connection_gui)
connect_button.pack(padx=30, pady=10)

backup_utility_button = tk.Button(root, text="Backup Files", command=backup_utility)
backup_utility_button.pack(padx=30, pady=10)

restore_button = tk.Button(root, text="Restore from Backup")
restore_button.pack(padx=30, pady=10)

info_button = tk.Button(root, text="Statistics")
info_button.pack(padx=30, pady=10)

root.mainloop()