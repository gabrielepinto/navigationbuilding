import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# Load your data
g = pd.read_csv("esempio_stanze_v3.csv")
g["room"] = g["room"].apply(lambda x: str(x) + "_room")
g["link"] = g["link"].apply(lambda x: str(x) + "_room")
g["xy"] = g[["x", "y"]].apply(lambda x: list(x), axis=1)

# Create a graph using NetworkX
G = nx.Graph()

# Add nodes to the graph
nodes = dict(g[["room", "xy"]].values)
G.add_nodes_from(nodes.keys())

# Create edges dictionary with bidirectional connections
edges_dict = {}
for _, row in g.iterrows():
    room = row["room"]
    links = row["link"]
    if not pd.isnull(links):
        links = links.split(",")
        for link in links:
            if link not in edges_dict:
                edges_dict[link] = []
            edges_dict[link].append(room)

# Add edges to the graph
for room, links in edges_dict.items():
    G.add_edges_from([(room, link) for link in links])

for u, v in G.edges:
    if 'scala' in u and 'scala' in v:
        floor_u = u[7]
        floor_v = v[7]
        if floor_u != floor_v:
            G[u][v]['weight'] = 20.0  # Adjust the weight as needed

# Create a Streamlit app
st.title("Trova percorso al palazzo delle finanze")

# Sidebar with user input
st.sidebar.subheader("Choose Start and End Rooms")

# Dropdown menus to select start and end rooms
start_room = st.sidebar.selectbox("Start Room", list(G.nodes))
end_room = st.sidebar.selectbox("End Room", list(G.nodes))

# Button to find the route
if st.sidebar.button("Find Route"):
    try:
        shortest_path = nx.shortest_path(G, source=start_room, target=end_room, weight='weight')
        shortest_distance = nx.shortest_path_length(G, source=start_room, target=end_room, weight='weight')

        st.write(f"Shortest path from {start_room} to {end_room}: {shortest_path}")
        st.write(f"Shortest distance: {shortest_distance}")

        # Visualization
        nodes_with_z = {}
        leva_un_piano = g[["room", "x", "y", "piano"]].drop_duplicates().copy()
        leva_un_piano["piano"] = leva_un_piano["piano"] - 1
        for i, s in leva_un_piano.iterrows():
            nodes_with_z[s["room"]] = s[["x", "y", "piano"]].to_list()

        colors_dict = dict({0: "black", 1: "red", 2: "blue", 3: "green"})

        # Visualization
        path = shortest_path
        if path:
            fig = plt.figure()
            axs = fig.add_subplot(111, projection='3d')

            # Plot path
            for i in range(0, len(path) - 1):
                room1, room2 = path[i], path[i + 1]
                x1, y1, z1 = nodes_with_z[room1]
                x2, y2, z2 = nodes_with_z[room2]
                axs.plot([x1, x2], [y1, y2], [z1, z2], 'k-', linewidth=3)

            # Plot corridors
            for i, rr in g.iterrows():
                room1, room2 = rr["room"], rr["link"]
                if (("scala" in room1) & ("scala" in room2)) == False:
                    x1, y1, z1 = nodes_with_z[room1]
                    x2, y2, z2 = nodes_with_z[room2]
                    axs.plot([x1, x2], [y1, y2], [z1, z2], 'k-', color=colors_dict[rr["piano"] - 1], alpha=0.2)
                else:
                    if room1[7] == room2[7]:
                        x1, y1, z1 = nodes_with_z[room1]
                        x2, y2, z2 = nodes_with_z[room2]
                        axs.plot([x1, x2], [y1, y2], [z1, z2], 'k-', color=colors_dict[rr["piano"] - 1], alpha=0.2)

            for room, (x, y, z) in nodes_with_z.items():
                if room in path:
                    axs.scatter(x, y, z, color=colors_dict[z], s=50)

                if ("scala" in room) & ("1" in room):
                    axs.text(x * 1.05, y, z, s=room[0:7], fontsize=8)
                
                if room in [start_room, end_room]:
                    if "scala" not in room:
                        axs.text(x * 1.05, y, z, s=room.split("_room")[0], fontsize=8)
                    axs.scatter(x, y, z, color="red" if room==start_room else "blue", s=70)
                
            axs.set_xticks([])
            axs.set_yticks([])
            axs.set_zticks([])
            axs.set_ylim(0, 15)
            axs.set_xlim(0, 30)
            axs.set_zlim(0, 3)

            for floor in range(0, 4):
                x = [0, 0, 30, 30]
                y = [0, 15, 15, 0]
                z = [floor] * 4
                verts = [list(zip(x, y, z))]
                axs.text(x=28, y=10, s=f"Piano {floor}", z=floor, fontsize=8, color=colors_dict[floor])

            st.pyplot(fig)
    except nx.NetworkXNoPath:
        st.write(f"No path found from {start_room} to {end_room}")
