import win32com.client
import os

file_path = r"E:\My Drive\_clay0aucoin@gmail.com\personal.lib\resume\Clay Aucoin - Resume.docx"

properties = ["Title", "Author", "Company", "Revision number", "Content created", "Date last saved"]
shell = win32com.client.Dispatch("Shell.Application")
folder = shell.NameSpace(os.path.dirname(file_path))
item = folder.ParseName(os.path.basename(file_path))

for prop in properties:
    print(f"{prop}: {folder.GetDetailsOf(item, properties.index(prop))}")
