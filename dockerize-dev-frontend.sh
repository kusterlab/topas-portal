cd vue-frontend
sudo docker build --build-arg NODE_ENV=development --build-arg VUE_APP_API_HOST=http://$(hostname -I | awk '{print $1}'):3832 -t mtb:dev . 
sudo docker stop mtb_portal_frontend
sudo docker run -d --name mtb_portal_frontend -it -p 3834:3834 --rm mtb:dev

