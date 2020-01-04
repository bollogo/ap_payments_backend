# AP Payments Backend

## Installation

Create a new virtual Python 3 environment

```
python3 -m venv <path_to_venv>
```

Activate the newly created virtual environemnt

```
source <path_to_venv>/bin/activate
```

Install all requirements

```
pip3 install -r requirements.txt
```

We now have to setup a new sqlite database and creating all the needed tables by calling
```
python manage.py migrate
```

We now need to setup paypal in our environemnt
```
export PAYPAL_MODE=sandbox # or live, depending on your use
export PAYPAL_CLIENT_ID=<your_paypal_client_id>
export PAYPAL_CLIENT_SECRET=<your_paypal_client_secret>
```

The last thing we need to do before starting our server is to create a new superuser account. Simply follow the instructions in the terminal
```
python manage.py createsuperuser
```

Now, you should be able to start the django local development server with on your machine on port 8001 with

```
python manage.py runserver 0:8001
```

