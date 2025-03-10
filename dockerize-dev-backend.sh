# this script can dockerize the db and the flask backend but not the frontend
sudo docker-compose -f docker-compose-backend.local.yml stop
sudo docker-compose -f docker-compose-backend.local.yml down --volumes   # uncomment to start the db; all db data will be lost
sudo docker volume rm flask_cohort_data                        # uncomment to delete the volumes; all db  data will be lost
sudo docker-compose -f docker-compose-backend.local.yml rm -f
sudo docker-compose -f docker-compose-backend.local.yml pull
sudo docker-compose -f docker-compose-backend.local.yml up --build -d
