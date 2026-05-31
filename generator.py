import csv
import random
import os
import struct

def gen(n=50000000): 
    prods = ["Monitor", "CPU", "GPU", "SSD", "RAM", "PSU", "Case", "Mouse", "Keyboard"]
    csv_name = "data.csv"
    bin_name = "data.bin"
    
    print(f"Генерация {n} строк...")
    
    with open(csv_name, 'w', newline='', encoding='utf-8') as f_csv, \
         open(bin_name, 'wb') as f_bin:
        
        w = csv.writer(f_csv)
        w.writerow(['ID', 'Name', 'Quantity', 'Price'])
        
        buf = []
        for i in range(1, n + 1):
            t_id = random.randint(100000000, 999999999) 
            t_name = random.choice(prods)
            t_qty = random.randint(100, 999)
            t_price = random.randint(10000, 999999)
            
            buf.append([t_id, t_name, t_qty, t_price])
            
            bin_data = struct.pack('I 12s I I', t_id, t_name.encode('utf-8').ljust(12, b'\0'), t_qty, t_price)
            f_bin.write(bin_data)
            
            if i % 1000000 == 0:
                w.writerows(buf)
                buf = []
                print(f"Готово: {i} строк")
        if buf:
            w.writerows(buf)
        
    print(f"CSV создан! Размер: {os.path.getsize(csv_name)/1e6:.2f} МБ")
    print(f"BIN создан! Размер: {os.path.getsize(bin_name)/1e6:.2f} МБ")

if __name__ == "__main__": 
    gen(50000000)   # можно увеличить до 50000000, но для теста оставлено 50000