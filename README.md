# Foody
A restaurant management system.

## How to deploy
- Download the source code
```sh
git clone https://github.com/pythonbrad/foody.git
cd foody
```
- Create a virtual environment
```sh
python3 -m venv .foody_venv
source .foody_venv/bin/activate
```
- Install the requirements
```sh
pip install -r requirements.txt
```
- Config the environement (.env file)
```sh
cp .env_example .env
```
- Config the database
```sh
python manage.py makemigrations
python manage.py migrate
```

## License
MIT