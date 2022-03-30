# Lightstreamer

Here I have implemented a simple demo with Lightstreamer server version 7.2.2 for single channel masseging.

## Installation

1. Download Lightstreamer:

Please download from here <a href="http://www.lightstreamer.com" rel="nofollow">Lightstreamer</a>
Then unzip and keep all in a single folder.

2. Clone this repository: 

```
git clone git@github.com:devnet-limited/hrms.git
```

3. Lightstreamer setup: 

Copy the folder "PythonAdapter" from adapters/ and paste it in Lightstreamer/adapter/PythonAdapter
Copy the file "lightstreamer_conf.xml" from conf/ and paste it in Lightstreamer/conf/lightstreamer_conf.xml

Here I am using 8080 and 8888 port to run Lightstreamer server. To run clinet script I am using 8003, 8002, 8001 port.

4. Remote adapter: 

You don't need to move remoteAdapter.py file or you can move to any place from where you can execute this file. Finally run the below cmd.

```
pip install lightstreamer-adapter==1.2.2
```


5. Client Side:

Copy ClientScript folder with all files to Lightstreamer/pages/demos/ClientScript or to your external web server location as you need.

6. Run Lightstreamer Server:

On comandline, enter to your server script folder and dig to bin/unix-like and run the below cmd

```
./start.sh 
```
or 

```
./LS.sh run
```

7. Run Remote Adapter:
On another comandline, enter to the location of yout remote adapter file which is provided in this repository named remoteAdapter.py and the below cmd.

```
python3 remoteAdapter.py --host localhost --metadata_rrport 8003 --data_rrport 8001 --data_notifport 8002 
```

8. Browse client:
Now go to your faverite browser and browse https://localhost:8080/demos/ClientScript or url of your web server.



## References

* Lightstreamer: https://lightstreamer.com/static/download/
* Lightstreamer Documentation: https://libraries.io/pypi/lightstreamer-adapter
* Lightstreamer Demos: https://demos.lightstreamer.com/