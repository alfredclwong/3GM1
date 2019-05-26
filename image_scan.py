import os
matches=[]
for root, dirs, files in os.walk('/media/pi'):
    for filename in files:
        if filename.endswith('.jpg','.png',')):
            matches.append(os.path.join(root,filename))
