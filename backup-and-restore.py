import mysql.connector as sql
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import datetime
import shutil
import os
import matplotlib.pyplot as plt

# Defining these as global variables as they would be used across many functions
con = None
cursor = None
conn_gui = None

# Function to connect to MySQL instance and create databases and tables (if required)
def mysql_connection(hname, uname, pwd):
    global con, cursor, conn_gui

    try:
        con = sql.connect(host=hname, user=uname, passwd=pwd)
        cursor = con.cursor()

        create_database = "CREATE DATABASE IF NOT EXISTS backup_restore"
        cursor.execute(create_database)
        cursor.execute("USE backup_restore")

        create_info_table = '''CREATE TABLE IF NOT EXISTS backup_info(
        Backup_ID int primary key auto_increment,
        Date datetime NOT NULL,
        Backup_Name varchar(255),
        Source_Path mediumtext NOT NULL,
        Backup_Path mediumtext NOT NULL,
        Total_Size bigint NOT NULL)'''

        create_backup_table = '''CREATE TABLE IF NOT EXISTS backup_files(
        Backup_ID int references backup_info(Backup_ID),
        File_Name text NOT NULL,
        File_Type varchar(255) NOT NULL,
        File_Size bigint NOT NULL,
        File_Path mediumtext NOT NULL)'''

        cursor.execute(create_info_table)
        cursor.execute(create_backup_table)
        con.commit()

        if con.is_connected():
            messagebox.showinfo("Success", "Successfully connected to MySQL Database!\nNow you may take backups or restore from backups!")
            conn_gui.destroy()
    except sql.Error as e:
        messagebox.showerror("Failed", f"{e}\n\nCouldn't connect to MySQL database.\nPlease Try Again!")

def connection_utility():
    global conn_gui

    conn_gui = tk.Toplevel(root)
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
        hname = host_entry.get()
        uname = user_entry.get()
        pwd = pwd_entry.get()
        mysql_connection(hname, uname, pwd)

    conn_button = tk.Button(conn_gui, text="Connect to Database", command=collect_and_connect)
    conn_button.grid(row=4, columnspan=2, pady=15)

def backup(src_entry, dest_entry, name_entry):
    src_path = os.path.normpath(src_entry.get())
    dest_path = os.path.normpath(dest_entry.get())
    name = name_entry.get()

    if not src_path or not dest_path or not name:
        messagebox.showerror("Error", "All Fields are required!")

    else:
        backup_time = str(datetime.datetime.now())[:19]
        total_size = 0

        try:
            dest_path = dest_path + "\\" + name
            for dirpath, dirnames, filenames in os.walk(src_path):
                for file in filenames:
                    file_path = os.path.join(dirpath, file)
                    total_size += os.path.getsize(file_path)

            # Insert backup details into the database
            # We used %s formatting because .format and f' ' were not handling the file_path correctly
            # It was not including the slashes properly while inserting into the database
            insert_backup_info = '''INSERT INTO backup_info(Date, Backup_Name, Source_Path, Backup_Path, Total_Size)
            VALUES (%s, %s, %s, %s, %s)'''

            cursor.execute(insert_backup_info, (backup_time, name, src_path, dest_path, total_size))
            con.commit()

            backup_id = cursor.lastrowid

            for dirpath, dirnames, filenames in os.walk(src_path):
                for file in filenames:
                    file_path = os.path.normpath(os.path.join(dirpath, file))
                    rel_path = os.path.relpath(file_path, src_path)
                    dest_file_path = os.path.normpath(os.path.join(dest_path, rel_path))

                    if not os.path.exists(os.path.dirname(dest_file_path)):
                        os.makedirs(os.path.dirname(dest_file_path))

                    shutil.copy2(file_path, dest_file_path)
                    file_size = os.path.getsize(file_path)

                    file_type = os.path.splitext(file)[1]
                    insert_file_info = '''INSERT INTO backup_files(Backup_ID, File_Name, File_Type, File_Size, File_Path) 
                    VALUES(%s, %s, %s, %s, %s)'''

                    cursor.execute(insert_file_info, (backup_id, file, file_type, file_size, file_path))

                    con.commit()

            messagebox.showinfo("Success", f"Backup completed successfully!\nTotal size: {total_size/(1024*1024)} MB")

        except Exception as e:
            con.rollback()
            messagebox.showerror("Error", f"An error occurred during backup: {str(e)}")

def backup_utility():
    global con

    # con will have None value if connection was never established
    # con.is_connected()==False will be True if connection was tried to be established but failed to take place for some reason
    if con is None or not con.is_connected():
        messagebox.showwarning("Error", "Kindly Connect to MySQL Database first!")
        connection_utility()
    else:
        backup_gui = tk.Toplevel(root)
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
            src_entry.delete(0, tk.END)
            src_entry.insert(0, filedialog.askdirectory())

        def browse_dest_path():
            dest_entry.delete(0, tk.END)
            dest_entry.insert(0, filedialog.askdirectory())

        src_browse = tk.Button(backup_gui, text="Browse", command=browse_src_path)
        src_browse.grid(row=0, column=2, padx=10, pady=10)

        dest_browse = tk.Button(backup_gui, text="Browse", command=browse_dest_path)
        dest_browse.grid(row=1, column=2, padx=10, pady=10)

        def call_backup():
            backup(src_entry, dest_entry, name_entry)

        backup_button = tk.Button(backup_gui, text="Start Backup", command=call_backup)
        backup_button.grid(row=4, columnspan=3, pady=10)
    
def restore(restore_id, dest_entry):
    cursor.execute(f'SELECT source_path from backup_info where backup_id={restore_id}')

    src_path = str(cursor.fetchone()[0])
    dest_path = os.path.join(dest_entry.get(), src_path.split('\\')[-1])
    dest_path = os.path.normpath(dest_path)

    for dirpath, dirnames, filenames in os.walk(src_path):
        for file in filenames:
            file_path = os.path.normpath(os.path.join(dirpath, file))
            rel_path = os.path.relpath(file_path, src_path)
            dest_file_path = os.path.normpath(os.path.join(dest_path, rel_path))

            if not os.path.exists(os.path.dirname(dest_file_path)):
                os.makedirs(os.path.dirname(dest_file_path))


            shutil.copy2(file_path, dest_file_path) 
    
    messagebox.showinfo("Success", f"Restore completed successfully!")

def restore_utility():
    global con

    if con is None or not con.is_connected():
        messagebox.showwarning("Error", "Kindly Connect to MySQL Database first!")
        connection_utility()

    else:
        # Create a function just to enter destination directory
        def dest_path_select():
            id_tup=[]
            restore_id = int(id_entry.get())
            cursor.execute('SELECT backup_id from backup_info')
            id_tup = [x[0] for x in cursor.fetchall()]

            if restore_id not in id_tup:
                messagebox.showwarning("Invalid Backup ID", "The Backup ID you entered either does't exist\nor was deleted")
                restore_gui.destroy()
                restore_utility()
            else:
                rest_path_sel_gui = tk.Toplevel(restore_gui)
                rest_path_sel_gui.title("Select Restore Directory")

                tk.Label(rest_path_sel_gui, text="Enter Path to Restore").grid(row=0, column=0, padx=10, pady=(10,0))

                def browse_dest_path():
                    dest_entry.delete(0, tk.END)
                    dest_entry.insert(0, filedialog.askdirectory())
                
                def call_restore():
                    restore(restore_id, dest_entry)

                dest_entry = tk.Entry(rest_path_sel_gui)
                dest_entry.grid(row=0, column=1, padx=10, pady=(10,0))

                browse_dest_path = tk.Button(rest_path_sel_gui, text="Browse", command=browse_dest_path)
                browse_dest_path.grid(row=0, column=2, padx=10, pady=(10,0))

                start_rest_butt = tk.Button(rest_path_sel_gui, text='Start Restore', command=call_restore)
                start_rest_butt.grid(row=1, columnspan=3, pady=10)

        restore_gui = tk.Toplevel(root)
        restore_gui.title("Restore Files")
        cursor.execute('SELECT backup_id, backup_name, date, source_path, total_size/(1024*1024) FROM backup_info')

        rows = cursor.fetchall()

        table = ttk.Treeview(restore_gui, columns=('id', 'name', 'date', 'src_path','total_size'), show='headings')

        #Define column headings of the table
        table.heading('id', text='Backup ID')
        table.heading('name', text='Backup Name')
        table.heading('date', text='Date')
        table.heading('src_path', text='Source Path')
        table.heading('total_size', text='Total Size (MB)')

        
        #Add columns to the table
        table.column('id', width=75, anchor='center')
        table.column('name', width=150, anchor='center')
        table.column('date', width=150, anchor='center')
        table.column('src_path', width=300, anchor='center')
        table.column('total_size', width=150, anchor='center')

        for i in rows:
            table.insert('', 'end', values=i)

        table.pack()

        input_frame = tk.Frame(restore_gui)
        input_frame.pack(pady=(10, 10))  # Center the frame with vertical padding

        # Place the label and entry side by side inside the frame
        tk.Label(input_frame, text="Enter Backup ID to Restore").pack(side='left', padx=(35, 5))
        id_entry = tk.Entry(input_frame)
        id_entry.pack(side='left', padx=(5, 10))

        # Place the button to the right of the entry
        restore_button = tk.Button(input_frame, text="Start Restore", command=dest_path_select)
        restore_button.pack(side='left', padx=(10, 5))

def statistics(backup_id, stat_gui):
    global cursor
    
    graphs = tk.Toplevel(stat_gui)
    graphs.title('Select Graphs')

    tk.Label(graphs, text=f"Selected Backup ID: {backup_id}").grid(row=0, columnspan=2)

    type_button = tk.Button(graphs, text="Type-wise File Distribution Pie Chart", command=lambda id=backup_id:typewise_chart(id))
    type_button.grid(row=1, columnspan=2, padx=10, pady=10)

    avg_size_button = tk.Button(graphs, text="Average File Size Distribution", command=lambda id=backup_id:avg_file_size(id))
    avg_size_button.grid(row=2, columnspan=2, padx=10, pady=10)

    top_files_button = tk.Button(graphs, text="Top 10 Files by Size", command=lambda id=backup_id:largest_files(id))
    top_files_button.grid(row=3, columnspan=2, padx=10, pady=10)

    def typewise_chart(backup_id):

        # Fetch typewise file distribution
        query = f'SELECT file_type, SUM(file_size) FROM backup_files WHERE backup_id={backup_id} GROUP BY file_type'
        cursor.execute(query)
        backup_info = cursor.fetchall()
        types = []
        sizes = []

        for item in backup_info:
            sizes.append(item[1])
            types.append(item[0])

        plt.pie(sizes, labels=types, startangle=0, autopct='%1.1f%%', colors=plt.cm.Paired(range(len(types))))
        plt.title("Typewise Distribution of Files", fontweight='bold')
        plt.show()
        
    def avg_file_size(backup_id):
        # Fetch average file size per file type
        avg_query = f'SELECT file_type, AVG(file_size) FROM backup_files WHERE backup_id={backup_id} GROUP BY file_type'
        cursor.execute(avg_query)
        avg_info = cursor.fetchall()

        avg_types = []
        avg_sizes = []

        for item in avg_info:
            avg_types.append(item[0])
            avg_sizes.append(item[1]/(1024*1024))
        
        plt.bar(avg_types, avg_sizes, color='skyblue')
        plt.xlabel('File Type')
        plt.ylabel('Average File Size (MB)')
        plt.title('Average File Size per File Type', fontweight='bold')
        plt.show()

    def largest_files(backup_id):
        # Fetch top 10 largest files
        cursor.execute(f'''
            SELECT File_Name, File_Size
            FROM backup_files
            WHERE backup_id={backup_id}
            ORDER BY File_Size DESC
            LIMIT 10
        ''')
        top_files = cursor.fetchall()

        file_names = [file[0] for file in top_files]
        file_sizes = [file[1]/(1024*1024) for file in top_files]

        plt.figure(figsize=(13,6))
        plt.barh(file_names[::-1], file_sizes[::-1], color='skyblue') # Invert for descending order
        plt.xlabel('File Size (MB)')
        plt.ylabel('File Name')
        plt.title('Top 10 Largest Files', fontweight='bold')

        plt.subplots_adjust(left=0.3)
        plt.show()

def statistics_utility():
    global con

    if con is None or not con.is_connected():
        messagebox.showwarning("Error", "Kindly Connect to MySQL Database first!")
        connection_utility()
    else:
        query = 'SELECT backup_id, backup_name, total_size FROM backup_info'
        cursor.execute(query)
        data = cursor.fetchall()
        
        stat_gui = tk.Toplevel(root)
        stat_gui.title("Backup Stats")

        # Define the headers
        headers = ["Backup ID", "Backup Name", "Total Size", "Actions"]

        for i, header in enumerate(headers):
            tk.Label(stat_gui, text=header, font=("Arial", 10, "bold")).grid(row=0, column=i, padx=10, pady=5)

        for i, (backup_id, backup_name, total_size) in enumerate(data, start=1):
            tk.Label(stat_gui, text=backup_id).grid(row=i, column=0, padx=10, pady=7)
            tk.Label(stat_gui, text=backup_name).grid(row=i, column=1, padx=10, pady=7)
            tk.Label(stat_gui, text=total_size).grid(row=i, column=2, padx=10, pady=7)
            
            # Add a button in the "Actions" column
            button = tk.Button(stat_gui, text="Stats", command=lambda id=backup_id:statistics(id, stat_gui))
            button.grid(row=i, column=3, padx=10, pady=7)

        
# Creating the main Tkinter window
root = tk.Tk()
root.title("Backup and Restore")

# Add all the required buttons into the main window
connect_button = tk.Button(root, text="Connect To MySQL Database", command=connection_utility)
connect_button.pack(padx=30, pady=10)

backup_utility_button = tk.Button(root, text="Backup Files", command=backup_utility)
backup_utility_button.pack(padx=30, pady=10)

restore_button = tk.Button(root, text="Restore from Backup", command=restore_utility)
restore_button.pack(padx=30, pady=10)

stats_button = tk.Button(root, text="Statistics", command=statistics_utility)
stats_button.pack(padx=30, pady=10)

root.mainloop()