import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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
st.sidebar.subheader("Indica punto di partenza e punto di arrivo")

# dizionario nomi
g["nomi_belli"]=g["room"].apply(lambda x:x.split("_room")[0])
g["nomi_belli"]=g["nomi_belli"].apply(lambda x:x[0:6]+""+x[6].upper()+" piano "+x[7] if "scala" in x else x)
g["nomi_belli"]=g["nomi_belli"].apply(lambda x:"stanza " + str(x) if x[0].isdigit() else x) 
diz_nomi_stanze=dict(g[["nomi_belli","room"]].values)

# Dropdown menus to select start and end rooms


start_room = st.sidebar.selectbox("Punto di partenza", list(g.nomi_belli.unique()))
end_room = st.sidebar.selectbox("Punto di arrivo", list(g.nomi_belli.unique()))


#start_room = st.sidebar.selectbox("Start Room", list(G.nodes))
#end_room = st.sidebar.selectbox("End Room", list(G.nodes))

# Button to find the route
if st.sidebar.button("Trova il percorso"):
    
    try:
        
        ### utilizza nomi databse per la funzione
        start_room=diz_nomi_stanze[start_room]
        end_room=diz_nomi_stanze[end_room]

        ## filtra db con piano massimo
        max_piano=g.loc[g["room"].isin([start_room,end_room]),"piano"].max()
        gplot=g.loc[g["piano"]<=max_piano]
        
        ### vai
        shortest_path = nx.shortest_path(G, source=start_room, target=end_room, weight='weight')
        shortest_distance = nx.shortest_path_length(G, source=start_room, target=end_room, weight='weight')

        #st.write(f"Per andare dalla stanza {start_room} alla stanza {end_room}: {shortest_path}")

        # Visualization
        nodes_with_z = {}
        leva_un_piano = g[["room", "x", "y", "piano"]].drop_duplicates().copy()
        leva_un_piano["piano"] = leva_un_piano["piano"] - 1
        for i, s in leva_un_piano.iterrows():
            nodes_with_z[s["room"]] = s[["x", "y", "piano"]].to_list()

        colors_dict = dict({0: "black", 1: "black", 2: "black", 3: "black"})

        # Visualization
        path = shortest_path
        if path:
            multip=20
            fig = plt.figure(figsize=(15,25))
            axs = fig.add_subplot(111, projection='3d')
            axs.text(15, 15, 0.0, "Via XX Settembre",zdir="x", color="blue",horizontalalignment="center",fontsize=12)
            axs.text(15, -4, 0.0, "Via Cernaia",zdir="x", color="blue",horizontalalignment="center",fontsize=12)
            axs.text(0.8, 4, 0.0, "Via Pastrengo",zdir="y", color="blue",horizontalalignment="center",fontsize=12)
            axs.text(35, 4, 0.0, "Via Goito",zdir="y", color="blue",horizontalalignment="center",fontsize=12)
            # Plot path
            for i in range(0, len(path) - 1):
                room1, room2 = path[i], path[i + 1]
                x1, y1, z1 = nodes_with_z[room1]
                x2, y2, z2 = nodes_with_z[room2]
                axs.plot([x1, x2], [y1, y2], [z1*multip, z2*multip], 'k-', linewidth=3)

            # Plot corridors
            for i, rr in gplot.iterrows():
                room1, room2 = rr["room"], rr["link"]
                if (("scala" in room1) & ("scala" in room2)) == False:
                    x1, y1, z1 = nodes_with_z[room1]
                    x2, y2, z2 = nodes_with_z[room2]
                    axs.plot([x1, x2], [y1, y2], [z1*multip, z2*multip], 'k-', color=colors_dict[rr["piano"] - 1], alpha=0.2)
                else:
                    if room1[7] == room2[7]:
                        x1, y1, z1 = nodes_with_z[room1]
                        x2, y2, z2 = nodes_with_z[room2]
                        axs.plot([x1, x2], [y1, y2], [z1*multip, z2*multip], 'k-', color=colors_dict[rr["piano"] - 1], alpha=0.2)
                ### this is to plot in any case:
                x1, y1, z1 = nodes_with_z[room1]
                x2, y2, z2 = nodes_with_z[room2]
                axs.plot([x1, x2], [y1, y2], [z1*multip, z2*multip], 'k-', color=colors_dict[rr["piano"] - 1], alpha=0.2)
            ### plot points
            for room, (x, y, z) in nodes_with_z.items():
                if room in path:
                    axs.scatter(x, y, z*multip, color=colors_dict[z], s=30)
                    
                if ("scala" in room) & ("1" in room):
                    axs.text(x * 1.05, y, z*multip, s=room[0:7], color="red",fontsize=12)
                
                if room in [start_room, end_room]:
                    #if "scala" not in room:
                    #    axs.text(x * 1.05, y, z*multip, s=room.split("_room")[0], fontsize=12)
                    #axs.text(x * 1.05, y, z*multip, s="Partenza" if room==start_room else "Arrivo",background_color="white", fontsize=12)

                    axs.text(x*1.05,y,z*multip,s="Partenza" if room==start_room else "Arrivo",
                     bbox={"boxstyle":"roundtooth, pad=0.7","fc":"w","alpha":1},fontsize=15) 
                    
                    axs.scatter(x, y, z*multip, color="red" if room==start_room else "blue", s=70)
                
            axs.set_xticks([])
            axs.set_yticks([])
            axs.set_zticks([])
            axs.set_ylim(0, 15)
            axs.set_xlim(0, 30)
            axs.set_zlim(0, 50)

            for floor in range(0, gplot["piano"].max()):
                x = [0, 0, 30, 30]
                y = [0, 15, 15, 0]
                z = [floor*multip] * 4
                verts = [list(zip(x, y, z))]
                axs.text(x=28, y=10, s=f"Piano {floor}", z=floor*multip, fontsize=12, color=colors_dict[floor])
                #axs.add_collection3d(Poly3DCollection(verts,color=colors_dict[floor],alpha=0.1))

                ### shadow corridor
                rooms=gplot.loc[gplot["room"].apply(lambda x:(x[0].isdigit())&(x[0]=="1")),["room","corridoio","x","y"]].drop_duplicates()
                max_x=rooms.groupby("corridoio")["x"].max()
                max_y=rooms.groupby("corridoio")["y"].max()
                min_x=rooms.groupby("corridoio")["x"].min()
                min_y=rooms.groupby("corridoio")["y"].min()
                for corridoio in max_x.index:
                    x = [min_x[corridoio]-1,min_x[corridoio]-1,max_x[corridoio]+1,max_x[corridoio]+1]
                    y = [min_y[corridoio]-1,max_y[corridoio]+1,max_y[corridoio]+1,min_y[corridoio]-1]
                    z = [floor*multip]*4
                    verts = [list(zip(x,y,z))]
                    axs.add_collection3d(Poly3DCollection(verts,color=colors_dict[floor],alpha=0.1,linewidth=0.01))



            st.pyplot(fig)
    except nx.NetworkXNoPath:
        st.write(f"No path found from {start_room} to {end_room}")
