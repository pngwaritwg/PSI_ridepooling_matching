# app.py
from flask import Flask, request, jsonify
import osmnx as ox
import networkx as nx
from database import route_triples_collection  # Import create_app and db
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

app = Flask(__name__)
# Load the road network
G = ox.graph_from_point((18.7961042,98.9657007), dist=2500, network_type='drive')

def create_n_routes_with_time(start, end, start_time, c, k, velocity=13.89, num_routes=10):
    """
    Create multiple routes with segments (v_i, v_i+c, t_i+j), where time is calculated based on the distance and velocity.

    Args:
        start: tuple of (latitude, longitude) for start point
        end: tuple of (latitude, longitude) for end point
        start_time: initial time as a string (e.g., "12:00")
        c, k: additional parameters for future use (currently unused)
        velocity: speed in meters per second (default ~50 km/h)
        num_routes: number of k-shortest routes to create
    """
    
    # Project start and end locations to nearest nodes
    start_node = ox.distance.nearest_nodes(G, start[1], start[0])
    end_node = ox.distance.nearest_nodes(G, end[1], end[0])

    # Find k shortest paths using length as the weight
    n_paths = list(ox.k_shortest_paths(G, start_node, end_node, k=num_routes, weight="length"))

    all_triples = []  # To store triples from all routes
    fig, ax = ox.plot_graph(G, node_size=0, edge_color='gray', show=False, close=False)
    
    # Iterate over each path to calculate time for each segment
    for path in n_paths:
        edge_lengths = ox.routing.route_to_gdf(G, path)["length"]
        
        # Initialize the route and time
        route = []
        current_time = datetime.strptime(start_time, "%H:%M")
        
        # Iterate over path segments to calculate time for each edge
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            segment_length = edge_lengths.iloc[i]  # Get the length of the edge in meters

            # Calculate time taken for this segment
            time_taken = int(segment_length / velocity)  # Time in seconds
            current_time += timedelta(seconds=time_taken)

            # Store the segment with the current time
            route.append((u, v, (current_time.hour * 60 + current_time.minute)))  # Store time as total minutes
        
        # Create triples (v_i, v_i+c, t_i+j) for all i and for all j in range [-k, k]
        for i in range(len(route)):
            for j in range(-k, k + 1):
                v_i, v_i_next, t_i = route[i]

                # Ensure the index for v_i + c is within the range of the route
                if i + c < len(route):
                    v_i_c = route[i + c][0]  # Get v_(i+c)
                    time_with_offset = t_i + j
                    
                    # Check if time_with_offset is greater than zero
                    if time_with_offset > 0:
                        all_triples.append((v_i, v_i_c, time_with_offset))

        # Extract coordinates for path nodes
        path_nodes_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path]
        
        # Scatter plot path nodes on top of the route
        path_lats, path_lons = zip(*path_nodes_coords)
        
        # Draw arrows between path nodes
        for i in range(len(path) - 1):
            ax.arrow(path_lons[i], path_lats[i], 
                     path_lons[i + 1] - path_lons[i], 
                     path_lats[i + 1] - path_lats[i], 
                     head_width=0.0005, head_length=0.0003, width=0.00005, 
                     fc='red', ec='red')

    # Add a legend and title
    plt.legend()
    plt.title("K Shortest Paths from Start to End")
    plt.savefig(f"plot/{datetime.utcnow()}.png")

    return all_triples

def create_route_with_time(start, end, start_time, c, k, velocity=13.89):
    """
    Create a route with segments (v_i, v_i+c, t_i+j), where time is calculated based on the distance and velocity.

    Args:
        start: tuple of (latitude, longitude) for start point
        end: tuple of (latitude, longitude) for end point
        start_time: initial time as a string (e.g., "12:00")
        c, k: additional parameters for future use (currently unused)
        velocity: speed in meters per second (default ~50 km/h)
    """
    
    # Project start and end locations to nearest nodes
    start_node = ox.distance.nearest_nodes(G, start[1], start[0])
    end_node = ox.distance.nearest_nodes(G, end[1], end[0])

    # Find the shortest path using travel time
    path = ox.routing.shortest_path(G, start_node, end_node, k=10, weight="length")

    edge_lengths = ox.routing.route_to_gdf(G, path)["length"]
    
    # Initialize the route and time
    route = []
    current_time = datetime.strptime(start_time, "%H:%M")
    
    # Iterate over path segments to calculate time for each edge
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        segment_length = edge_lengths.iloc[i] # Get the length of the edge in meters

        # Calculate time taken for this segment
        time_taken = int(segment_length / velocity)  # Time in seconds
        current_time += timedelta(seconds=time_taken)

        # Store the segment with the current time
        route.append((u, v, (current_time.hour * 60 + current_time.minute)))  # Store time as total minutes

    # Create triples (v_i, v_i+c, t_i+j) for all i and for all j in range [-k, k]
    triples = []
    for i in range(len(route)):
        for j in range(-k, k + 1):
            v_i, v_i_next, t_i = route[i]
            
            # Ensure the index for v_i + c is within the range of the route
            if i + c < len(route):
                v_i_c = route[i + c][0]  # Get v_(i+c)
                time_with_offset = t_i + j
                
                # Check if time_with_offset is greater than zero
                if time_with_offset > 0:
                    triples.append((v_i, v_i_c, time_with_offset))

    fig, ax = ox.plot_graph(G, node_size=0, edge_color='gray', show=False, close=False)
    
    # Extract coordinates for path nodes
    path_nodes_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path]
    
    # Scatter plot path nodes on top of the route
    path_lats, path_lons = zip(*path_nodes_coords)
    
    # Draw arrows between path nodes
    for i in range(len(path) - 1):
        ax.arrow(path_lons[i], path_lats[i], 
                 path_lons[i + 1] - path_lons[i], 
                 path_lats[i + 1] - path_lats[i], 
                 head_width=0.0005, head_length=0.0003, width=0.00005, 
                 fc='red', ec='red')

    # Add a legend and title
    plt.legend()
    plt.title("Shortest Path from Start to End")
    plt.savefig(f"plot/{datetime.utcnow()}.png")

    return triples

# def create_route(start, end, start_time, c, k):
    
#     # Project start and end locations to nearest nodes
#     start_node = ox.distance.nearest_nodes(G, start[1], start[0])
#     end_node = ox.distance.nearest_nodes(G, end[1], end[0])
    
#     # Find the shortest path
#     # path = nx.shortest_path(G, start_node, end_node)
#     path = ox.shortest_path(G, start_node, end_node, weight="travel_time")
#     # path = nx.dijkstra_path(G, start_node, end_node)

#     edge_lengths = ox.routing.route_to_gdf(G, route)["length"]
    
#     # Create the route defined as (v_i, v_i+1, t_i)
#     route = [(path[i], path[i+1], start_time) for i in range(len(path)-1)]
    
#     # Create triples (v_i, v_i+c, t_i+j) for all i and for all j in range [-k, k]
#     triples = []
#     for i in range(len(route)):
#         for j in range(-k, k + 1):
#             v_i, v_i_next, t_i = route[i]
            
#             # Ensure the index for v_i + c is within the range of the route
#             if i + c < len(route):
#                 v_i_c = route[i + c][0]  # Get v_(i+c)
#                 time_with_offset = t_i + j
                
#                 # Check if time_with_offset is greater than zero
#                 if time_with_offset > 0:
#                     triples.append((v_i, v_i_c, time_with_offset))
    
#     # Visualize the road network, start node, end node, and shortest path
#     fig, ax = ox.plot_graph(G, node_size=0, edge_color='gray', show=False, close=False)
    
#     # Plot the start and end nodes
#     start_lat, start_lon = start[0], start[1]
#     end_lat, end_lon = end[0], end[1]
    
#     # Mark the start and end locations
#     ax.scatter(start_lon, start_lat, color='green', s=100, label='Start', zorder=5)
#     ax.scatter(end_lon, end_lat, color='red', s=100, label='End', zorder=5)
    
#     # Get node coordinates from the graph
#     pos = {node: (data['x'], data['y']) 
#            for node, data in G.nodes(data=True)}
    
#     # Plot the shortest path
#     path_edges = list(zip(path[:-1], path[1:]))  # Create edge pairs
#     nx.draw_networkx_edges(G, pos=pos, edgelist=path_edges, 
#                           edge_color='green', width=2, alpha=1)
    
#     # Add a legend and title
#     plt.legend()
#     plt.title("Shortest Path from Start to End")
#     plt.savefig(f"plot/{datetime.utcnow()}.png")
    
#     return triples

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    user_type = data['user_type']  # 'rider' or 'driver'
    start_location = data['start_location']
    end_location = data['end_location']
    start_time = data['start_time']
    c = data['c']
    k = data['k']

    # Create route
    triples = create_n_routes_with_time(start_location, end_location, start_time, c, k)

    # Convert tuples to lists, as MongoDB requires lists instead of tuples
    triples_as_lists = [list(triple) for triple in triples]

    # Create the MongoDB document
    route_document = {
        "user_type": user_type,
        "triples": triples_as_lists,
        "created_at": datetime.utcnow()
    }
    
    # Insert the document into MongoDB
    route_triples_collection.insert_one(route_document)

    return jsonify({'status': 'success', 'triples': triples_as_lists}), 201

@app.route('/routes', methods=['GET'])
def get_routes():
    # Fetch all route triples from MongoDB, sorted by creation date
    routes = list(route_triples_collection.find().sort("created_at", 1))
    
    # Convert the result to JSON serializable format
    for route in routes:
        route['_id'] = str(route['_id'])  # Convert ObjectId to string for JSON compatibility

    return jsonify(routes), 200

if __name__ == '__main__':
    app.run(debug=True)
