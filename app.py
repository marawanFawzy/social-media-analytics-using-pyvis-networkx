from flask import Flask, render_template, request
from tkinter import *
import networkx as nx
from networkx.algorithms import community, cuts
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
import csv
from pyvis import network as net
from IPython.core.display import HTML
from IPython.display import display
import itertools
import json
from sklearn.metrics.cluster import normalized_mutual_info_score


app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('home.html')


@app.route('/karate')
def get():
    nodes_path = request.args.get('npath')
    edges_path = request.args.get('epath')
    if nodes_path and edges_path:
        # Read nodes from the CSV file
        with open(nodes_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            nodes = [(int(row[0]), {'Class': row[1], 'Gender': row[2]})
                     for row in reader]

        # Read edges from the CSV file
        with open(edges_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            edges = [(int(row[0]), int(row[1])) for row in reader]

        # to get nodes and edges fom csv
        G = nx.Graph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        print("data read")
    else:
        G = nx.karate_club_graph()
    
    #directed graph example
    #G = nx.gn_graph(10, kernel=lambda x: x ** 1.5)
    G = G.to_undirected()
    # create html page with size 500 * 70% with name Zachary’s Karate Club graph and menu and filter
    graph = net.Network(height='500px', width='70%',
                        select_menu=True,
                        filter_menu=True, neighborhood_highlight=True)

    # dataset karate_club_graph
    print("code start")

    # Run the Girvan Newman algorithm

    k = len(G.nodes)
    print(G.nodes)
    mods = dict()
    comms = dict()
    comms_it = 2

    for communities in itertools.islice(community.girvan_newman(G), k):
        comm = tuple(sorted(c) for c in communities)
        mods[comms_it] = community.modularity(G, comm)
        comms[comms_it] = comm
        comms_it += 1

    print(mods)
    print(comms)

    best_partion = max(mods, key=mods.get)
    number = best_partion
    mod = mods[best_partion]
    comm = comms[best_partion]

    i = 0
    communities = dict()
    for c in comm:
        for j in c:
            communities[j] = i+1
        i = i + 1

    
    betweenness_centrality = nx.betweenness_centrality(G, None, False, None)
    closeness_centrality = nx.closeness_centrality(G)
    eigenvector_centrality = nx.eigenvector_centrality(G)
    pagerank = nx.pagerank(G)
    page_rank_value = max(pagerank, key=pagerank.get)

    d = dict(G.degree)
    max_color = max(d, key=d.get)
    max_color = d[max_color]

    nx.set_node_attributes(G, d, 'degree')
    d.update((x, 5*y) for x, y in d.items())
    nx.set_node_attributes(G, d, 'size')
    nx.set_node_attributes(G, betweenness_centrality, 'betweenness_centrality')
    nx.set_node_attributes(G, closeness_centrality, 'closeness_centrality')
    nx.set_node_attributes(G, eigenvector_centrality, 'eigenvector_centrality')
    nx.set_node_attributes(G, communities, 'community')
    nx.set_node_attributes(G, pagerank, 'pagerank')

    # Conductance
    # Find the community with the lowest conductance
    min_cond = float('inf')
    min_comm = None

    for c in comm:
        # Calculate the conductance of the community
        cond = cuts.conductance(G, c)
        # Check if this community has lower conductance
        if cond < min_cond:
            min_cond = cond
            min_comm = c

    ground_truth = {}
    for node in G.nodes(data=True):
        ground_truth[node[0]] = node[1]["club"] # change this when data is changed

    # Calculate the NMI score between the two clusterings
    nmi_score = normalized_mutual_info_score(
        list(ground_truth.values()), list(communities.values()))
    
    nodesHTML = []

    print("graph")
    i = 0
    for node in G.nodes(data=True):
        nodesHTML.append(node)

        bias = node[1]["degree"]/max_color * 255
        red = hex(int(bias))[2:]
        blue = hex(int(256-bias))[2:]

        if len(red) == 1:
            red = '0'+red
        if len(blue) == 1:
            blue = '0'+blue
        node_color = '#'+red+'00'+blue

        graph.add_node(node[0], label=str(node[0]), size=node[1]["size"],
                       betweenness_centrality=node[1]["betweenness_centrality"],
                       eigenvector_centrality=node[1]["eigenvector_centrality"],
                       closeness_centrality=node[1]["closeness_centrality"],
                       community=node[1]["community"], pagerank=node[1]["pagerank"], color=node_color)
        i = i+1

    graph.from_nx(G)
    graph.show_buttons(filter_=['physics'])
    graph.write_html('karate.html', False, False)

    return render_template('evaluations.html', number=number, min_cond=min_cond, min_comm=min_comm, mod=mod, nmi_score=nmi_score, nodes=nodesHTML, page_rank=page_rank_value)
