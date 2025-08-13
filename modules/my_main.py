import database_creation
import data_procession
import data_collection

db_name = 'our_database.db'
database_creation.main(db_name)
files = {'curtis.html', 'huff.html', 'huff_8_13.html'}
for file in files:
    data_dict, date, dine_hall_id = data_collection.main(file)
    data_procession.main(data_dict, date, dine_hall_id, db_name)