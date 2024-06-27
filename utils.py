import csv
import os
import tkinter as tk
from tkinter import messagebox


def print_the_output_statement(output, message):
    output.insert(tk.END, f"{message} \n", "bold")
    output.update_idletasks()  # Update the widget immediately
    print(message)


def save_data_to_file(combined_headers, combined_data, save_folder):
    try:
        os.makedirs(save_folder, exist_ok=True)
        file_name = f"{save_folder}/combined_table_data.csv"
        if combined_data:
            with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(combined_headers)  # Write headers as the first row
                csvwriter.writerows(combined_data)  # Write data rows
            return file_name
    except Exception as e:
        messagebox.showerror("Error", f"Error saving data: {str(e)}")
