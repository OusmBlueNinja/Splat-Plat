echo "Installing Dependences"
pip install -r ./data/requirements.txt
echo "Starting Physicics Engine"
python3 ./data/init.py
echo "Starting Program"
python3 Platformer.py