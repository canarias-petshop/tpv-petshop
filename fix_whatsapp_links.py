import os
import glob

# Find all python files in the directory
py_files = glob.glob("*.py")

for file in py_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'https://api.whatsapp.com/send?phone=' in content:
        # We need to carefully replace wa.me with api.whatsapp.com
        # Format usually is: f"https://api.whatsapp.com/send?phone={phone_var}&text={urllib.parse.quote(msg)}"
        
        # Replace the domain and the ? after the phone variable with &
        # To do this safely:
        # replace "https://api.whatsapp.com/send?phone=" with "https://api.whatsapp.com/send?phone="
        # AND replace "&text=" with "&text="
        
        new_content = content.replace('https://api.whatsapp.com/send?phone=', 'https://api.whatsapp.com/send?phone=')
        new_content = new_content.replace('&text=', '&text=')
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")
