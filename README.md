### Step-by-Step Fix: Move Project to WSL and Dockerize
- Step 1: Open your WSL terminal
Run:
wsl
You’ll land in something like: username@YourPC:~$

- Step 2: Create a project directory in WSL
Inside WSL, do:

mkdir -p ~/projects/digital-wallet
cd ~/projects/digital-wallet

- Step 3: Copy files from Windows to WSL
Still inside WSL, copy your Windows files using the /mnt/ path:

cp /mnt/c/Users/Haricharan/Documents/DigitalWallet/sqlite-tools-win-x64-3490200/*.py .
cp /mnt/c/Users/Haricharan/Documents/DigitalWallet/sqlite-tools-win-x64-3490200/expenses.db .

✅ Now you have:

DigiApi.py
main.py
expenses.db
in your WSL folder, ready to use.

- Step 4: Create requirements.txt
Still in the same folder (~/projects/digital-wallet):

nano requirements.txt
Paste:

fastapi
uvicorn[standard]

Press Ctrl + O, then Enter to save. Press Ctrl + X to exit.

- Step 5: Create Dockerfile
Still in that directory:

nano Dockerfile
Paste:

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000

CMD ["uvicorn", "DigiApi:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]
Save and exit.

- Step 6: Build Docker Image

docker build -t digiapi-backend .
- Step 7: Run the Container

docker run -d -p 9000:9000 --name digiapi-container digiapi-backend
- Step 8: Test It!
Open browser in Windows and visit:

http://localhost:9000/docs
You should see FastAPI running 

-----------
if the url is not reachable, do the below debugging
- How to Check if It’s Running
Run this in WSL to see running containers:
docker ps

You should see something like:

CONTAINER ID   IMAGE             PORTS                    NAMES
abc123         digiapi-backend   0.0.0.0:9000->9000/tcp   digiapi-container

- If You Change Code
If you modify your Python files (like DigiApi.py), you need to:

Rebuild the image:

docker build -t digiapi-backend .
Restart the container:

docker stop digiapi-container
docker rm digiapi-container
docker run -d -p 9000:9000 --name digiapi-container digiapi-backend

### Step-by-Step Troubleshooting
- Step 1: View Container Logs
Run this command to see what’s happening inside:

docker logs -f digiapi-container

- Step 2: Manually Exec into the Container
If the logs don't help, jump inside the container to run things yourself:

docker exec -it digiapi-container /bin/bash

I got the below error, because we haven't added all the modules in our requirements.txt

The error is:
ModuleNotFoundError: No module named 'passlib'

- Fix: Add passlib to requirements.txt
Update your requirements.txt to include:

fastapi
uvicorn[standard]
passlib[bcrypt]
python-jose

- Then Rebuild and Restart Docker
Now do:
docker build -t digiapi-backend .
docker stop digiapi-container
docker rm digiapi-container
docker run -d -p 9000:9000 --name digiapi-container digiapi-backend

Our docker will run and then the URL is reachable.
