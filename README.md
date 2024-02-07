# FOODGRAM

Foodram is a social platform for food enthusiasts to share their culinary experiences, discover new recipes, and connect with like-minded individuals. Whether you're a home cook or a professional chef, Foodram provides a space to showcase your culinary creations and explore a world of delicious possibilities.


Used libraries:  
- [Django                        3.2.3](https://docs.djangoproject.com/en/3.2/)  
- [djangorestframework           3.12.4](https://www.django-rest-framework.org/)  
- [djangorestframework-simplejwt 4.8.0](https://django-rest-framework-simplejwt.readthedocs.io/)

## Features

- **Recipe Sharing:** Share your favorite recipes with the community. Include detailed instructions, ingredients, and mouthwatering images.

- **Follow Users:** Connect with other food lovers by following their profiles. Stay updated on their latest culinary creations.

- **Favorite Recipes:** Save your favorite recipes to easily access them later. Build a personalized collection of go-to dishes.

- **Download Ingredient Lists:** Need to shop for ingredients? Download the ingredient list of any recipe to make your grocery shopping a breeze.


## Installation of the project:
Clone the repository and change into it on the command line:

	git clone https://github.com/mityay36/foodgram-project-react/

Make your own .env file in main directory. All required variables are listed in .env.example
 
Perform Docker images

  	cd frontend
  	docker build -t YOUR_USERNAME/foodgram_frontend .
  	cd ../backend
  	docker build -t YOUR_USERNAME/foodgram_backend .
  	cd ../nginx
  	docker build -t YOUR_USERNAME/foodgram_gateway . 

Push your images to Docker Hub

  	docker push YOUR_USERNAME/foodgram_frontend
  	docker push YOUR_USERNAME/foodgram_backend
  	docker push YOUR_USERNAME/foodgram_gateway

Connect to our remote server

  	ssh -i PATH_TO_SSH_KEY/SSH_KEY_NAME YOUR_USERNAME@SERVER_IP_ADDRESS 

Make an "foodgram" directory

  	mkdir foodgram

Download DockerCompose on the server

  	sudo apt update
  	sudo apt install curl
  	curl -fsSL https://get.docker.com -o get-docker.sh
  	sudo sh get-docker.sh
  	sudo apt install docker-compose

Copy docker-compose.production.yml and .env files to your server

  	scp -i PATH_TO_SSH_KEY/SSH_KEY_NAME docker-compose.production.yml YOUR_USERNAME@SERVER_IP_ADDRESS:/home/YOUR_USERNAME/foodgram/docker-compose.production.yml

Start Docker Compose in daemon mode

  	sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml up -d

Make migrations and collect static of your project

  	sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py migrate
  	sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py collectstatic
  	sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/

Open nginx configuration file

  	sudo nano /etc/nginx/sites-enabled/default

Update your server location section

  	location / {
    		proxy_set_header Host $http_host;
    		proxy_pass http://127.0.0.1:9000;
  	}

Make sure the cof file is ok

  	sudo nginx -t

Reload nginx

  	sudo service nginx reload
  
### Сайт доступен по ссылке: 
### [mityay36foodgram.hopto.org](https://mityay36foodgram.hopto.org)

## Author
[Dmitry Pokrovsky](https://github.com/mityay36) & Yandex.Practicum
