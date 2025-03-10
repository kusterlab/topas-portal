cd vue-frontend
sudo docker build -f dockerfile_dev -t mtb:dev . 
sudo docker stop mtb_portal_frontend
sudo docker run -d --name mtb_portal_frontend -it -p 3834:3834 --rm mtb:dev

