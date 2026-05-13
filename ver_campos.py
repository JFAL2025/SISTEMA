import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=(localdb)\\jfal;Trusted_Connection=yes;DATABASE=MATRIZ')
cursor = conn.cursor()

cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'USUARIOS'")
columns = cursor.fetchall()

print('📋 Campos de la tabla USUARIOS:')
print('=' * 40)
for col in columns:
    print(f'  - {col[0]} ({col[1]})')

conn.close()