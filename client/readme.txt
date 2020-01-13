pyinstaller --hidden-import=queue -F -w clientmnt.py

pyinstaller -F clientmnt.py
pyinstaller -F -w clientmnt.py



test:
pyinstaller -F testdir.py







#¹Ø±Õ½ø³Ì
taskkill [/S system [/U username [/P [password]]]]
         {[/FI filter] [/PID processid] | /IM imagename} [/T] [/F]

print(os.popen('tasklist').read())
os.system('taskkill /IM SougouCloud.exe /F')


