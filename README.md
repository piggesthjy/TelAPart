This the the python code to detect Service and Maintenance Issues of Cable Boradband Network

1. Run it using python command:
 - Install the following python libraries: 
   ```
   pip3 install requirement.txt
   ```
 - Change the data_path in main.py to the input file path and the configuration path:
   ```
   data_path = your_file_path
   config_path = your_config_path
   ```
 - Run script using:
   ```
   python3 main.py
   ```

2. Run it inside docker:
  - Build the docker image using the following command:
    ```
    sudo docker build -t image_name .
    ```
    
  - rename your input data file to input.json
  - Run the docker container using the following command:
    ```
    sudo docker run -v dir_of_input.json:/input image_name
    ```
