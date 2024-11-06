# PSI ridepooling matching

This project build on top of QuickPool so you can follows its installation guide + additional external dependencies.
For demo purpose, we mock input from driver and rider with triples generation app.
- User can act as a driver or rider to input their start and end position to create route triples to the database(mongoDB)
- Modified original QuickPool code fetch these triples from the db into its PSI with a third party (third party PSI).
Further explaination can be found in slides: https://docs.google.com/presentation/d/1HIrOMiZK4FcA88VesIeRQKzkMVmp_dyIA_9d5xN4dH4/edit?usp=sharing

# Original QuickPool Overview
- Basically, the original QuickPool simulates each party in the third party PSI: private computation and communication between them
- Private route from rider and driver are multiple tuples of integer (v_i, v_(i+1))
- There are several implementation of PSI with 3rd party. The one we are interested use EMP (Efficient Multi-Party computation) framework’s block to encapsulate a 128 bit data (each tuple in the route tuples) from rider and driver
    - EMP's block(v_i || v_(i+1)) where v_i, v_(i+1) are uint64
- For masking its input before sending it to the 3rd party to compute EMP’s PRP based on the AES
- The 3rd party compute the match but it haven't implemented the last communication to each rider and driver corresponding to the match

# Modification of QuickPool
- Instead of tuples, routes are now represented as multiple triples (v_i, v_(i+threshold), t_(i+time flexibility)) into 
EMP's block(v_i || v_(i+threshold) || t_(i+time flexibility))
    - The node from the Openstreetmap is represented by 64 bit integer
    - We make the v_i, v_(i+threshold) to be fit within 42 bit by manipulating the node to node - min_node(local road network) in the triples generation app. also t_(i+time flexibility) is represent by integer (-max time flexibility, minutes away from 12:00 am + max time flexibilty) which fits in 42 bit
        - (Haven't implemented) here we can change from 42 bit || 42 bit || 42 bit to 58 bit || 58 bit || 12 bit
    - Then follows the same steps from original QuickPool

# Triples generation 
- A python app where it recieves a request with the form like
```
{
    "user_type": "rider",
    "start_location": [18.788691, 98.982505],
    "end_location": [18.788712, 98.967227],
    "start_time": "16:25",
    "c": 8,
    "k": 3
}
```
where c is intersection threshold, k is time flexibilty
- Send a json to the mongoDB with the form like
```
{
    "_id": "6728f0cee72dcfae54f64d33",
    "created_at": "Mon, 04 Nov 2024 16:05:34 GMT",
    "triples": [[1050972592,1050972698,987], ..]
}
```
where id is just unique mongoDB's generated id
- Plot the route over a map for later visualization

## Additional External Dependencies
- [mongocxx](https://www.mongodb.com/docs/languages/cpp/cpp-driver/current/get-started/download-and-install/)

### Docker
Execute the following commands from the `QuickPool` directory
```sh
# Build the QuickPool Docker image.
#
# Building the Docker image requires at least 4GB RAM. This needs to be set 
# explicitly in case of Windows and MacOS.
docker build -t quickpool .

# Create and run a container.
#
# This should start the shell from within the container.
docker run -it -v $PWD:/code quickpool

# The following command changes the working directory to the one containing the 
# source code and should be run on the shell started using the previous command.
cd /code
```

## Run the triples generation app
Execute the following commands from the root directory
```sh
python app.py
```

## Compilation
Execute the following commands from the `QuickPool` directory
```sh
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..

cmake --build . --target Intersection_app
```

## Run the protocol
Execute the following commands from the `QuickPool` directory created during compilation to run the programs:
```sh
./run_quickpool.sh 3 3
```

## Replicate results
You can try an example sequence of request here from places in Chiangemai
1. invis garden -> sting hive
```
{
    "user_type": "driver",
    "start_location": [18.795551,98.9673624],
    "end_location": [18.794558, 98.979166],
    "start_time": "16:30",
    "c": 8,
    "k": 3
}
```

2. invis garden -> NW to north gate
```
{
    "user_type": "rider",
    "start_location": [18.795551,98.9673624],
    "end_location": [18.796772, 98.975797],
    "start_time": "16:25",
    "c": 8,
    "k": 3
}
```

3. galae restaurant -> maya shopping mall
```
{
    "user_type": "rider",
    "start_location": [18.793261, 98.946005],
    "end_location": [18.802104, 98.967178],
    "start_time": "16:27",
    "c": 8,
    "k": 3
}
```
4. cmu gym -> cm national museum
```
{
    "user_type": "driver",
    "start_location": [18.797534, 98.957479],
    "end_location": [18.810716, 98.975804],
    "start_time": "16:30",
    "c": 8,
    "k": 3
}
```

5. wat phra sing -> wat suan dok
```
{
    "user_type": "rider",
    "start_location": [18.788691, 98.982505],
    "end_location": [18.788712, 98.967227],
    "start_time": "16:25",
    "c": 8,
    "k": 3
}
```
6.huen pen restaurant -> sri pat opd
```
{
    "user_type": "driver",
    "start_location": [18.785715, 98.984893],
    "end_location": [18.790536, 98.970832],
    "start_time": "16:26",
    "c": 8,
    "k": 3
}
```
